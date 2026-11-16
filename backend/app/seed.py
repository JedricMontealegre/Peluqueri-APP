from datetime import time
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.domain import User, UserRole, Service, Schedule

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_seeders(db: Session):
    # 1. Evitar duplicados si ya se ejecutó
    if db.query(User).first():
        return

    # 2. Usuarios de prueba (Requeridos en Sección 6 + Peluqueros)
    users = [
        User(
            full_name="Administrador Salón",
            email="admin@system.com",
            phone="3000000001",
            hashed_password=pwd_context.hash("Admin2026!"),
            role=UserRole.ADMIN
        ),
        User(
            full_name="Cliente Prueba",
            email="user@system.com",
            phone="3000000002",
            hashed_password=pwd_context.hash("User2026!"),
            role=UserRole.CLIENT
        ),
        User(
            full_name="Carlos Estilista",
            email="carlos@peluqueriapp.com",
            phone="3000000003",
            hashed_password=pwd_context.hash("Peluquero2026!"),
            role=UserRole.HAIRDRESSER
        ),
        User(
            full_name="Laura Colorista",
            email="laura@peluqueriapp.com",
            phone="3000000004",
            hashed_password=pwd_context.hash("Peluquero2026!"),
            role=UserRole.HAIRDRESSER
        ),
    ]
    db.add_all(users)
    db.commit()

    # 3. Catálogo de Servicios (FR-03)
    services = [
        Service(name="Corte de Cabello", description="Corte clásico o moderno con lavado", duration_minutes=30, price=25000),
        Service(name="Tinte Completo", description="Coloración profesional y tratamiento hidratante", duration_minutes=90, price=95000),
        Service(name="Tratamiento Capilar", description="Keratina y restauración profunda", duration_minutes=60, price=70000),
    ]
    db.add_all(services)
    db.commit()

    # 4. Horarios base para los peluqueros (Lunes a Sábado: 08:00 - 18:00)
    hairdressers = db.query(User).filter(User.role == UserRole.HAIRDRESSER).all()
    schedules = []
    for hd in hairdressers:
        for day in range(0, 6): # 0=Lunes a 5=Sábado
            schedules.append(
                Schedule(
                    hairdresser_id=hd.id,
                    day_of_week=day,
                    start_time=time(8, 0),
                    end_time=time(18, 0),
                    is_available=True
                )
            )
    db.add_all(schedules)
    db.commit()