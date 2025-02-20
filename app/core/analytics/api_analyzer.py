from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.analytics import APIUsageMetrics, UserBehavior, PerformanceInsight
from app.core.ai.behavior_analyzer import BehaviorAnalyzer

class APIAnalyzer:
    def __init__(self, behavior_analyzer: BehaviorAnalyzer):
        self.analyzer = behavior_analyzer
        self.usage_metrics: Dict[str, APIUsageMetrics] = {}
        self.user_behaviors: Dict[str, List[UserBehavior]] = {}
        self.insights_cache: Dict[str, List[PerformanceInsight]] = {}
        
    async def analyze_api_usage(self, timeframe: str = "24h") -> Dict[str, Any]:
        try:
            # Collect usage data
            usage_data = await self._collect_usage_data(timeframe)
            
            # Analyze user behavior patterns
            behavior_patterns = await self._analyze_behavior_patterns(usage_data)
            
            # Generate performance insights
            insights = await self._generate_insights(usage_data, behavior_patterns)
            
            # Predict future trends
            trends = await self._predict_usage_trends(usage_data)
            
            # Generate optimization recommendations
            recommendations = await self._generate_recommendations(insights, trends)
            
            return {
                "usage_metrics": usage_data,
                "behavior_patterns": behavior_patterns,
                "insights": insights,
                "trends": trends,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"API analysis failed: {str(e)}")
            raise 