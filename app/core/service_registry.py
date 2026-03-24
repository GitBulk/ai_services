from app.core.settings import settings
from app.services.faiss_vector_service import FaissVectorService
from app.services.ranking.cross_encoder_reranker import CrossEncoderReranker
from app.services.ranking.heuristic_reranker import HeuristicReranker
from app.services.retrieval.retriever import Retriever
from app.services.search_service import SearchService
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
            self.services['text_vector'] = FaissVectorService(resource_manager=resource_manager, index_name='text', use_cosine = True)
            self.services['product_vector'] = FaissVectorService(resource_manager=resource_manager, index_name='product', use_cosine = True)
        else:
            self.services['text_vector'] = InMemoryVectorService(self.text_service)

        if self.settings.RERANKER == 'cross':
            self.services['reranker'] = CrossEncoderReranker()
        else:
            self.services['reranker'] = HeuristicReranker()

        self.services['retriever'] = Retriever(vector_service=self.services['text_vector'], text_service=self.services['text'])
        self.services['search'] = SearchService(retriever=self.services['retriever'], reranker=self.services['reranker'])

    def get(self, name):
        return self.services[name]

# ServiceRegistry → quản lý service
service_registry = ServiceRegistry(settings)
