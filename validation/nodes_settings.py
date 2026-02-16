from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List
from enum import Enum


class ProcessType(str, Enum):
    PORTRAIT = "portrait"
    PORTRAIT_DT = "portrait_dt"
    POSE = "pose"
    POSE_DT = "pose_dt"
    PORTRAIT_TO_POSE = "portrait_to_pose"


# ============================================================================
# Lora Settings
# ============================================================================

class LoraSlot(BaseModel):
    """Настройки одного слота Lora"""
    on: bool = Field(True, description="Включить/выключить Lora")
    lora: str = Field(..., description="Путь к файлу Lora (например: 'Pony\\\\Realism_slider.safetensors')")
    strength: float = Field(1.0, ge=-2.0, le=3.0, description="Сила применения Lora")


class LoraPreset(str, Enum):
    """Предустановленные пресеты Lora"""
    NONE = "none"              # Без Lora
    REALISTIC = "realistic"    # Реалистичный стиль
    CARTOON = "cartoon"        # Мультяшный стиль  
    BEAUTY = "beauty"          # Красота/гламур
    CUSTOM = "custom"          # Ручная настройка через lora_slots


# Пресеты Lora — набор слотов для каждого пресета
LORA_PRESETS: Dict[LoraPreset, List[LoraSlot]] = {
    LoraPreset.NONE: [],
    LoraPreset.REALISTIC: [
        LoraSlot(on=True, lora="Pony\\Realism_slider.safetensors", strength=0.6),
        LoraSlot(on=True, lora="Pony\\mature_female_slider.safetensors", strength=0.8),
    ],
    LoraPreset.CARTOON: [
        LoraSlot(on=True, lora="Pony\\Cartoon\\ExpressiveH (Hentai LoRa Style).safetensors", strength=1.4),
        LoraSlot(on=True, lora="Pony\\Cartoon\\Detail Tweaker XL.safetensors", strength=1.5),
    ],
    LoraPreset.BEAUTY: [
        LoraSlot(on=True, lora="Pony\\Crazy Girlfriend Mix.safetensors", strength=0.7),
        LoraSlot(on=True, lora="Pony\\Real_Beauty.safetensors", strength=0.6),
    ],
    LoraPreset.CUSTOM: [],  # При CUSTOM используются lora_slots
}


class LoraSettings(BaseModel):
    """
    Настройки Lora для workflow.
    
    Можно использовать:
    1. Пресет: preset="realistic" — применит предустановленный набор Lora
    2. Кастомный: preset="custom", lora_slots=[...] — явное указание Lora
    3. Комбинация: preset="realistic", lora_slots=[...] — пресет + дополнительные Lora
    """
    preset: LoraPreset = Field(
        LoraPreset.NONE, 
        description="Пресет Lora (none/realistic/cartoon/beauty/custom)"
    )
    lora_slots: Optional[List[LoraSlot]] = Field(
        None, 
        description="Список Lora для применения (используется при preset=custom или как дополнение к пресету)"
    )
    
    def get_all_lora_slots(self) -> List[LoraSlot]:
        """Возвращает итоговый список Lora слотов (пресет + кастомные)"""
        result: List[LoraSlot] = []
        
        # Добавляем Lora из пресета (кроме CUSTOM и NONE)
        if self.preset not in (LoraPreset.CUSTOM, LoraPreset.NONE):
            result.extend(LORA_PRESETS.get(self.preset, []))
        
        # Добавляем кастомные слоты
        if self.lora_slots:
            result.extend(self.lora_slots)
        
        return result


# ============================================================================
# Process Parameters
# ============================================================================

class BaseProcessParams(BaseModel):
    """Базовые параметры для всех процессов"""
    width: int = Field(896, ge=64, le=2048)
    height: int = Field(1216, ge=64, le=2048)
    steps: int = Field(20, ge=18, le=30)
    seed: int = Field(1)
    sampler: str = Field('dpmpp_2m_sde')
    scheduler: str = Field('karras')
    lora_settings: Optional[LoraSettings] = Field(
        None, 
        description="Настройки Lora (пресет или кастомный список)"
    )


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