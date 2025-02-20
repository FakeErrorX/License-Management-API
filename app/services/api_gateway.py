from typing import Dict, List, Optional
from fastapi import HTTPException, Request
from datetime import datetime
import httpx
import jwt
import redis
import logging
from app.core.config import settings

class APIGatewayService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.logger = logging.getLogger(__name__)
        self.http_client = httpx.AsyncClient()

    async def route_request(self, request: Request, target_service: str) -> Dict:
        """Route and load balance API requests."""
        try:
            # Get available service instances
            instances = await self._get_service_instances(target_service)
            if not instances:
                raise HTTPException(status_code=503, detail="Service unavailable")

            # Select instance using load balancing
            instance = await self._load_balance(instances)

            # Apply request policies
            await self._apply_request_policies(request)

            # Forward request
            response = await self._forward_request(request, instance)

            # Record metrics
            await self._record_request_metrics(target_service, response)

            return response
        except Exception as e:
            self.logger.error(f"Request routing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def register_service(self, service_info: Dict) -> Dict:
        """Register a new service in the mesh."""
        try:
            service_id = service_info["service_id"]
            service_key = f"service:{service_id}"

            # Store service info
            self.redis.hset(
                service_key,
                mapping={
                    "name": service_info["name"],
                    "url": service_info["url"],
                    "health_check": service_info["health_check"],
                    "registered_at": datetime.now().isoformat()
                }
            )

            # Set service TTL
            self.redis.expire(service_key, 300)  # 5 minutes

            return {
                "service_id": service_id,
                "status": "registered",
                "ttl": 300
            }
        except Exception as e:
            self.logger.error(f"Service registration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def configure_circuit_breaker(self, config: Dict) -> Dict:
        """Configure circuit breaker for a service."""
        try:
            service_id = config["service_id"]
            breaker_key = f"circuit_breaker:{service_id}"

            # Store circuit breaker config
            self.redis.hset(
                breaker_key,
                mapping={
                    "failure_threshold": config["failure_threshold"],
                    "reset_timeout": config["reset_timeout"],
                    "half_open_timeout": config["half_open_timeout"]
                }
            )

            return {
                "service_id": service_id,
                "status": "configured",
                "config": config
            }
        except Exception as e:
            self.logger.error(f"Circuit breaker configuration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def setup_rate_limiting(self, config: Dict) -> Dict:
        """Set up rate limiting for a service."""
        try:
            service_id = config["service_id"]
            rate_key = f"rate_limit:{service_id}"

            # Store rate limit config
            self.redis.hset(
                rate_key,
                mapping={
                    "requests_per_second": config["requests_per_second"],
                    "burst_size": config["burst_size"],
                    "user_limit": config.get("user_limit", 0)
                }
            )

            return {
                "service_id": service_id,
                "status": "configured",
                "config": config
            }
        except Exception as e:
            self.logger.error(f"Rate limiting setup failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def configure_service_mesh(self, mesh_config: Dict) -> Dict:
        """Configure service mesh policies."""
        try:
            mesh_id = mesh_config["mesh_id"]
            mesh_key = f"service_mesh:{mesh_id}"

            # Store mesh configuration
            self.redis.hset(
                mesh_key,
                mapping={
                    "timeout": mesh_config["timeout"],
                    "retry_policy": mesh_config["retry_policy"],
                    "circuit_breaker": mesh_config["circuit_breaker"],
                    "load_balancer": mesh_config["load_balancer"]
                }
            )

            return {
                "mesh_id": mesh_id,
                "status": "configured",
                "config": mesh_config
            }
        except Exception as e:
            self.logger.error(f"Service mesh configuration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_service_instances(self, service: str) -> List[Dict]:
        """Get available service instances."""
        instances = []
        for key in self.redis.scan_iter(f"service:{service}:*"):
            instance = self.redis.hgetall(key)
            if instance and await self._check_health(instance["url"]):
                instances.append(instance)
        return instances

    async def _load_balance(self, instances: List[Dict]) -> Dict:
        """Select instance using load balancing."""
        # Simple round-robin for now
        key = "load_balancer:counter"
        counter = self.redis.incr(key) % len(instances)
        return instances[counter]

    async def _apply_request_policies(self, request: Request) -> None:
        """Apply request policies (authentication, rate limiting, etc.)."""
        # Verify JWT if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token")

        # Apply rate limiting
        client_ip = request.client.host
        rate_key = f"rate_limit:{client_ip}"
        if self.redis.get(rate_key):
            raise HTTPException(status_code=429, detail="Too many requests")
        self.redis.setex(rate_key, 1, 60)  # 1 request per minute

    async def _forward_request(self, request: Request, instance: Dict) -> Dict:
        """Forward request to selected instance."""
        url = instance["url"]
        method = request.method.lower()
        headers = dict(request.headers)
        body = await request.body()

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                content=body
            )
            return response.json()

    async def _record_request_metrics(self, service: str, response: Dict) -> None:
        """Record request metrics."""
        metrics_key = f"metrics:{service}:{datetime.now().strftime('%Y-%m-%d')}"
        self.redis.hincrby(metrics_key, "requests", 1)
        self.redis.hincrby(metrics_key, "response_time", response.get("duration", 0))

    async def _check_health(self, url: str) -> bool:
        """Check service health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health")
                return response.status_code == 200
        except Exception:
            return False
