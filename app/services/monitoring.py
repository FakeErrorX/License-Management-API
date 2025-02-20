from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import psutil
import os

from app.core.config import settings

# Initialize Prometheus metrics
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
API_LATENCY = Histogram('api_latency_seconds', 'API latency in seconds', ['endpoint'])
ACTIVE_USERS = Gauge('active_users', 'Number of active users')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Memory usage percentage')
API_ERRORS = Counter('api_errors_total', 'Total API errors', ['endpoint', 'error_type'])

class MonitoringService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.metrics = self.db.metrics
        self.alerts = self.db.alerts
        self.logs = self.db.logs

    async def record_api_request(self, endpoint: str, method: str, latency: float):
        """
        Record API request metrics.
        """
        API_REQUESTS.labels(endpoint=endpoint, method=method).inc()
        API_LATENCY.labels(endpoint=endpoint).observe(latency)
        
        await self.metrics.insert_one({
            "type": "api_request",
            "endpoint": endpoint,
            "method": method,
            "latency": latency,
            "timestamp": datetime.utcnow()
        })

    async def record_error(self, endpoint: str, error_type: str, error_details: Dict):
        """
        Record API error.
        """
        API_ERRORS.labels(endpoint=endpoint, error_type=error_type).inc()
        
        await self.metrics.insert_one({
            "type": "error",
            "endpoint": endpoint,
            "error_type": error_type,
            "details": error_details,
            "timestamp": datetime.utcnow()
        })

    async def update_system_metrics(self):
        """
        Update system metrics.
        """
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        CPU_USAGE.set(cpu_percent)
        MEMORY_USAGE.set(memory_percent)
        
        await self.metrics.insert_one({
            "type": "system",
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "timestamp": datetime.utcnow()
        })

    async def get_prometheus_metrics(self) -> str:
        """
        Get Prometheus metrics.
        """
        return prometheus_client.generate_latest().decode()

    async def create_alert_rule(self, rule: Dict) -> Dict:
        """
        Create a new monitoring alert rule.
        """
        rule["created_at"] = datetime.utcnow()
        result = await self.alerts.insert_one(rule)
        rule["id"] = str(result.inserted_id)
        return rule

    async def get_alert_rules(self) -> List[Dict]:
        """
        Get all alert rules.
        """
        rules = await self.alerts.find().to_list(None)
        return [{**rule, "id": str(rule["_id"])} for rule in rules]

    async def delete_alert_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule.
        """
        result = await self.alerts.delete_one({"_id": rule_id})
        return result.deleted_count > 0

    async def get_api_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: Optional[str] = None
    ) -> Dict:
        """
        Get API metrics for a time range.
        """
        match = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        if endpoint:
            match["endpoint"] = endpoint

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$endpoint",
                    "total_requests": {"$sum": 1},
                    "avg_latency": {"$avg": "$latency"},
                    "error_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$type", "error"]}, 1, 0]
                        }
                    }
                }
            }
        ]

        metrics = await self.metrics.aggregate(pipeline).to_list(None)
        return {
            "metrics": metrics,
            "period": {
                "start": start_time,
                "end": end_time
            }
        }

    async def get_system_health(self) -> Dict:
        """
        Get system health metrics.
        """
        # Get latest system metrics
        latest_metrics = await self.metrics.find(
            {"type": "system"}
        ).sort("timestamp", -1).limit(1).to_list(None)

        # Get error rates
        error_rates = await self.metrics.aggregate([
            {
                "$match": {
                    "type": "error",
                    "timestamp": {
                        "$gte": datetime.utcnow().replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                    }
                }
            },
            {
                "$group": {
                    "_id": "$error_type",
                    "count": {"$sum": 1}
                }
            }
        ]).to_list(None)

        return {
            "system": latest_metrics[0] if latest_metrics else None,
            "error_rates": {err["_id"]: err["count"] for err in error_rates},
            "timestamp": datetime.utcnow()
        }

    async def get_api_latency_stats(self, endpoint: str) -> Dict:
        """
        Get detailed API latency statistics.
        """
        pipeline = [
            {
                "$match": {
                    "type": "api_request",
                    "endpoint": endpoint,
                    "timestamp": {
                        "$gte": datetime.utcnow().replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_latency": {"$avg": "$latency"},
                    "max_latency": {"$max": "$latency"},
                    "min_latency": {"$min": "$latency"},
                    "p95_latency": {"$percentile": ["$latency", 0.95]},
                    "total_requests": {"$sum": 1}
                }
            }
        ]

        stats = await self.metrics.aggregate(pipeline).to_list(None)
        return stats[0] if stats else {}

    async def get_geo_metrics(self) -> Dict:
        """
        Get geographical API usage metrics.
        """
        pipeline = [
            {
                "$match": {
                    "type": "api_request",
                    "geo_data": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$geo_data.country",
                    "request_count": {"$sum": 1},
                    "avg_latency": {"$avg": "$latency"}
                }
            }
        ]

        geo_metrics = await self.metrics.aggregate(pipeline).to_list(None)
        return {
            "geo_metrics": geo_metrics,
            "timestamp": datetime.utcnow()
        }

    async def get_user_behavior_metrics(self, user_id: str) -> Dict:
        """
        Get user behavior metrics.
        """
        pipeline = [
            {
                "$match": {
                    "type": "api_request",
                    "user_id": user_id
                }
            },
            {
                "$group": {
                    "_id": "$endpoint",
                    "request_count": {"$sum": 1},
                    "avg_latency": {"$avg": "$latency"},
                    "last_access": {"$max": "$timestamp"}
                }
            }
        ]

        behavior_metrics = await self.metrics.aggregate(pipeline).to_list(None)
        return {
            "user_id": user_id,
            "metrics": behavior_metrics,
            "timestamp": datetime.utcnow()
        }
