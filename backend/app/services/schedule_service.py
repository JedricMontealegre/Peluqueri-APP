from datetime import date
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.domain import UserRole, Schedule
from app.repositories.base_repo import UserRepository, ScheduleRepository
from app.schemas.dtos import (
    UserResponse,
    HairdresserAppointmentResponse,
    ScheduleCreateRequest,
    ScheduleUpdateRequest,
    ScheduleResponse,
)


class ScheduleService:
    """Componente ServicioHorarios: agenda de peluqueros (FR-05) y turnos (FR-06)."""

    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.schedule_repo = ScheduleRepository(db)

    def get_hairdresser_agenda(
        self, hairdresser_id: int, target_date: Optional[date] = None
    ) -> List[HairdresserAppointmentResponse]:
        rows = self.schedule_repo.get_appointments_by_hairdresser(
            hairdresser_id, target_date
        )
        agenda: List[HairdresserAppointmentResponse] = []
        for appt, service, client_user in rows:
            is_guest = client_user is None
            client_name = (
                client_user.full_name
                if client_user
                else (appt.guest_name or "Cliente Invitado")
            )
            client_phone = client_user.phone if client_user else appt.guest_phone

            agenda.append(
                HairdresserAppointmentResponse(
                    id=appt.id,
                    appointment_date=appt.appointment_date,
                    start_time=appt.start_time,
                    end_time=appt.end_time,
                    status=appt.status,
                    service_name=service.name,
                    duration_minutes=service.duration_minutes,
                    client_name=client_name,
                    client_phone=client_phone,
                    is_guest=is_guest,
                )
            )
        return agenda

    def list_hairdressers(self) -> List[UserResponse]:
        return [
            UserResponse.model_validate(hd)
            for hd in self.user_repo.list_active_hairdressers()
        ]

    def list_all_schedules(
        self, hairdresser_id: Optional[int] = None
    ) -> List[ScheduleResponse]:
        rows = self.schedule_repo.list_schedules_with_hairdresser(hairdresser_id)
        return [
            ScheduleResponse(
                id=sched.id,
                hairdresser_id=sched.hairdresser_id,
                hairdresser_name=hd.full_name,
                day_of_week=sched.day_of_week,
                start_time=sched.start_time,
                end_time=sched.end_time,
                is_available=sched.is_available,
            )
            for sched, hd in rows
        ]

    def create_schedule(self, payload: ScheduleCreateRequest) -> ScheduleResponse:
        if payload.start_time >= payload.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La hora de inicio debe ser anterior a la hora de finalización",
            )

        hairdresser = self.user_repo.get_by_id(payload.hairdresser_id)
        if not hairdresser or hairdresser.role != UserRole.HAIRDRESSER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El peluquero indicado no existe",
            )

        overlap = self.schedule_repo.find_overlapping_schedule(
            hairdresser_id=payload.hairdresser_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El peluquero ya tiene un turno asignado que se cruza con esa franja",
            )

        new_schedule = Schedule(
            hairdresser_id=payload.hairdresser_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_available=payload.is_available,
        )
        created = self.schedule_repo.save(new_schedule)
        return ScheduleResponse(
            id=created.id,
            hairdresser_id=created.hairdresser_id,
            hairdresser_name=hairdresser.full_name,
            day_of_week=created.day_of_week,
            start_time=created.start_time,
            end_time=created.end_time,
            is_available=created.is_available,
        )

    def update_schedule(
        self, schedule_id: int, payload: ScheduleUpdateRequest
    ) -> ScheduleResponse:
        sched = self.schedule_repo.get_by_id(schedule_id)
        if not sched:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horario no encontrado",
            )

        if payload.start_time is not None:
            sched.start_time = payload.start_time
        if payload.end_time is not None:
            sched.end_time = payload.end_time
        if payload.is_available is not None:
            sched.is_available = payload.is_available

        if sched.start_time >= sched.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La hora de inicio debe ser anterior a la hora de finalización",
            )

        updated = self.schedule_repo.save(sched)
        hairdresser = self.user_repo.get_by_id(updated.hairdresser_id)
        return ScheduleResponse(
            id=updated.id,
            hairdresser_id=updated.hairdresser_id,
            hairdresser_name=hairdresser.full_name if hairdresser else "Peluquero",
            day_of_week=updated.day_of_week,
            start_time=updated.start_time,
            end_time=updated.end_time,
            is_available=updated.is_available,
        )

    def delete_schedule(self, schedule_id: int) -> None:
        sched = self.schedule_repo.get_by_id(schedule_id)
        if not sched:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Horario no encontrado",
            )
        self.schedule_repo.delete(sched)