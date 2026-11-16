from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models.domain import Base
from app.seed import run_seeders

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Crear tablas en PostgreSQL si no existen
    Base.metadata.create_all(bind=engine)
    # 2. Poblar datos iniciales (Servicios + Usuarios de prueba)
    db = SessionLocal()
    try:
        run_seeders(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Permitir peticiones desde el Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "Peluqueri-APP Backend"}