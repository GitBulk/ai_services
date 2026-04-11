from typing import Annotated

from fastapi import Depends

from app.core.model_registry import ModelRegistry
from app.dependencies.ai_model import get_ai_model_registry
from app.dependencies.repositories import (
    get_async_product_vector_repository,
    get_product_repository,
)
from app.repositories.async_product_vector_repository import AsyncProductVectorRepository
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService


def get_product_service(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    vector_repo: Annotated[AsyncProductVectorRepository, Depends(get_async_product_vector_repository)],
    ai_model: Annotated[ModelRegistry, Depends(get_ai_model_registry)],
) -> ProductService:
    return ProductService(product_repo, vector_repo, ai_model)


InjectedProductService = Annotated[ProductService, Depends(get_product_service)]
