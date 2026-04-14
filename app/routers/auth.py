from fastapi import APIRouter, HTTPException, status

from app.dependencies.auth import CurrentUser
from app.dependencies.services import InjectedAuthService
from app.schemas.request.auth import LoginRequest, RegisterRequest
from app.schemas.response.auth import AuthResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, auth: InjectedAuthService):
    try:
        return await auth.register(request.name, request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, auth: InjectedAuthService):
    try:
        return await auth.login(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.get("/profile", response_model=UserResponse)
async def profile(current_user: CurrentUser, auth: InjectedAuthService):
    return await auth.get_profile(current_user.id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: CurrentUser):
    pass
