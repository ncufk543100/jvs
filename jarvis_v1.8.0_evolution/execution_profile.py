from enum import Enum
from typing import Dict, Any

class ExecutionProfile(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    LEARNING = "learning"

class ProfileContext:
    def __init__(self, profile: ExecutionProfile = ExecutionProfile.DEVELOPMENT):
        self.profile = profile
        self.context: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {"profile": self.profile.value, "context": self.context}

def get_current_profile() -> ProfileContext:
    return ProfileContext(ExecutionProfile.DEVELOPMENT)