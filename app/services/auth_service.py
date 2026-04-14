from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User
from app.schemas.response.auth import AuthResponse, UserResponse


class AuthService:
    def __init__(self):
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def register(self, name: str, email: str, password: str) -> AuthResponse:
        if await User.filter(email=email).exists():
            raise ValueError("Email already registered")
        user = await User.create(name=name, email=email, password_hash=self._hash_password(password))
        return self._to_auth_response(user)

    async def login(self, email: str, password: str) -> AuthResponse:
        user = await User.filter(email=email).first()
        if not user or not self._verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        return self._to_auth_response(user)

    async def get_profile(self, user_id: int) -> UserResponse:
        user = await User.get(id=user_id)
        return self._to_user_response(user)

    def _to_auth_response(self, user: User) -> AuthResponse:
        return AuthResponse(
            token=self._create_token(user.id),
            user=self._to_user_response(user),
        )

    def _to_user_response(self, user: User) -> UserResponse:
        return UserResponse(id=user.id, name=user.name, email=user.email, avatar_path=user.avatar_path)

    def _create_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(
            {"sub": str(user_id), "exp": expire}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def _hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)
