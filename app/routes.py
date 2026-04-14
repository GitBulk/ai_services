from fastapi import APIRouter

from app.routers import auth, nlp, products, system

router = APIRouter()

router.include_router(system.router)
router.include_router(auth.router)
router.include_router(products.router)
router.include_router(nlp.router)
