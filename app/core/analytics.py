from datetime import datetime
from typing import Dict, Any, List
from app.core.logger import logger
from app.models.analytics import APIMetrics, UsageStats
from motor.motor_asyncio import AsyncIOMotorClient

class APIAnalytics:
    def __init__(self, mongodb_client: AsyncIOMotorClient):
        self.db = mongodb_client.analytics
        
    async def track_api_call(self, endpoint: str, user_id: str, metrics: APIMetrics):
        try:
            await self.db.api_calls.insert_one({
                "endpoint": endpoint,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "response_time": metrics.response_time,
                "status_code": metrics.status_code,
                "ip_address": metrics.ip_address,
                "geo_location": metrics.geo_location,
                "request_size": metrics.request_size,
                "response_size": metrics.response_size
            })
        except Exception as e:
            logger.error(f"Failed to track API call: {str(e)}")

    async def get_usage_stats(self, user_id: str) -> UsageStats:
        try:
            stats = await self.db.api_calls.aggregate([
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$user_id",
                    "total_calls": {"$sum": 1},
                    "avg_response_time": {"$avg": "$response_time"},
                    "total_data_transfer": {"$sum": {"$add": ["$request_size", "$response_size"]}}
                }}
            ]).to_list(1)
            return UsageStats(**stats[0]) if stats else UsageStats()
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return UsageStats() 