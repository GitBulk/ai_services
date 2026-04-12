from fastapi import APIRouter
from pydantic import BaseModel

from app.core.service_registry import service_registry

router = APIRouter(prefix="/nlp", tags=["NLP"])


class SimilarityRequest(BaseModel):
    sentence1: str
    sentence2: str


@router.post("/similarity")
def similarity(request: SimilarityRequest):
    score = service_registry.get("text").similarity(request.sentence1, request.sentence2)
    return {"score": float(score)}
