from typing import Any, Optional

from pydantic import BaseModel


class Quality(BaseModel):
    valid: bool
    fps: Optional[float] = None
    frames: Optional[int] = None
    duration: Optional[float] = None


class ModelAResult(BaseModel):
    available: bool
    prediction: Optional[int] = None
    score: Optional[float] = None
    status: Optional[str] = None
    quality: Optional[Quality] = None
    features: Optional[dict[str, Any]] = None


class ModelBResult(BaseModel):
    available: bool
    prediction: Optional[int] = None
    score: Optional[float] = None


class EnsembleResult(BaseModel):
    prediction: Optional[int] = None
    method: str


class ScreeningResponse(BaseModel):
    session_id: Optional[str] = None
    patient_id: str
    model_a: Optional[ModelAResult] = None
    model_b: Optional[ModelBResult] = None
    ensemble: Optional[EnsembleResult] = None
    disclaimer: str = "Kết quả sàng lọc, không phải chẩn đoán y tế."
