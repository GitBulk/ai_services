from fastapi import APIRouter

from app.core.service_registry import service_registry

router = APIRouter(tags=["System"])


@router.get("/online")
def online():
    return {"online": True}


@router.get("/search/debug")
def debug_search(query: str):
    search_service = service_registry.get("search")
    return search_service.debug_search(query)
