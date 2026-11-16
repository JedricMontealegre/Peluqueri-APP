import json
from datetime import date, time, datetime, timedelta
from typing import List, Optional
import redis
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.domain import User, UserRole, Appointment, AppointmentStatus
from app.repositories.base_repo import (
    UserRepository,
    ServiceRepository,
    AppointmentRepository,
)
from app.schemas.dtos import (
    TimeSlotResponse,
    AvailabilityResponse,
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
)


class BookingService:
    """Componentes ServicioDisponibilidad y ServicioReservas (FR-02, FR-04, FR-08, NFR-01, NFR-03)."""

    SLOT_STEP_MINUTES = 30
    CACHE_TTL_SECONDS = 300  # 5 minutos

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.service_repo = ServiceRepository(db)
        self.appt_repo = AppointmentRepository(db)
        self.redis = self._init_redis()

    def _init_redis(self) -> Optional[redis.Redis]:
        try:
            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def _cache_key(
        self, hairdresser_id: int, target_date: date, service_id: Optional[int]
    ) -> str:
        return f"availability:{hairdresser_id}:{target_date.isoformat()}:{service_id or 0}"

    def _invalidate_availability_cache(
        self, hairdresser_id: int, target_date: date
    ) -> None:
        if not self.redis:
            return
        try:
            pattern = f"availability:{hairdresser_id}:{target_date.isoformat()}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass

    @staticmethod
    def _add_minutes(base_time: time, minutes: int) -> time:
        dt = datetime.combine(date.today(), base_time) + timedelta(minutes=minutes)
        return dt.time()

    @staticmethod
    def _overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
        return start_a < end_b and end_a > start_b

    # =========================================================
    # MOTOR DE DISPONIBILIDAD CON CACHÉ REDIS (FR-04 / NFR-01)
    # =========================================================

    def get_available_slots(
        self,
        hairdresser_id: int,
        target_date: date,
        service_id: Optional[int] = None,
    ) -> AvailabilityResponse:
        hairdresser = self.user_repo.get_by_id(hairdresser_id)
        if not hairdresser or hairdresser.role != UserRole.HAIRDRESSER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peluquero no encontrado",
            )

        duration = self.SLOT_STEP_MINUTES
        if service_id is not None:
            service = self.service_repo.get_by_id(service_id)
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Servicio no encontrado",
                )
            duration = service.duration_minutes

        # 1. Consultar caché en Redis (NFR-01 < 1.5s)
        cache_key = self._cache_key(hairdresser_id, target_date, service_id)
        if self.redis:
            try:
                cached_raw = self.redis.get(cache_key)
                if cached_raw:
                    data = json.loads(cached_raw)
                    data["cached"] = True
                    return AvailabilityResponse(**data)
            except Exception:
                pass

        # 2. Calcular franjas libres desde PostgreSQL
        day_of_week = target_date.weekday()  # 0=Lunes ... 6=Domingo
        schedules = self.appt_repo.get_active_schedules_for_day(
            hairdresser_id, day_of_week
        )
        booked = self.appt_repo.get_active_appointments_for_date(
            hairdresser_id, target_date, lock_rows=False
        )

        slots: List[TimeSlotResponse] = []
        for sched in schedules:
            cursor = sched.start_time
            while True:
                slot_end = self._add_minutes(cursor, duration)
                # Evitar desbordamiento de medianoche o fuera del turno
                if slot_end <= cursor or slot_end > sched.end_time:
                    break

                has_conflict = any(
                    self._overlaps(cursor, slot_end, appt.start_time, appt.end_time)
                    for appt in booked
                )
                if not has_conflict:
                    slots.append(
                        TimeSlotResponse(
                            start_time=cursor, end_time=slot_end, available=True
                        )
                    )

                next_cursor = self._add_minutes(cursor, self.SLOT_STEP_MINUTES)
                if next_cursor <= cursor:
                    break
                cursor = next_cursor

        response = AvailabilityResponse(
            hairdresser_id=hairdresser.id,
            hairdresser_name=hairdresser.full_name,
            date=target_date,
            service_id=service_id,
            duration_minutes=duration,
            slots=slots,
            cached=False,
        )

        # 3. Guardar resultado en Redis
        if self.redis:
            try:
                self.redis.setex(
                    cache_key,
                    self.CACHE_TTL_SECONDS,
                    response.model_dump_json(),
                )
            except Exception:
                pass

        return response

    # =========================================================
    # CREACIÓN DE CITA CON BLOQUEO TRANSACCIONAL (FR-02 / NFR-03)
    # =========================================================

    def create_appointment(
        self,
        payload: AppointmentCreateRequest,
        current_user: Optional[User] = None,
    ) -> AppointmentResponse:
        # Validar datos del cliente (invitado vs autenticado)
        if current_user is None:
            if not payload.guest_name or not payload.guest_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Los usuarios invitados deben ingresar nombre y teléfono de contacto",
                )
            client_id = None
            guest_name = payload.guest_name.strip()
            guest_phone = payload.guest_phone.strip()
            guest_email = (
                payload.guest_email.strip().lower()
                if payload.guest_email
                else None
            )
        else:
            client_id = current_user.id
            guest_name = (
                payload.guest_name.strip()
                if payload.guest_name
                else current_user.full_name
            )
            guest_phone = (
                payload.guest_phone.strip()
                if payload.guest_phone
                else current_user.phone
            )
            guest_email = (
                payload.guest_email.strip().lower()
                if payload.guest_email
                else current_user.email
            )

        hairdresser = self.user_repo.get_by_id(payload.hairdresser_id)
        if not hairdresser or hairdresser.role != UserRole.HAIRDRESSER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peluquero no encontrado",
            )

        service = self.service_repo.get_by_id(payload.service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servicio no encontrado",
            )

        end_time = self._add_minutes(payload.start_time, service.duration_minutes)

        # Verificar que caiga dentro del horario laboral del peluquero
        day_of_week = payload.appointment_date.weekday()
        schedules = self.appt_repo.get_active_schedules_for_day(
            payload.hairdresser_id, day_of_week
        )
        within_schedule = any(
            sched.start_time <= payload.start_time and end_time <= sched.end_time
            for sched in schedules
        )
        if not within_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La franja seleccionada está fuera del horario laboral del peluquero",
            )

        try:
            # Bloqueo pesimista (SELECT ... FOR UPDATE) sobre citas de ese peluquero/fecha
            existing_appointments = self.appt_repo.get_active_appointments_for_date(
                payload.hairdresser_id,
                payload.appointment_date,
                lock_rows=True,
            )

            conflict = any(
                self._overlaps(
                    payload.start_time, end_time, appt.start_time, appt.end_time
                )
                for appt in existing_appointments
            )
            if conflict:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La franja horaria seleccionada ya no está disponible. Por favor elige otro horario.",
                )

            # Reutilizar fila si existía una cita cancelada en esa misma hora exacta
            cancelled_row = self.appt_repo.get_cancelled_exact_slot(
                payload.hairdresser_id,
                payload.appointment_date,
                payload.start_time,
            )
            if cancelled_row:
                cancelled_row.service_id = service.id
                cancelled_row.client_id = client_id
                cancelled_row.guest_name = guest_name
                cancelled_row.guest_phone = guest_phone
                cancelled_row.guest_email = guest_email
                cancelled_row.end_time = end_time
                cancelled_row.status = AppointmentStatus.CONFIRMED
                saved_appt = cancelled_row
            else:
                saved_appt = Appointment(
                    hairdresser_id=hairdresser.id,
                    service_id=service.id,
                    client_id=client_id,
                    guest_name=guest_name,
                    guest_phone=guest_phone,
                    guest_email=guest_email,
                    appointment_date=payload.appointment_date,
                    start_time=payload.start_time,
                    end_time=end_time,
                    status=AppointmentStatus.CONFIRMED,
                )
                self.db.add(saved_appt)

            self.db.commit()
            self.db.refresh(saved_appt)

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicto de concurrencia: otro usuario acaba de reservar este horario.",
            )

        # Invalidar caché de Redis para esa fecha/peluquero
        self._invalidate_availability_cache(
            payload.hairdresser_id, payload.appointment_date
        )

        return self._build_appointment_response(saved_appt, service, hairdresser)

    # =========================================================
    # CONSULTAR, CANCELAR Y REPROGRAMAR CITAS (FR-08)
    # =========================================================

    def list_my_appointments(self, current_user: User) -> List[AppointmentResponse]:
        rows = self.appt_repo.list_client_appointments(current_user.id)
        return [
            self._build_appointment_response(appt, service, hairdresser)
            for appt, service, hairdresser in rows
        ]

    def cancel_appointment(
        self,
        appointment_id: int,
        current_user: Optional[User] = None,
        guest_phone: Optional[str] = None,
    ) -> AppointmentResponse:
        detail = self.appt_repo.get_appointment_detail(appointment_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada",
            )

        appt, service, hairdresser = detail
        self._authorize_appointment_access(appt, current_user, guest_phone)

        if appt.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cita ya se encuentra cancelada",
            )

        appt.status = AppointmentStatus.CANCELLED
        self.db.commit()
        self.db.refresh(appt)

        self._invalidate_availability_cache(
            appt.hairdresser_id, appt.appointment_date
        )
        return self._build_appointment_response(appt, service, hairdresser)

    def reschedule_appointment(
        self,
        appointment_id: int,
        payload: AppointmentRescheduleRequest,
        current_user: Optional[User] = None,
    ) -> AppointmentResponse:
        detail = self.appt_repo.get_appointment_detail(appointment_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada",
            )

        appt, service, current_hairdresser = detail
        self._authorize_appointment_access(appt, current_user, payload.guest_phone)

        if appt.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede reprogramar una cita cancelada",
            )

        target_hairdresser_id = payload.hairdresser_id or appt.hairdresser_id
        target_hairdresser = self.user_repo.get_by_id(target_hairdresser_id)
        if not target_hairdresser or target_hairdresser.role != UserRole.HAIRDRESSER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peluquero destino no encontrado",
            )

        new_end_time = self._add_minutes(payload.start_time, service.duration_minutes)
        day_of_week = payload.appointment_date.weekday()
        schedules = self.appt_repo.get_active_schedules_for_day(
            target_hairdresser_id, day_of_week
        )
        within_schedule = any(
            sched.start_time <= payload.start_time and new_end_time <= sched.end_time
            for sched in schedules
        )
        if not within_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo horario está fuera del turno del peluquero",
            )

        old_hairdresser_id = appt.hairdresser_id
        old_date = appt.appointment_date

        try:
            existing = self.appt_repo.get_active_appointments_for_date(
                target_hairdresser_id, payload.appointment_date, lock_rows=True
            )
            conflict = any(
                other.id != appt.id
                and self._overlaps(
                    payload.start_time, new_end_time, other.start_time, other.end_time
                )
                for other in existing
            )
            if conflict:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La nueva franja horaria ya está ocupada",
                )

            appt.hairdresser_id = target_hairdresser_id
            appt.appointment_date = payload.appointment_date
            appt.start_time = payload.start_time
            appt.end_time = new_end_time

            self.db.commit()
            self.db.refresh(appt)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La nueva franja horaria fue reservada por otro usuario",
            )

        self._invalidate_availability_cache(old_hairdresser_id, old_date)
        self._invalidate_availability_cache(
            target_hairdresser_id, payload.appointment_date
        )

        return self._build_appointment_response(appt, service, target_hairdresser)

    def _authorize_appointment_access(
        self,
        appt: Appointment,
        current_user: Optional[User],
        guest_phone: Optional[str],
    ) -> None:
        if current_user:
            if current_user.role == UserRole.ADMIN:
                return
            if appt.client_id == current_user.id:
                return
        if guest_phone and appt.guest_phone and guest_phone.strip() == appt.guest_phone.strip():
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta cita (inicia sesión o verifica el teléfono registrado)",
        )

    @staticmethod
    def _build_appointment_response(
        appt: Appointment, service, hairdresser: User
    ) -> AppointmentResponse:
        return AppointmentResponse(
            id=appt.id,
            hairdresser_id=appt.hairdresser_id,
            hairdresser_name=hairdresser.full_name,
            service_id=appt.service_id,
            service_name=service.name,
            service_price=service.price,
            duration_minutes=service.duration_minutes,
            client_id=appt.client_id,
            client_name=appt.guest_name or "Cliente Registrado",
            client_phone=appt.guest_phone,
            guest_email=appt.guest_email,
            appointment_date=appt.appointment_date,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=appt.status,
        )