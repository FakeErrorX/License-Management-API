from datetime import datetime
from typing import Dict, Any
import asyncio
from app.core.feature_tracker import feature_registry
from app.core.logger import logger
from app.core.health_checks import FeatureHealthCheck

class FeatureMonitor:
    def __init__(self):
        self.last_check: Dict[str, datetime] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        
    async def monitor_features(self):
        while True:
            for feature_name, feature in feature_registry.get_all_features().items():
                if feature.status == FeatureStatus.COMPLETED:
                    try:
                        # Use the feature-specific health check
                        health_status = await FeatureHealthCheck.get_feature_health(feature_name)
                        self.health_status[feature_name] = health_status
                        self.last_check[feature_name] = datetime.utcnow()
                        
                        if health_status["status"] != "healthy":
                            logger.warning(f"Feature {feature_name} health check failed: {health_status['details']}")
                    except Exception as e:
                        logger.error(f"Error monitoring feature {feature_name}: {str(e)}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def get_health_status(self) -> Dict[str, Any]:
        return {
            "health_status": self.health_status,
            "last_check": self.last_check
        }

feature_monitor = FeatureMonitor() 