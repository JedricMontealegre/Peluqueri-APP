from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.domain import User, UserRole
from app.repositories.base_repo import UserRepository
from app.schemas.dtos import UserRegisterRequest, UserResponse, TokenResponse


class AuthService:
    """Componente ServicioUsuarios: registro, autenticación y cifrado BCrypt."""

    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_client(self, payload: UserRegisterRequest) -> UserResponse:
        normalized_email = payload.email.lower().strip()
        if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de correo electrónico inválido",
            )

        if self.user_repo.get_by_email(normalized_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta registrada con este correo electrónico",
            )

        new_user = User(
            full_name=payload.full_name.strip(),
            email=normalized_email,
            phone=payload.phone.strip() if payload.phone else None,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.CLIENT,
            is_active=True,
        )
        created = self.user_repo.save(new_user)
        return UserResponse.model_validate(created)

    def authenticate_user(self, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo electrónico o contraseña incorrectos",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta de usuario se encuentra inactiva",
            )

        token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )