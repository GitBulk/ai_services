import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.model_registry import model_registry

# from app.services.processor import processor
# from app.core import service_registry
from app.core.service_registry import service_registry
from app.schemas.product import ProductSearchRequest
from app.services import processor

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
        "processed_on": str(gpu_tensor.device),  # Trả về 'mps:0' nếu chạy trên GPU Mac
        "status": "Success",
    }


class SimilarityRequest(BaseModel):
    sentence1: str
    sentence2: str


@router.post("/similarity")
def similarity(request: SimilarityRequest):
    # score = service_registry.text_service.similarity(request.sentence1, request.sentence2)
    score = service_registry.get("text").similarity(request.sentence1, request.sentence2)
    return {"score": float(score)}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


# @router.post('/search')
# def search(request: SearchRequest):
#     result = service_registry.in_memory_vector_service.search(request.query, request.top_k)
#     return { 'result': result }


@router.get("/search/debug")
def debug_search(query: str):
    search_service = service_registry.get("search")
    return search_service.debug_search(query)


@router.post("/search_products")
def search(request: ProductSearchRequest):
    if not request.query_text and not request.image_url:
        raise HTTPException(status_code=400, detail="Cần cung cấp query_text hoặc image_url")

    top_k = min(request.top_k or 5, 20)
    query_vector = model_registry.encode_multimodal(text=request.query_text, image_url=request.image_url)
    vector_service = service_registry.get("product_service")
    candidates = vector_service.search(query_vector=query_vector, top_k=top_k)

    return {"result": candidates}


class ScamDetectionRequest(BaseModel):
    message: str
    language: str = "en"  # 'en', 'es', 'vi'


@router.post("/detect-scam")
async def detect_scam(request: ScamDetectionRequest):
    """
    Detect scam/spam messages with fuzzy matching and context analysis.

    Args:
        message: The message text to analyze
        language: Language code ('en', 'es', 'vi') - default 'en'

    Returns:
        {
            'is_scam': bool,
            'scam_score': float (0-100),
            'reason': str,
            'keywords_found': dict,
            'context': dict
        }
    """
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if request.language not in ["en", "es", "vi"]:
        raise HTTPException(status_code=400, detail="Language must be 'en', 'es', or 'vi'")

    service = service_registry.get("scam_detection")
    result = service.detect(request.message, request.language)

    return result
