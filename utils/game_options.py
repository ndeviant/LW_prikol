from typing import Dict, Any
from pydantic import BaseModel, Field

class GameOptions(BaseModel):
    """Game configuration options"""
    debug: bool = Field(False, description="Enable debug mode")
    sleep: float = Field(3.0, ge=0.0, description="Base sleep time between actions")
    launch_wait_time: int = Field(35, ge=0, description="Time to wait for game to launch")
    tap_delay: float = Field(1.0, ge=0.0, description="Delay between taps")
    template_match_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Template matching threshold")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries for operations")
    health_check_interval: int = Field(3, ge=0, description="Interval between health checks")
    package_name: str = Field("com.fun.lastwar.gp", description="Game package name") 