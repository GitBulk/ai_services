from app.core.settings import settings
from app.services.faiss_vector_service import FaissVectorService
from app.services.text_embedding_service import TextEmbeddingService
from app.services.in_memory_vector_service import InMemoryVectorService

class ServiceRegistry:
    def __init__(self, settings):
        self.text_service = None
        self.settings = settings
        self.services = {}

    def initialize(self, model_registry, resource_manager):
        # text service
        text_model = model_registry.get('text_embedding')
        self.services['text'] = TextEmbeddingService(text_model)

        # vector service
        if self.settings.VECTOR_BACKEND == 'faiss':
            self.services['vector'] = FaissVectorService(resource_manager=resource_manager, use_cosine = True)
        else:
            self.services['vector'] = InMemoryVectorService(self.text_service)

    def get(self, name):
        return self.services[name]

# ServiceRegistry → quản lý service
service_registry = ServiceRegistry(settings)
