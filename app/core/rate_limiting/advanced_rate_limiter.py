from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.rate_limiting import RateLimit, RateLimitPolicy, QuotaUsage
from app.core.ai.traffic_predictor import TrafficPredictor

class AdvancedRateLimiter:
    def __init__(self, traffic_predictor: TrafficPredictor):
        self.predictor = traffic_predictor
        self.rate_limits: Dict[str, RateLimit] = {}
        self.quota_usage: Dict[str, QuotaUsage] = {}
        self.policies: Dict[str, RateLimitPolicy] = {}
        
    async def check_rate_limit(self, request_data: Dict[str, Any]) -> bool:
        try:
            # Predict traffic patterns
            prediction = await self._predict_traffic_pattern(request_data)
            
            # Adjust rate limits dynamically
            adjusted_limit = await self._adjust_rate_limits(prediction)
            
            # Check quota usage
            quota_check = await self._check_quota_usage(request_data)
            
            # Apply burst handling
            burst_allowed = await self._handle_burst_traffic(request_data)
            
            # Update usage metrics
            await self._update_usage_metrics(request_data)
            
            return all([adjusted_limit, quota_check, burst_allowed])
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            raise 