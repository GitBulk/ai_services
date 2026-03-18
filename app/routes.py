from pydantic import BaseModel
import torch
from fastapi import APIRouter, Depends, Request
# from app.services.processor import processor
# from app.core import service_registry
from app.core.service_registry import service_registry
from app.core.model_registry import model_registry
from app.services import processor
from app.services.text_embedding_service import TextEmbeddingService

router = APIRouter()

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
    # score = service_registry.text_service.similarity(request.sentence1, request.sentence2)
    score = service_registry.get('text').similarity(request.sentence1, request.sentence2)
    return { "score": float(score) }


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

# @router.post('/search')
# def search(request: SearchRequest):
#     result = service_registry.in_memory_vector_service.search(request.query, request.top_k)
#     return { 'result': result }

# def get_vector_service(request: Request):
#     return request.app.state.service_registry.get('vector')

def get_vector_service():
    return service_registry.get('vector')

@router.post('/search')
def search(request: SearchRequest, vector_service = Depends(get_vector_service)):
    query_vector = model_registry.encode_text(request.query)
    result = vector_service.search(query_vector = query_vector, top_k = request.top_k or 5)
    return { 'result': result }
