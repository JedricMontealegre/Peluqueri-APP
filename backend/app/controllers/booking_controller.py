from typing import List, Optional
from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.domain import User
from app.schemas.dtos import (
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
    AppointmentResponse,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/reservas", tags=["Gestión de Reservas (FR-02, FR-08)"])


@router.post(
    "", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED
)
def create_booking(
    payload: AppointmentCreateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Permite reservar una cita tanto a usuarios invitados como autenticados."""
    service = BookingService(db)
    return service.create_appointment(payload=payload, current_user=current_user)


@router.get("/mis-reservas", response_model=List[AppointmentResponse])
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista el historial de citas de un cliente autenticado."""
    service = BookingService(db)
    return service.list_my_appointments(current_user)


@router.patch("/{appointment_id}/cancelar", response_model=AppointmentResponse)
def cancel_booking(
    appointment_id: int,
    payload: Optional[AppointmentCancelRequest] = Body(default=None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Cancela una cita existente y libera la franja horaria."""
    service = BookingService(db)
    guest_phone = payload.guest_phone if payload else None
    return service.cancel_appointment(
        appointment_id=appointment_id,
        current_user=current_user,
        guest_phone=guest_phone,
    )


@router.put("/{appointment_id}/reprogramar", response_model=AppointmentResponse)
def reschedule_booking(
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Reprograma la fecha, hora o estilista de una cita existente."""
    service = BookingService(db)
    return service.reschedule_appointment(
        appointment_id=appointment_id,
        payload=payload,
        current_user=current_user,
    )