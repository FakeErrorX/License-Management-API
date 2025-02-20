from typing import Dict, Any, List
from datetime import datetime
import asyncio
from app.core.logger import logger
from app.models.monitoring import HealthCheck, ServiceStatus, AlertConfig
from app.core.analytics import APIAnalytics

class APIHealthMonitor:
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.health_checks: Dict[str, HealthCheck] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.alert_configs: Dict[str, AlertConfig] = {}
        
    async def monitor_api_health(self) -> Dict[str, Any]:
        try:
            # Perform comprehensive health checks
            health_results = await self._run_health_checks()
            
            # Analyze service status
            status = await self._analyze_service_status(health_results)
            
            # Check for anomalies
            anomalies = await self._detect_anomalies(status)
            
            # Generate health report
            report = await self._generate_health_report(health_results, status, anomalies)
            
            # Trigger alerts if needed
            if anomalies:
                await self._trigger_alerts(anomalies)
                
            return report
        except Exception as e:
            logger.error(f"Health monitoring failed: {str(e)}")
            raise 