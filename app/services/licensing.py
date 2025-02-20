from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import jwt
import uuid
import ipaddress
from cryptography.fernet import Fernet
import blockchain
from web3 import Web3
import requests
import platform
import psutil
import netifaces
import sqlite3

from app.core.config import settings

class LicensingService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.licenses = self.db.licenses
        self.activations = self.db.activations
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize encryption
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
        
        # Initialize blockchain
        self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        
        # Initialize offline database
        self.offline_db = sqlite3.connect('offline_licenses.db')

    async def generate_license(
        self,
        license_type: str,
        user_data: Dict
    ) -> Dict:
        """
        Generate unique license key.
        """
        try:
            # Generate unique key
            key = await self.generate_unique_key()
            
            # Create license data
            license_data = await self.create_license_data(key, license_type, user_data)
            
            # Store license
            await self.store_license(license_data)
            
            # Store on blockchain if enabled
            if settings.USE_BLOCKCHAIN:
                await self.store_on_blockchain(license_data)
            
            return {
                "license_key": key,
                "type": license_type,
                "details": license_data,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License generation failed: {str(e)}"
            )

    async def activate_license(
        self,
        license_key: str,
        activation_data: Dict
    ) -> Dict:
        """
        Activate license key.
        """
        try:
            # Validate license
            license_data = await self.validate_license(license_key)
            
            # Check activation limits
            await self.check_activation_limits(license_data)
            
            # Create activation
            activation = await self.create_activation(license_data, activation_data)
            
            return {
                "activation_id": activation["activation_id"],
                "status": "active",
                "details": activation,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License activation failed: {str(e)}"
            )

    async def validate_license_usage(
        self,
        license_key: str,
        usage_data: Dict
    ) -> Dict:
        """
        Validate license usage.
        """
        try:
            # Get license data
            license_data = await self.get_license_data(license_key)
            
            # Check restrictions
            restrictions = await self.check_license_restrictions(
                license_data,
                usage_data
            )
            
            # Update usage metrics
            await self.update_usage_metrics(license_data, usage_data)
            
            return {
                "valid": restrictions["valid"],
                "restrictions": restrictions,
                "usage": await self.get_usage_metrics(license_data),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"License validation failed: {str(e)}"
            )

    async def manage_feature_access(
        self,
        license_key: str,
        feature: str,
        action: str
    ) -> Dict:
        """
        Manage feature-based access.
        """
        try:
            # Get license data
            license_data = await self.get_license_data(license_key)
            
            # Update feature access
            updated = await self.update_feature_access(license_data, feature, action)
            
            # Sync changes
            await self.sync_feature_changes(updated)
            
            return {
                "license_key": license_key,
                "feature": feature,
                "status": updated["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Feature access update failed: {str(e)}"
            )

    async def manage_offline_licensing(
        self,
        action: str,
        license_data: Dict
    ) -> Dict:
        """
        Manage offline license activation.
        """
        try:
            if action == "generate":
                result = await self.generate_offline_license(license_data)
            elif action == "activate":
                result = await self.activate_offline_license(license_data)
            elif action == "sync":
                result = await self.sync_offline_license(license_data)
            else:
                raise ValueError("Invalid action")
            
            return {
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Offline licensing failed: {str(e)}"
            )

    async def manage_device_licensing(
        self,
        license_key: str,
        device_data: Dict
    ) -> Dict:
        """
        Manage device-based licensing.
        """
        try:
            # Validate device
            device = await self.validate_device(device_data)
            
            # Check device limits
            await self.check_device_limits(license_key)
            
            # Register device
            registration = await self.register_device(license_key, device)
            
            return {
                "license_key": license_key,
                "device_id": registration["device_id"],
                "status": registration["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Device licensing failed: {str(e)}"
            )

    async def manage_project_licensing(
        self,
        license_key: str,
        project_data: Dict
    ) -> Dict:
        """
        Manage project-based licensing.
        """
        try:
            # Validate project
            project = await self.validate_project(project_data)
            
            # Check project limits
            await self.check_project_limits(license_key)
            
            # Register project
            registration = await self.register_project(license_key, project)
            
            return {
                "license_key": license_key,
                "project_id": registration["project_id"],
                "status": registration["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Project licensing failed: {str(e)}"
            )

    async def manage_time_restrictions(
        self,
        license_key: str,
        time_data: Dict
    ) -> Dict:
        """
        Manage time-based license restrictions.
        """
        try:
            # Validate time restrictions
            restrictions = await self.validate_time_restrictions(time_data)
            
            # Update license
            updated = await self.update_time_restrictions(
                license_key,
                restrictions
            )
            
            return {
                "license_key": license_key,
                "restrictions": restrictions,
                "status": updated["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Time restriction update failed: {str(e)}"
            )

    async def generate_unique_key(self) -> str:
        """
        Generate unique license key.
        """
        try:
            key = str(uuid.uuid4()).replace("-", "").upper()
            key = f"{key[:4]}-{key[4:8]}-{key[8:12]}-{key[12:16]}"
            return key
        except Exception:
            return str(uuid.uuid4())

    async def create_license_data(
        self,
        key: str,
        license_type: str,
        user_data: Dict
    ) -> Dict:
        """
        Create license data structure.
        """
        try:
            return {
                "license_key": key,
                "type": license_type,
                "user_data": user_data,
                "status": "active",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=365),
                "features": {},
                "restrictions": {},
                "activations": [],
                "usage": {}
            }
        except Exception:
            return {}

    async def store_license(self, license_data: Dict) -> None:
        """
        Store license in database.
        """
        try:
            await self.licenses.insert_one(license_data)
        except Exception:
            pass

    async def store_on_blockchain(self, license_data: Dict) -> None:
        """
        Store license on blockchain.
        """
        try:
            # Implementation would store on blockchain
            pass
        except Exception:
            pass

    async def validate_license(self, license_key: str) -> Dict:
        """
        Validate license key.
        """
        try:
            license_data = await self.licenses.find_one({"license_key": license_key})
            if not license_data:
                raise ValueError("Invalid license key")
            return license_data
        except Exception:
            raise ValueError("License validation failed")

    async def check_activation_limits(self, license_data: Dict) -> None:
        """
        Check license activation limits.
        """
        try:
            if len(license_data.get("activations", [])) >= license_data.get("max_activations", 1):
                raise ValueError("Maximum activations reached")
        except Exception:
            raise ValueError("Activation check failed")

    async def create_activation(
        self,
        license_data: Dict,
        activation_data: Dict
    ) -> Dict:
        """
        Create license activation.
        """
        try:
            activation = {
                "activation_id": str(uuid.uuid4()),
                "license_key": license_data["license_key"],
                "device_info": activation_data.get("device_info", {}),
                "ip_address": activation_data.get("ip_address"),
                "created_at": datetime.utcnow()
            }
            
            await self.activations.insert_one(activation)
            return activation
        except Exception:
            return {}
