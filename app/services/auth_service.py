from datetime import datetime, timezone, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User
from app.schemas.response.auth import AuthResponse, UserResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ALGORITHM = "HS256"


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)


def _to_auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        token=_create_token(user.id),
        user=UserResponse(id=user.id, name=user.name, email=user.email, avatar_path=user.avatar_path),
    )


async def register(name: str, email: str, password: str) -> AuthResponse:
    if await User.filter(email=email).exists():
        raise ValueError("Email already registered")
    user = await User.create(name=name, email=email, password_hash=_hash_password(password))
    return _to_auth_response(user)


async def login(email: str, password: str) -> AuthResponse:
    user = await User.filter(email=email).first()
    if not user or not _verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return _to_auth_response(user)


async def get_profile(user_id: int) -> UserResponse:
    user = await User.get(id=user_id)
    return UserResponse(id=user.id, name=user.name, email=user.email, avatar_path=user.avatar_path)
