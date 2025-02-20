from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import tensorflow as tf
import hashlib
import logging
from prometheus_client import Counter, Histogram
from app.core.config import settings

class SmartCachingService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.cache_stats = self.db.cache_stats
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        
        # Initialize ML models
        self.cache_predictor = RandomForestRegressor()
        self.ttl_predictor = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        # Initialize metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total number of cache hits'
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total number of cache misses'
        )
        self.cache_latency = Histogram(
            'cache_latency_seconds',
            'Cache operation latency'
        )

    async def get_cached_response(
        self,
        request_data: Dict,
        endpoint: str
    ) -> Optional[Dict]:
        """
        Get cached API response using smart caching.
        """
        try:
            # Generate cache key
            cache_key = await self._generate_cache_key(request_data, endpoint)
            
            # Check cache
            cached = await self._check_cache(cache_key)
            
            if cached:
                self.cache_hits.inc()
                return cached
            
            self.cache_misses.inc()
            return None
        except Exception as e:
            logging.error(f"Cache retrieval failed: {str(e)}")
            return None

    async def cache_response(
        self,
        request_data: Dict,
        response_data: Dict,
        endpoint: str
    ) -> Dict:
        """
        Cache API response with smart TTL.
        """
        try:
            # Generate cache key
            cache_key = await self._generate_cache_key(request_data, endpoint)
            
            # Predict optimal TTL
            ttl = await self._predict_optimal_ttl(request_data, endpoint)
            
            # Store in cache
            await self._store_in_cache(cache_key, response_data, ttl)
            
            return {
                "cache_key": cache_key,
                "ttl": ttl,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cache storage failed: {str(e)}"
            )

    async def optimize_cache_strategy(
        self,
        endpoint: str
    ) -> Dict:
        """
        Optimize caching strategy for endpoint.
        """
        try:
            # Analyze cache performance
            analysis = await self._analyze_cache_performance(endpoint)
            
            # Generate optimization strategy
            strategy = await self._generate_optimization_strategy(analysis)
            
            # Apply optimizations
            result = await self._apply_cache_optimizations(strategy)
            
            return {
                "endpoint": endpoint,
                "strategy": strategy,
                "improvements": result,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cache optimization failed: {str(e)}"
            )

    async def predict_cache_requirements(
        self,
        timeframe: str = "1h"
    ) -> Dict:
        """
        Predict future cache requirements.
        """
        try:
            # Collect cache stats
            stats = await self._collect_cache_stats(timeframe)
            
            # Generate predictions
            predictions = await self._predict_requirements(stats)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(predictions)
            
            return {
                "predictions": predictions,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cache prediction failed: {str(e)}"
            )

    async def manage_cache_invalidation(
        self,
        invalidation_rules: Dict
    ) -> Dict:
        """
        Manage smart cache invalidation.
        """
        try:
            # Validate rules
            validated = await self._validate_invalidation_rules(invalidation_rules)
            
            # Apply rules
            result = await self._apply_invalidation_rules(validated)
            
            # Monitor effects
            effects = await self._monitor_invalidation_effects(result)
            
            return {
                "rules": validated,
                "effects": effects,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cache invalidation failed: {str(e)}"
            )

    async def _generate_cache_key(self, request_data: Dict, endpoint: str) -> str:
        """Generate unique cache key."""
        # Normalize request data
        normalized = json.dumps(request_data, sort_keys=True)
        
        # Generate hash
        key_hash = hashlib.sha256(
            f"{endpoint}:{normalized}".encode()
        ).hexdigest()
        
        return f"cache:{endpoint}:{key_hash}"

    async def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if data exists in cache."""
        with self.cache_latency.time():
            cached_data = self.redis.get(cache_key)
            
        if cached_data:
            return json.loads(cached_data)
        return None

    async def _predict_optimal_ttl(self, request_data: Dict, endpoint: str) -> int:
        """Predict optimal TTL for cache entry."""
        # Extract features
        features = await self._extract_ttl_features(request_data, endpoint)
        
        # Generate prediction
        prediction = self.ttl_predictor.predict(np.array([features]))
        
        # Convert to seconds (minimum 60 seconds, maximum 24 hours)
        ttl = int(max(60, min(86400, prediction[0][0])))
        
        return ttl

    async def _store_in_cache(
        self,
        cache_key: str,
        data: Dict,
        ttl: int
    ) -> None:
        """Store data in cache with TTL."""
        with self.cache_latency.time():
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )

    async def _extract_ttl_features(
        self,
        request_data: Dict,
        endpoint: str
    ) -> List[float]:
        """Extract features for TTL prediction."""
        # Get endpoint stats
        stats = await self.cache_stats.find_one({"endpoint": endpoint})
        
        return [
            stats.get("avg_hit_rate", 0.5),
            stats.get("avg_ttl", 300),
            stats.get("data_size", 1000),
            stats.get("request_frequency", 1),
            len(json.dumps(request_data))
        ]

    async def _analyze_cache_performance(self, endpoint: str) -> Dict:
        """Analyze cache performance for endpoint."""
        # Get cache stats
        stats = await self.cache_stats.find({
            "endpoint": endpoint,
            "timestamp": {
                "$gte": datetime.utcnow() - timedelta(hours=24)
            }
        }).to_list(None)
        
        # Calculate metrics
        hit_rate = sum(s["hits"] for s in stats) / max(1, sum(s["total"] for s in stats))
        avg_latency = sum(s["latency"] for s in stats) / len(stats) if stats else 0
        
        return {
            "hit_rate": hit_rate,
            "avg_latency": avg_latency,
            "total_requests": sum(s["total"] for s in stats),
            "cache_size": sum(s["size"] for s in stats)
        }

    async def _generate_optimization_strategy(self, analysis: Dict) -> Dict:
        """Generate cache optimization strategy."""
        strategy = {
            "ttl_adjustment": 0,
            "prefetch_enabled": False,
            "compression_enabled": False
        }
        
        # Adjust TTL based on hit rate
        if analysis["hit_rate"] < 0.5:
            strategy["ttl_adjustment"] = 300  # Increase TTL by 5 minutes
        
        # Enable prefetching for high-traffic endpoints
        if analysis["total_requests"] > 1000:
            strategy["prefetch_enabled"] = True
        
        # Enable compression for large cache entries
        if analysis["cache_size"] > 1024 * 1024:  # 1MB
            strategy["compression_enabled"] = True
        
        return strategy
