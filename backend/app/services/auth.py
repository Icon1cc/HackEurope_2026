from uuid import UUID

from app.repositories.user import UserRepository
from app.schemas.auth import UserRegister, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserRegister) -> UserResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        user = await self.repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            company_name=data.company_name,
        )
        return UserResponse.model_validate(user)

    async def login(self, data) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is disabled")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Invalid or expired refresh token")

        user_id = UUID(payload["sub"])
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or disabled")

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_current_user(self, user_id: UUID) -> UserResponse | None:
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        return UserResponse.model_validate(user)
