from pydantic import BaseModel


class ProductSearchRequest(BaseModel):
    query_text: str | None = None
    image_url: str | None = None
    top_k: int = 5
