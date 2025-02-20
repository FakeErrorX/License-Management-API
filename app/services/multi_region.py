from typing import Dict, List, Optional
from fastapi import HTTPException
from datetime import datetime
import httpx
import redis
from app.core.config import settings

class MultiRegionService:
    def __init__(self, db):
        self.db = db
        self.regions = self.db.regions
        self.redis = redis.from_url(settings.REDIS_URL)
        self.http_client = httpx.AsyncClient()

    async def register_region(
        self,
        region_id: str,
        endpoint: str,
        location: Dict[str, float],  # {latitude: float, longitude: float}
        capacity: Dict[str, int]  # {max_requests: int, max_users: int}
    ) -> Dict:
        """Register a new API region."""
        try:
            # Verify endpoint health
            health_check = await self.http_client.get(f"{endpoint}/health")
            if health_check.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Region endpoint health check failed"
                )

            region_data = {
                "region_id": region_id,
                "endpoint": endpoint,
                "location": location,
                "capacity": capacity,
                "status": "active",
                "current_load": 0,
                "registered_at": datetime.now()
            }

            await self.regions.insert_one(region_data)

            # Cache region data
            self.redis.hset(
                f"region:{region_id}",
                mapping={
                    "endpoint": endpoint,
                    "status": "active",
                    "current_load": "0"
                }
            )

            return {
                "region_id": region_id,
                "status": "registered",
                "endpoint": endpoint
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Region registration failed: {str(e)}"
            )

    async def get_nearest_region(
        self,
        location: Dict[str, float]  # {latitude: float, longitude: float}
    ) -> Dict:
        """Get the nearest available region based on geolocation."""
        try:
            # Get all active regions
            regions = await self.regions.find(
                {"status": "active"}
            ).to_list(None)

            if not regions:
                raise HTTPException(
                    status_code=404,
                    detail="No active regions available"
                )

            # Calculate distances and find nearest region
            nearest_region = min(
                regions,
                key=lambda r: self._calculate_distance(
                    location,
                    r["location"]
                )
            )

            return {
                "region_id": nearest_region["region_id"],
                "endpoint": nearest_region["endpoint"],
                "distance_km": self._calculate_distance(
                    location,
                    nearest_region["location"]
                )
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to find nearest region: {str(e)}"
            )

    async def update_region_load(
        self,
        region_id: str,
        current_load: int
    ) -> Dict:
        """Update the current load of a region."""
        try:
            # Update in database
            await self.regions.update_one(
                {"region_id": region_id},
                {"$set": {"current_load": current_load}}
            )

            # Update in cache
            self.redis.hset(
                f"region:{region_id}",
                "current_load",
                str(current_load)
            )

            return {
                "region_id": region_id,
                "current_load": current_load,
                "updated_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update region load: {str(e)}"
            )

    async def route_request(
        self,
        user_location: Optional[Dict[str, float]] = None,
        preferred_region: Optional[str] = None
    ) -> Dict:
        """Route an API request to the most appropriate region."""
        try:
            if preferred_region:
                # Check if preferred region is available
                region = await self.regions.find_one({
                    "region_id": preferred_region,
                    "status": "active"
                })
                if region:
                    return {
                        "region_id": region["region_id"],
                        "endpoint": region["endpoint"]
                    }

            if user_location:
                # Route based on location
                return await self.get_nearest_region(user_location)

            # Load balancing if no location or preferred region
            regions = await self.regions.find(
                {"status": "active"}
            ).to_list(None)

            if not regions:
                raise HTTPException(
                    status_code=404,
                    detail="No active regions available"
                )

            # Select region with lowest load
            selected_region = min(
                regions,
                key=lambda r: r["current_load"]
            )

            return {
                "region_id": selected_region["region_id"],
                "endpoint": selected_region["endpoint"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Request routing failed: {str(e)}"
            )

    def _calculate_distance(
        self,
        point1: Dict[str, float],
        point2: Dict[str, float]
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in kilometers

        lat1 = radians(point1["latitude"])
        lon1 = radians(point1["longitude"])
        lat2 = radians(point2["latitude"])
        lon2 = radians(point2["longitude"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c

        return distance
