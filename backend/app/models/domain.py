import enum
from sqlalchemy import (
    Column, Integer, String, Float, Date, Time, 
    ForeignKey, Enum, UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship, declarative_base

# Declaración obligatoria de Base para que FastAPI/SQLAlchemy reconozca los modelos
Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    HAIRDRESSER = "HAIRDRESSER"
    CLIENT = "CLIENT"

class AppointmentStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    is_active = Column(Boolean, default=True)

    schedules = relationship("Schedule", back_populates="hairdresser")
    hairdresser_appointments = relationship(
        "Appointment", foreign_keys="Appointment.hairdresser_id", back_populates="hairdresser"
    )

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    price = Column(Float, nullable=False)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    hairdresser_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)

    hairdresser = relationship("User", back_populates="schedules")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    hairdresser_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_name = Column(String(100), nullable=True)
    guest_phone = Column(String(20), nullable=True)
    guest_email = Column(String(120), nullable=True)

    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.CONFIRMED, nullable=False)

    hairdresser = relationship("User", foreign_keys=[hairdresser_id], back_populates="hairdresser_appointments")
    service = relationship("Service")

    __table_args__ = (
        UniqueConstraint("hairdresser_id", "appointment_date", "start_time", name="uq_hairdresser_slot"),
    )