from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.dependencies.services import InjectedProductService
from app.schemas.request.product import ProductSearchRequest

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/sample")
async def sample_product(service: InjectedProductService):
    candidates = await service.sample_product()
    return {"result": candidates}


@router.post("/search")
async def search_products(request: ProductSearchRequest, service: InjectedProductService):
    if not request.query_text and not request.image_url:
        raise HTTPException(status_code=400, detail="Cần cung cấp query_text hoặc image_url")
    top_k = min(request.top_k or 5, 20)

    candidates = await service.hybrid_search(request.query_text, top_k)
    return {"result": candidates}


@router.post("/search/stream")
async def search_products_stream(request: ProductSearchRequest, service: InjectedProductService):
    if not request.query_text:
        raise HTTPException(status_code=400, detail="Cần cung cấp query_text")
    top_k = min(request.top_k or 5, 20)

    return StreamingResponse(
        service.rag_search_stream(request.query_text, limit=top_k),
        media_type="application/x-ndjson",
    )
