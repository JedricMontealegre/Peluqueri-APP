from datetime import date, time
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.domain import UserRole, AppointmentStatus


# =========================================================
# DTOs DE AUTENTICACIÓN Y USUARIOS (FR-01 / NFR-04)
# =========================================================

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6, max_length=72)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =========================================================
# DTOs DE AGENDA DEL PELUQUERO (FR-05 / US-02)
# =========================================================

class HairdresserAppointmentResponse(BaseModel):
    id: int
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    service_name: str
    duration_minutes: int
    client_name: str
    client_phone: Optional[str]
    is_guest: bool


# =========================================================
# DTOs DE GESTIÓN DE HORARIOS ADMIN (FR-06)
# =========================================================

class ScheduleCreateRequest(BaseModel):
    hairdresser_id: int
    day_of_week: int = Field(..., ge=0, le=6, description="0=Lunes ... 6=Domingo")
    start_time: time
    end_time: time
    is_available: bool = True


class ScheduleUpdateRequest(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: int
    hairdresser_id: int
    hairdresser_name: str
    day_of_week: int
    start_time: time
    end_time: time
    is_available: bool


# =========================================================
# ESPACIO PARA DTOs DE CATÁLOGO Y RESERVAS (Daniel Arias)
# =========================================================