from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar_path: str | None = None


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
