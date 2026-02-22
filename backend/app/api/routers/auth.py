from fastapi import APIRouter, Depends, HTTPException
from app.services.auth import AuthService
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
)
from app.core.dependencies import get_auth_service, get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.register(data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.login(data)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.refresh_tokens(data.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
