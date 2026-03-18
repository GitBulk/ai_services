from pydantic import BaseModel
import torch
from fastapi import APIRouter
from app.services.processor import processor
from app.core import service_registry
from services.text_embedding_service import TextEmbeddingService

router= APIRouter()

@router.post("/analyze")
async def analyze_document(content: str):
    # 1. làm sạch văn bảng bằng processor
    refined_text = processor.clean_historical_text(content)

    # 2. giả sử ta biến văn bản thành Tensor để hiểu AI
    mock_tensor = torch.randn(3, 3)
    gpu_tensor = processor.move_to_gpu(mock_tensor)

    return {
        "original": content,
        "refined": refined_text,
        "processed_on": str(gpu_tensor.device), # Trả về 'mps:0' nếu chạy trên GPU Mac
        "status": "Success"
    }

class SimilarityRequest(BaseModel):
    sentence1: str
    sentence2: str

@router.post("/similarity")
def similarity(request: SimilarityRequest):
    score = service_registry.text_service.similarity(request.sentence1, request.sentence2)
    return { "score": float(score) }
