from typing import List
from sqlalchemy.orm import Session

from app.repositories.base_repo import ServiceRepository, UserRepository
from app.schemas.dtos import ServiceResponse, HairdresserPublicResponse


class CatalogService:
    """Componente CatálogoServicios: consulta de servicios y estilistas activos (FR-03)."""

    def __init__(self, db: Session):
        self.service_repo = ServiceRepository(db)
        self.user_repo = UserRepository(db)

    def list_services(self) -> List[ServiceResponse]:
        services = self.service_repo.list_all_ordered()
        return [ServiceResponse.model_validate(s) for s in services]

    def list_available_hairdressers(self) -> List[HairdresserPublicResponse]:
        hairdressers = self.user_repo.list_active_hairdressers()
        return [
            HairdresserPublicResponse.model_validate(hd) for hd in hairdressers
        ]