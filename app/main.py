from fastapi import FastAPI
from app.core.signal_handler import setup_signal_handlers
from app.routes import router as nova_router
from app.core.settings import settings
from app.core.model_registry import model_registry
from app.core.service_registry import service_registry
from app.services.vector_resource_manager import VectorResourceManager

async def lifespan(app: FastAPI):
    print('[INFO] Starting Nova AI...')
    # load model
    model_registry.load_models()

    resource_manager = VectorResourceManager(index_path=settings.FAISS_INDEX_PATH, metadata_path=settings.FAISS_METADATA_PATH)
    resource_manager.initialize()

    service_registry.initialize(model_registry, resource_manager)

    # setup signals to reload index
    setup_signal_handlers(service_registry, model_registry)

    # Gán vào app.state để route có thể truy cập
    # app.state.service_registry = service_registry
    vector_service = service_registry.get('vector')
    vector_service.initialize()

    print('[INFO] Nova AI ready 🚀')

    yield

    # (optional) cleanup
    print('[INFO] Shutting down...')

app = FastAPI(
    title = settings.PROJECT_NAME,
    description = 'Nova AI',
    version = '1.0',
    lifespan = lifespan
)

app.include_router(nova_router, prefix = '/api/v1', tags = ['Nova Analysis'])

@app.get('/')
async def root():
    return {
        'message': 'Nova AI Service is running',
        'device': settings.DEVICE,
        'project': '#nova_ai',
        'version': settings.VERSION
    }