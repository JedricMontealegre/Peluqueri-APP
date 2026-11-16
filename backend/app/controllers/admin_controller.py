from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.domain import User, UserRole
from app.schemas.dtos import (
    UserResponse,
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
)
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/admin", tags=["Administración de Horarios (FR-06)"])


@router.get("/peluqueros", response_model=List[UserResponse])
def list_hairdressers(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    return service.list_hairdressers()


@router.get("/horarios", response_model=List[ScheduleResponse])
def list_schedules(
    hairdresser_id: Optional[int] = Query(None),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    return service.list_all_schedules(hairdresser_id=hairdresser_id)


@router.post(
    "/horarios", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED
)
def create_schedule(
    payload: ScheduleCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    return service.create_schedule(payload)


@router.put("/horarios/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    return service.update_schedule(schedule_id, payload)


@router.delete("/horarios/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    service.delete_schedule(schedule_id)