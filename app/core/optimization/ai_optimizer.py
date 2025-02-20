from typing import Dict, Any, List
import numpy as np
from datetime import datetime
from app.core.logger import logger
from app.models.optimization import PerformanceMetrics, OptimizationResult
from app.core.analytics import APIAnalytics

class AIPerformanceOptimizer:
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.optimization_history: Dict[str, List[OptimizationResult]] = {}
        
    async def optimize_endpoint(self, endpoint_path: str) -> OptimizationResult:
        try:
            # Collect performance metrics
            metrics = await self._collect_metrics(endpoint_path)
            
            # Analyze bottlenecks
            bottlenecks = await self._analyze_bottlenecks(metrics)
            
            # Generate optimization suggestions
            optimizations = await self._generate_optimizations(bottlenecks)
            
            # Apply optimizations
            result = await self._apply_optimizations(endpoint_path, optimizations)
            
            # Store optimization history
            if endpoint_path not in self.optimization_history:
                self.optimization_history[endpoint_path] = []
            self.optimization_history[endpoint_path].append(result)
            
            return result
        except Exception as e:
            logger.error(f"Optimization failed for endpoint {endpoint_path}: {str(e)}")
            raise

    async def _collect_metrics(self, endpoint_path: str) -> PerformanceMetrics:
        try:
            # Collect current performance metrics
            stats = await self.analytics.get_endpoint_stats(endpoint_path)
            return PerformanceMetrics(
                endpoint_path=endpoint_path,
                avg_response_time=stats.avg_response_time,
                memory_usage=stats.memory_usage,
                cpu_usage=stats.cpu_usage,
                database_queries=stats.db_queries,
                cache_hit_ratio=stats.cache_hits / (stats.cache_hits + stats.cache_misses) if (stats.cache_hits + stats.cache_misses) > 0 else 0,
                error_rate=stats.error_rate,
                collected_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            raise

    async def _analyze_bottlenecks(self, metrics: PerformanceMetrics) -> List[Dict[str, Any]]:
        bottlenecks = []
        
        # Check response time
        if metrics.avg_response_time > 500:  # 500ms threshold
            bottlenecks.append({
                "type": "response_time",
                "severity": "high",
                "details": f"Average response time {metrics.avg_response_time}ms is too high"
            })
            
        # Check memory usage
        if metrics.memory_usage > 80:  # 80% threshold
            bottlenecks.append({
                "type": "memory_usage",
                "severity": "medium",
                "details": f"Memory usage at {metrics.memory_usage}%"
            })
            
        return bottlenecks 

    async def _generate_optimizations(self, bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        optimizations = []
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "response_time":
                optimizations.append({
                    "type": "caching",
                    "action": "implement_response_caching",
                    "config": {"ttl": 300}  # 5 minutes cache
                })
            elif bottleneck["type"] == "memory_usage":
                optimizations.append({
                    "type": "memory",
                    "action": "optimize_memory_usage",
                    "config": {"gc_threshold": 75}  # Trigger GC at 75% usage
                })
        return optimizations

    async def _apply_optimizations(self, endpoint_path: str, optimizations: List[Dict[str, Any]]) -> OptimizationResult:
        try:
            # Record metrics before optimization
            metrics_before = await self._collect_metrics(endpoint_path)
            
            # Apply each optimization
            for opt in optimizations:
                await self._apply_single_optimization(endpoint_path, opt)
            
            # Record metrics after optimization
            metrics_after = await self._collect_metrics(endpoint_path)
            
            # Calculate improvement
            improvement = self._calculate_improvement(metrics_before, metrics_after)
            
            return OptimizationResult(
                endpoint_path=endpoint_path,
                optimizations_applied=optimizations,
                performance_improvement=improvement,
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to apply optimizations: {str(e)}")
            raise 