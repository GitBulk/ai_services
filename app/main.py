from fastapi import FastAPI
from app.routes import router as nova_router
from app.core import settings, model_registry, service_registry
from data.sample_data import SAMPLE_DATA

async def lifespan(app: FastAPI):
    print('[INFO] Starting Nova AI...')
    model_registry.load_models()
    service_registry.init_services(model_registry)
    service_registry.vector_service.build_index(SAMPLE_DATA)
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