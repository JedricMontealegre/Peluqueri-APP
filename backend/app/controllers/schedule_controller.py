from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dtos import (
    ServiceResponse,
    HairdresserPublicResponse,
    AvailabilityResponse,
)
from app.services.catalog_service import CatalogService
from app.services.booking_service import BookingService

router = APIRouter(tags=["Catálogo y Disponibilidad (FR-03, FR-04)"])


@router.get("/servicios", response_model=List[ServiceResponse])
def get_services_catalog(db: Session = Depends(get_db)):
    """Lista los servicios disponibles (corte, tinte, tratamiento) con duración y tarifa."""
    service = CatalogService(db)
    return service.list_services()


@router.get("/peluqueros/disponibles", response_model=List[HairdresserPublicResponse])
def get_public_hairdressers(db: Session = Depends(get_db)):
    """Lista los peluqueros activos para que el cliente elija estilista al agendar."""
    service = CatalogService(db)
    return service.list_available_hairdressers()


@router.get("/disponibilidad", response_model=AvailabilityResponse)
def get_availability(
    peluquero_id: int = Query(..., description="ID del peluquero"),
    fecha: date = Query(..., description="Fecha a consultar (YYYY-MM-DD)"),
    servicio_id: Optional[int] = Query(
        None, description="ID del servicio para calcular duración exacta"
    ),
    db: Session = Depends(get_db),
):
    """Consulta las franjas horarias libres (con soporte de caché en Redis)."""
    service = BookingService(db)
    return service.get_available_slots(
        hairdresser_id=peluquero_id, target_date=fecha, service_id=servicio_id
    )