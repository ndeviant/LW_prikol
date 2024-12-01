from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from pathlib import Path
import json
from logging_config import app_logger
from .constants import (
    SecretaryType,
    REQUIRED_SECRETARIES,
    OPTIONAL_SECRETARIES
)
from .game_options import GameOptions

class OCRConfig(BaseModel):
    """OCR configuration settings"""
    engine: int = Field(3, ge=0, le=4)
    page_seg_mode: int = Field(6, ge=0, le=13)
    whitelist: str = Field(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
        min_length=1
    )
    threshold: float = Field(0.7, ge=0.0, le=1.0)

class ImageConfig(BaseModel):
    """Image processing configuration"""
    match_threshold: float = Field(0.65, ge=0.0, le=1.0)
    secretary_match_threshold: float = Field(0.88, ge=0.0, le=1.0)
    min_distance: int = Field(20, ge=0)

class ButtonPosition(BaseModel):
    """Button position configuration"""
    x: str = Field(..., pattern=r'^\d+%$')
    y: str = Field(..., pattern=r'^\d+%$')
    
    @validator('x', 'y')
    def validate_percentage(cls, v):
        value = int(v.strip('%'))
        if not 0 <= value <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

class TemplateConfig(BaseModel):
    """Template paths configuration"""
    secretaries: Dict[str, str]
    buttons: Dict[str, str]

class PositionsConfig(BaseModel):
    """Button positions configuration"""
    list: ButtonPosition
    accept: ButtonPosition
    profile: ButtonPosition
    secretaryMenu: ButtonPosition

class Config(BaseModel):
    """Main configuration"""
    templates: TemplateConfig
    positions: PositionsConfig
    options: Dict[str, Any]
    ocr: OCRConfig
    image: ImageConfig

def load_and_validate_config(config_path: str = "config.json") -> Optional[Config]:
    """Load and validate configuration from file"""
    try:
        if not Path(config_path).exists():
            app_logger.error(f"Config file not found: {config_path}")
            return None
            
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        config = Config(**config_data)
        app_logger.info("Configuration validated successfully")
        return config
        
    except Exception as e:
        app_logger.error(f"Failed to load config: {e}")
        return None 