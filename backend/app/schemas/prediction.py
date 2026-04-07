from pydantic import BaseModel
from typing import Dict, List, Optional


class PatchPrediction(BaseModel):
    bbox: List[int]
    damage_class: str
    confidence: float


class SourceDimensions(BaseModel):
    width: int
    height: int


class PredictionResponse(BaseModel):
    damage_class: str
    confidence: float
    probabilities: Dict[str, float]
    hotspots: Optional[List[PatchPrediction]] = []
    source_dimensions: Optional[SourceDimensions] = None
