from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.domain import User, UserRole
from app.schemas.dtos import HairdresserAppointmentResponse
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/peluqueros", tags=["Agenda de Peluqueros (FR-05)"])


@router.get("/mis-citas", response_model=List[HairdresserAppointmentResponse])
def get_my_appointments(
    fecha: Optional[date] = Query(
        None, description="Filtrar por fecha (YYYY-MM-DD). Si se omite, lista todas."
    ),
    current_user: User = Depends(require_roles([UserRole.HAIRDRESSER, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    return service.get_hairdresser_agenda(
        hairdresser_id=current_user.id, target_date=fecha
    )