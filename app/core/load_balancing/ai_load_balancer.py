from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.load_balancing import ServerNode, LoadBalancerConfig, BalancingMetrics
from app.core.analytics import APIAnalytics

class AILoadBalancer:
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.nodes: Dict[str, ServerNode] = {}
        self.health_checks: Dict[str, datetime] = {}
        self.load_distribution: Dict[str, float] = {}
        
    async def distribute_request(self, request_data: Dict[str, Any]) -> ServerNode:
        try:
            # Get available nodes
            healthy_nodes = await self._get_healthy_nodes()
            
            # Predict optimal node using AI
            optimal_node = await self._predict_optimal_node(request_data, healthy_nodes)
            
            # Update load distribution
            await self._update_load_stats(optimal_node)
            
            return optimal_node
        except Exception as e:
            logger.error(f"Load balancing failed: {str(e)}")
            raise
            
    async def _predict_optimal_node(self, request_data: Dict[str, Any], nodes: List[ServerNode]) -> ServerNode:
        # Use AI to predict best node based on:
        # - Current load
        # - Node performance history
        # - Request characteristics
        # - Geographic location
        scores = {}
        for node in nodes:
            score = await self._calculate_node_score(node, request_data)
            scores[node.id] = score
            
        best_node_id = max(scores, key=scores.get)
        return self.nodes[best_node_id]

    async def _calculate_node_score(self, node: ServerNode, request_data: Dict[str, Any]) -> float:
        metrics = await self.analytics.get_node_metrics(node.id)
        
        # Calculate weighted score based on multiple factors
        weights = {
            'load': 0.3,
            'latency': 0.2,
            'reliability': 0.2,
            'geo_proximity': 0.15,
            'resource_availability': 0.15
        }
        
        scores = {
            'load': self._calculate_load_score(metrics.current_load),
            'latency': self._calculate_latency_score(metrics.avg_latency),
            'reliability': self._calculate_reliability_score(metrics.uptime),
            'geo_proximity': self._calculate_proximity_score(node, request_data),
            'resource_availability': self._calculate_resource_score(metrics)
        }
        
        return sum(weights[k] * scores[k] for k in weights) 