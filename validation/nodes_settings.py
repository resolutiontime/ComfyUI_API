from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union
from enum import Enum


class ProcessType(str, Enum):
    PORTRAIT = "portrait"
    PORTRAIT_DT = "portrait_dt"
    POSE = "pose"
    POSE_DT = "pose_dt"
    PORTRAIT_TO_POSE = "portrait_to_pose"

class BaseProcessParams(BaseModel):
    """Базовые параметры для всех процессов"""
    width: int = Field(896, ge=64, le=2048)
    height: int = Field(1216, ge=64, le=2048)
    steps: int = Field(20, ge=18, le=30)
    seed: int = Field(1)
    sampler: str = Field('dpmpp_2m_sde')
    scheduler: str = Field('karras')
    lora_settings: dict = {'1':1s,'2':2}


class PortraitParams(BaseProcessParams):
    """Специфичные параметры для портрета"""
    steps: int = Field(20, ge=18, le=30)
    cfg: float = Field(2, ge=1.5, le=4)
    prompt: str = "portrait of a person"
#     negative_prompt: str = "blurry, bad quality"
#     seed: int = -1

class PoseParams(BaseProcessParams):
    """Специфичные параметры для позы"""
    steps: int = Field(25, ge=18, le=30)
    cfg: float = Field(3, ge=1.5, le=4)
    prompt: str = "Pose of a person"


#     pose_image: Optional[str] = None
#     prompt: str = "full body pose"
#     denoise_strength: float = Field(0.7, ge=0.0, le=1.0)

class PoseFaceDetailParams(PoseParams):
    pass
#     """Параметры для позы с детализацией лица"""
#     face_restore_model: str = "GFPGAN"
#     face_detail_strength: float = Field(0.5, ge=0.0, le=1.0)