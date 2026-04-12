from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# from app.services.processor import processor
# from app.core import service_registry
from app.core.service_registry import service_registry
from app.dependencies.services import InjectedProductService
from app.schemas.request.product import ProductSearchRequest

router = APIRouter()


class SimilarityRequest(BaseModel):
    sentence1: str
    sentence2: str


@router.post("/similarity")
def similarity(request: SimilarityRequest):
    # score = service_registry.text_service.similarity(request.sentence1, request.sentence2)
    score = service_registry.get("text").similarity(request.sentence1, request.sentence2)
    return {"score": float(score)}


@router.get("/online")
def debug_search():
    return {"online": True}


@router.get("/search/debug")
def debug_search(query: str):
    search_service = service_registry.get("search")
    return search_service.debug_search(query)


@router.get("/sample_product")
async def sample_product(service: InjectedProductService):
    candidates = await service.sample_product()
    return {"result": candidates}


@router.post("/search_products")
async def search(request: ProductSearchRequest, service: InjectedProductService):
    if not request.query_text and not request.image_url:
        raise HTTPException(status_code=400, detail="Cần cung cấp query_text hoặc image_url")
    print(f"🚀 Searching: {request.query_text}")
    top_k = min(request.top_k or 5, 20)

    candidates = await service.hybrid_search(request.query_text, top_k)
    return {"result": candidates}


@router.post("/search_products_stream")
async def search_products_stream(request: ProductSearchRequest, service: InjectedProductService):
    if not request.query_text:
        raise HTTPException(status_code=400, detail="Cần cung cấp query_text")
    top_k = min(request.top_k or 5, 20)

    return StreamingResponse(
        service.rag_search_stream(request.query_text, limit=top_k),
        media_type="application/x-ndjson",
    )
