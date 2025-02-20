from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import json
import redis
from bson import ObjectId

from app.core.config import settings
from app.models.database import SystemSetting, FeatureFlag

class SystemService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.settings = self.db.system_settings
        self.feature_flags = self.db.feature_flags
        self.redis = redis.Redis.from_url(settings.REDIS_URL)

    async def get_system_setting(self, key: str) -> Dict:
        """
        Get a system setting.
        """
        # Try cache first
        cached = await self.redis.get(f"setting:{key}")
        if cached:
            return json.loads(cached)
        
        # Get from database
        setting = await self.settings.find_one({"key": key})
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting {key} not found"
            )
        
        # Cache the setting
        await self.redis.setex(
            f"setting:{key}",
            300,  # 5 minutes cache
            json.dumps(setting["value"])
        )
        
        return setting["value"]

    async def update_system_setting(self, key: str, value: Dict) -> Dict:
        """
        Update a system setting.
        """
        try:
            result = await self.settings.update_one(
                {"key": key},
                {
                    "$set": {
                        "value": value,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Clear cache
            await self.redis.delete(f"setting:{key}")
            
            return {"key": key, "value": value}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update setting: {str(e)}"
            )

    async def create_feature_flag(
        self,
        name: str,
        description: str,
        rules: Dict
    ) -> Dict:
        """
        Create a new feature flag.
        """
        try:
            flag = {
                "name": name,
                "description": description,
                "is_enabled": False,
                "rules": rules,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.feature_flags.insert_one(flag)
            flag["id"] = str(result.inserted_id)
            
            # Cache the flag
            await self.cache_feature_flag(flag)
            
            return flag
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create feature flag: {str(e)}"
            )

    async def update_feature_flag(
        self,
        flag_id: str,
        updates: Dict
    ) -> Dict:
        """
        Update a feature flag.
        """
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.feature_flags.update_one(
                {"_id": ObjectId(flag_id)},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feature flag not found"
                )
            
            # Clear cache
            await self.redis.delete(f"flag:{flag_id}")
            
            flag = await self.feature_flags.find_one({"_id": ObjectId(flag_id)})
            return {**flag, "id": str(flag["_id"])}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update feature flag: {str(e)}"
            )

    async def delete_feature_flag(self, flag_id: str) -> Dict:
        """
        Delete a feature flag.
        """
        try:
            result = await self.feature_flags.delete_one({"_id": ObjectId(flag_id)})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feature flag not found"
                )
            
            # Clear cache
            await self.redis.delete(f"flag:{flag_id}")
            
            return {"status": "success", "message": "Feature flag deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete feature flag: {str(e)}"
            )

    async def evaluate_feature_flag(
        self,
        flag_name: str,
        context: Dict
    ) -> bool:
        """
        Evaluate a feature flag for given context.
        """
        try:
            # Try cache first
            cached = await self.redis.get(f"flag_eval:{flag_name}")
            if cached:
                flag = json.loads(cached)
            else:
                flag = await self.feature_flags.find_one({"name": flag_name})
                if flag:
                    await self.cache_feature_flag(flag)
            
            if not flag:
                return False
            
            if not flag["is_enabled"]:
                return False
            
            return await self.evaluate_rules(flag["rules"], context)
        except Exception as e:
            # Log error and return conservative false
            print(f"Error evaluating feature flag: {str(e)}")
            return False

    async def evaluate_rules(self, rules: Dict, context: Dict) -> bool:
        """
        Evaluate feature flag rules against context.
        """
        try:
            if rules.get("type") == "all":
                return all(
                    await self.evaluate_rule(rule, context)
                    for rule in rules.get("rules", [])
                )
            elif rules.get("type") == "any":
                return any(
                    await self.evaluate_rule(rule, context)
                    for rule in rules.get("rules", [])
                )
            elif rules.get("type") == "percentage":
                return await self.evaluate_percentage_rule(
                    rules.get("percentage", 0),
                    context
                )
            else:
                return False
        except Exception:
            return False

    async def evaluate_rule(self, rule: Dict, context: Dict) -> bool:
        """
        Evaluate a single feature flag rule.
        """
        try:
            if rule["type"] == "user":
                return context.get("user_id") in rule.get("users", [])
            elif rule["type"] == "group":
                return context.get("group") in rule.get("groups", [])
            elif rule["type"] == "environment":
                return context.get("environment") == rule.get("environment")
            elif rule["type"] == "version":
                return self.compare_versions(
                    context.get("version", "0.0.0"),
                    rule.get("version", "0.0.0"),
                    rule.get("operator", ">=")
                )
            else:
                return False
        except Exception:
            return False

    async def evaluate_percentage_rule(
        self,
        percentage: float,
        context: Dict
    ) -> bool:
        """
        Evaluate percentage-based feature flag rule.
        """
        try:
            # Use consistent hashing for stable results
            hash_input = f"{context.get('user_id', '')}:{context.get('feature', '')}"
            hash_value = hash(hash_input) % 100
            return hash_value < percentage
        except Exception:
            return False

    def compare_versions(
        self,
        version1: str,
        version2: str,
        operator: str
    ) -> bool:
        """
        Compare version strings.
        """
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]
            
            if operator == ">=":
                return v1_parts >= v2_parts
            elif operator == ">":
                return v1_parts > v2_parts
            elif operator == "<=":
                return v1_parts <= v2_parts
            elif operator == "<":
                return v1_parts < v2_parts
            elif operator == "==":
                return v1_parts == v2_parts
            else:
                return False
        except Exception:
            return False

    async def cache_feature_flag(self, flag: Dict) -> None:
        """
        Cache a feature flag.
        """
        try:
            await self.redis.setex(
                f"flag:{str(flag['_id'])}",
                300,  # 5 minutes cache
                json.dumps(flag)
            )
            await self.redis.setex(
                f"flag_eval:{flag['name']}",
                300,  # 5 minutes cache
                json.dumps(flag)
            )
        except Exception:
            pass  # Fail silently on cache errors

    async def get_all_feature_flags(self) -> List[Dict]:
        """
        Get all feature flags.
        """
        try:
            flags = await self.feature_flags.find().to_list(None)
            return [{**flag, "id": str(flag["_id"])} for flag in flags]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get feature flags: {str(e)}"
            )

    async def bulk_update_feature_flags(
        self,
        updates: List[Dict]
    ) -> Dict:
        """
        Bulk update feature flags.
        """
        try:
            operations = []
            for update in updates:
                flag_id = update.pop("id", None)
                if flag_id:
                    update["updated_at"] = datetime.utcnow()
                    operations.append(UpdateOne(
                        {"_id": ObjectId(flag_id)},
                        {"$set": update}
                    ))
            
            if operations:
                result = await self.feature_flags.bulk_write(operations)
                
                # Clear cache for all updated flags
                for update in updates:
                    if update.get("id"):
                        await self.redis.delete(f"flag:{update['id']}")
                        if update.get("name"):
                            await self.redis.delete(f"flag_eval:{update['name']}")
                
                return {
                    "modified_count": result.modified_count,
                    "status": "success"
                }
            
            return {"modified_count": 0, "status": "no_operations"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to bulk update feature flags: {str(e)}"
            )
