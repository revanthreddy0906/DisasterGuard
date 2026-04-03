from pydantic import BaseModel
from typing import Dict, List, Optional

class PatchPrediction(BaseModel):
    bbox: List[int]
    damage_class: str
    confidence: float

class PredictionResponse(BaseModel):
    damage_class: str
    confidence: float
    probabilities: Dict[str, float]
    hotspots: Optional[List[PatchPrediction]] = []
