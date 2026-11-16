from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import User
from app.schemas.dtos import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación y Usuarios (FR-01)"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register_client(payload)


@router.post("/login", response_model=TokenResponse)
def login_json(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Endpoint JSON para iniciar sesión desde el frontend React."""
    service = AuthService(db)
    return service.authenticate_user(payload.email, payload.password)


@router.post("/token", response_model=TokenResponse)
def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Endpoint compatible con el botón 'Authorize' de Swagger UI."""
    service = AuthService(db)
    return service.authenticate_user(form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)