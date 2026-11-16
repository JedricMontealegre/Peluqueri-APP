from datetime import date
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from app.models.domain import User, UserRole, Schedule, Appointment, Service, AppointmentStatus

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == record_id).first()

    def get_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def save(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.commit()


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.email == email.lower().strip())
            .first()
        )

    def list_active_hairdressers(self) -> List[User]:
        return (
            self.db.query(User)
            .filter(User.role == UserRole.HAIRDRESSER, User.is_active == True)
            .all()
        )


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, db: Session):
        super().__init__(Schedule, db)

    def list_schedules_with_hairdresser(self, hairdresser_id: Optional[int] = None):
        query = self.db.query(Schedule, User).join(
            User, Schedule.hairdresser_id == User.id
        )
        if hairdresser_id:
            query = query.filter(Schedule.hairdresser_id == hairdresser_id)
        return query.order_by(
            Schedule.hairdresser_id.asc(),
            Schedule.day_of_week.asc(),
            Schedule.start_time.asc(),
        ).all()

    def find_overlapping_schedule(
        self, hairdresser_id: int, day_of_week: int, start_time, end_time
    ) -> Optional[Schedule]:
        return (
            self.db.query(Schedule)
            .filter(
                Schedule.hairdresser_id == hairdresser_id,
                Schedule.day_of_week == day_of_week,
                Schedule.start_time < end_time,
                Schedule.end_time > start_time,
            )
            .first()
        )

    def get_appointments_by_hairdresser(
        self, hairdresser_id: int, target_date: Optional[date] = None
    ):
        query = (
            self.db.query(Appointment, Service, User)
            .join(Service, Appointment.service_id == Service.id)
            .outerjoin(User, Appointment.client_id == User.id)
            .filter(Appointment.hairdresser_id == hairdresser_id)
        )
        if target_date:
            query = query.filter(Appointment.appointment_date == target_date)

        return query.order_by(
            Appointment.appointment_date.asc(), Appointment.start_time.asc()
        ).all()
class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: Session):
        super().__init__(Service, db)

    def list_all_ordered(self) -> List[Service]:
        return self.db.query(Service).order_by(Service.id.asc()).all()


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: Session):
        super().__init__(Appointment, db)

    def get_active_schedules_for_day(
        self, hairdresser_id: int, day_of_week: int
    ) -> List[Schedule]:
        return (
            self.db.query(Schedule)
            .filter(
                Schedule.hairdresser_id == hairdresser_id,
                Schedule.day_of_week == day_of_week,
                Schedule.is_available == True,
            )
            .order_by(Schedule.start_time.asc())
            .all()
        )

    def get_active_appointments_for_date(
        self, hairdresser_id: int, target_date: date, lock_rows: bool = False
    ) -> List[Appointment]:
        query = self.db.query(Appointment).filter(
            Appointment.hairdresser_id == hairdresser_id,
            Appointment.appointment_date == target_date,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        if lock_rows:
            query = query.with_for_update()
        return query.order_by(Appointment.start_time.asc()).all()

    def get_cancelled_exact_slot(
        self, hairdresser_id: int, target_date: date, start_time
    ) -> Optional[Appointment]:
        """Recupera un registro cancelado en la misma franja para reutilizarlo sin violar uq_hairdresser_slot."""
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.hairdresser_id == hairdresser_id,
                Appointment.appointment_date == target_date,
                Appointment.start_time == start_time,
                Appointment.status == AppointmentStatus.CANCELLED,
            )
            .first()
        )

    def get_appointment_detail(self, appointment_id: int):
        return (
            self.db.query(Appointment, Service, User)
            .join(Service, Appointment.service_id == Service.id)
            .join(User, Appointment.hairdresser_id == User.id)
            .filter(Appointment.id == appointment_id)
            .first()
        )

    def list_client_appointments(self, client_id: int):
        return (
            self.db.query(Appointment, Service, User)
            .join(Service, Appointment.service_id == Service.id)
            .join(User, Appointment.hairdresser_id == User.id)
            .filter(Appointment.client_id == client_id)
            .order_by(
                Appointment.appointment_date.desc(), Appointment.start_time.desc()
            )
            .all()
        )