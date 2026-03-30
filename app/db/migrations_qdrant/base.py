from qdrant_client import QdrantClient, models


class QdrantMigrationError(Exception):
    """Exception tùy chỉnh cho lỗi Migration"""

    pass


class QdrantMigration:
    def __init__(self, qdrant_db: QdrantClient):
        self.qdrant_db = qdrant_db

    def has_collection(self, collection_name: str) -> bool:
        return self.qdrant_db.collection_exists(collection_name)

    def create_collection(self, name: str, size: int = 512, dist=models.Distance.COSINE):
        if self.has_collection(name):
            raise QdrantMigrationError(f"Collection '{name}' is already exists.")

        return self.qdrant_db.create_collection(
            collection_name=name, vectors_config=models.VectorParams(size=size, distance=dist)
        )

    def set_alias_for_collection(self, collection_name: str, alias_name: str):
        if not self.has_collection(collection_name):
            raise QdrantMigrationError(f"Collection '{collection_name}' is not exists.")

        action = models.CreateAliasOperation(
            create_alias=models.CreateAlias(collection_name=collection_name, alias_name=alias_name)
        )
        self.qdrant_db.update_collection_aliases(change_aliases_operations=[action])

    def drop_col(self, name: str):
        return self.qdrant_db.delete_collection(collection_name=name)

    def add_index(
        self, col_name: str, field_name: str, field_type: models.PayloadSchemaType = models.PayloadSchemaType.KEYWORD
    ):
        return self.qdrant_db.create_payload_index(
            collection_name=col_name,
            field_name=field_name,
            field_schema=field_type,
        )

    # --- Helper: Quản lý Alias (Zero-downtime) ---
    def switch_alias(self, alias_name: str, col_name: str):
        action = models.RenameAliasOperation(
            rename_alias=models.RenameAlias(
                old_alias_name=alias_name,
                new_alias_name=alias_name,  # Alias name stays the same, its target changes
                collection_name=col_name,
            )
        )
        return self.qdrant_db.update_collection_aliases(change_alias_operations=[action])
        # return self.qdrant_db.update_collection_aliases(
        #     change=[models.CreateAliasOperation(alias_name=alias_name, collection_name=col_name)]
        # )
