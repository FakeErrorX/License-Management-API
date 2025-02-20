from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.discovery import ServiceRegistry, ServiceInstance
from app.core.ai.discovery_ai import DiscoveryAI

class ServiceRegistryManager:
    def __init__(self):
        self.registry = ServiceRegistry()
        self.health_checker = HealthChecker()
        self.load_balancer = LoadBalancer()
        
    async def register_service(self, service: ServiceInstance) -> bool:
        try:
            # Validate service
            await self._validate_service(service)
            
            # Register service
            self.registry.services[service.service_id] = service
            
            # Initialize health checks
            await self.health_checker.init_health_check(service)
            
            # Update load balancer
            await self.load_balancer.add_service(service)
            
            return True
            
        except Exception as e:
            logger.error(f"Service registration failed: {str(e)}")
            raise 