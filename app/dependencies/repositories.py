from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session

from app.db.qdrant_db import get_qdrant_db
from app.db.session import get_db
from app.repositories.product_repository import ProductRepository
from app.repositories.product_vector_repository import ProductVectorRepository


def get_product_repository(db: Annotated[Session, Depends(get_db)]) -> ProductRepository:
    # Inject ProductRepository, work with relation database (PostgreSQL)
    return ProductRepository(db)


def get_product_vector_repository(
    qdrant_db: Annotated[QdrantClient, Depends(get_qdrant_db)],
) -> ProductVectorRepository:
    # Inject ProductVectorRepository, work with vector database (Qdrant)
    return ProductVectorRepository(qdrant_db=qdrant_db)
