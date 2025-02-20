from pydantic import BaseModel
from typing import Optional

class RateLimitConfig(BaseModel):
    requests_per_minute: int
    burst_limit: Optional[int] = None
    user_tier: str = "standard" 