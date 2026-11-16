from datetime import date
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from app.models.domain import User, UserRole, Schedule, Appointment, Service

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