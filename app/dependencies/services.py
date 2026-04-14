from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.ai_models.model_manager import ModelManager
from app.dependencies.ai_model import get_model_manager
from app.dependencies.repositories import (
    get_async_product_vector_repository,
    get_product_repository,
)
from app.repositories.async_product_vector_repository import AsyncProductVectorRepository
from app.repositories.product_repository import ProductRepository
from app.services.auth_service import AuthService
from app.services.llm_service import LLMService
from app.services.product_service import ProductService


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache
def get_auth_service() -> AuthService:
    return AuthService()


# get_product_service takes arguments (the injected dependencies), so @lru_cache won't work on it.
# use plain factory function Annotated[ProductService, Depends(get_product_service)] instead.
def get_product_service(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    vector_repo: Annotated[AsyncProductVectorRepository, Depends(get_async_product_vector_repository)],
    ai_model: Annotated[ModelManager, Depends(get_model_manager)],
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
) -> ProductService:
    return ProductService(product_repo, vector_repo, ai_model, llm_service)


InjectedProductService = Annotated[ProductService, Depends(get_product_service)]
InjectedAuthService = Annotated[AuthService, Depends(get_auth_service)]
