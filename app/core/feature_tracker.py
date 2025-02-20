from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class FeatureStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TESTING = "testing"

class FeatureTracker(BaseModel):
    name: str
    status: FeatureStatus
    description: str
    dependencies: Optional[List[str]] = []
    completion_percentage: float = 0.0
    
class FeatureRegistry:
    def __init__(self):
        self.features: Dict[str, FeatureTracker] = {}
        
    def register_feature(self, feature: FeatureTracker):
        self.features[feature.name] = feature
        
    def update_status(self, feature_name: str, status: FeatureStatus):
        if feature_name in self.features:
            self.features[feature_name].status = status
            
    def get_feature(self, feature_name: str) -> Optional[FeatureTracker]:
        return self.features.get(feature_name)
    
    def get_all_features(self) -> Dict[str, FeatureTracker]:
        return self.features

feature_registry = FeatureRegistry() 