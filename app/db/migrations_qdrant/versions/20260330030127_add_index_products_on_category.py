from app.db.migrations_qdrant.base import QdrantMigration


class AddIndexProductsOnCategory(QdrantMigration):
    def up(self):
        self.add_index("dev_nova_products_alias", "master_category", "keyword")
        pass

    def down(self):
        pass
