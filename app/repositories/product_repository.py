from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_product_by_id(self, product_id: int) -> Product | None:
        # return self.db.query(Product).filter(Product.id == product_id).first()
        # return Product.find_by(self.db, id=product_id)
        pass

    def search_products(self, query: str, limit: int = 10) -> list[Product]:
        # return self.db.query(Product).filter(Product.name.ilike(f"%{query}%")).limit(limit).all()
        pass
