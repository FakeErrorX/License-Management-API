from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio
from app.core.logger import logger
from app.core.analytics import APIAnalytics
from app.models.rate_limit import RateLimitConfig

class AIRateLimiter:
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.rate_limits: Dict[str, RateLimitConfig] = {}
        self.request_counts: Dict[str, Dict[datetime, int]] = {}
        
    async def should_allow_request(self, user_id: str, endpoint: str) -> Tuple[bool, str]:
        try:
            # Get user's usage pattern
            usage_stats = await self.analytics.get_usage_stats(user_id)
            
            # Dynamically adjust rate limits based on usage pattern
            limit = self._calculate_dynamic_limit(usage_stats)
            
            # Check current request count
            current_count = self._get_current_count(user_id, endpoint)
            
            if current_count >= limit:
                return False, "Rate limit exceeded"
                
            # Update count
            await self._update_count(user_id, endpoint)
            return True, "Request allowed"
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return True, "Rate limiting failed, allowing request"
            
    def _calculate_dynamic_limit(self, usage_stats: UsageStats) -> int:
        # AI-based rate limit calculation
        base_limit = 1000
        
        # Adjust based on usage history
        if usage_stats.total_calls > 10000:
            base_limit *= 2
        elif usage_stats.avg_response_time > 1.0:
            base_limit = int(base_limit * 0.8)
            
        return base_limit
        
    async def _update_count(self, user_id: str, endpoint: str):
        now = datetime.utcnow()
        if user_id not in self.request_counts:
            self.request_counts[user_id] = {}
        self.request_counts[user_id][now] = self.request_counts[user_id].get(now, 0) + 1
        
    def _get_current_count(self, user_id: str, endpoint: str) -> int:
        if user_id not in self.request_counts:
            return 0
            
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        
        # Clean up old entries
        self.request_counts[user_id] = {
            ts: count for ts, count in self.request_counts[user_id].items()
            if ts > window_start
        }
        
        return sum(self.request_counts[user_id].values()) 