# Peluqueri-APP

Peluqueri-APP es una solución de software monolítica por capas integrada con PostgreSQL, Redis y Docker, orientada al agendamiento inteligente de citas, catálogo de servicios y gestión eficiente de agendas para establecimientos de belleza y cuidado personal.

## Requisitos previos

* **Docker Desktop** (o Docker Engine con Docker Compose) activo en el sistema.
* **Git** para clonar el repositorio.

---

## Cómo arrancar el prototipo

1. **Clonar el repositorio y entrar a la carpeta del proyecto:**
   ```bash
   git clone [https://github.com/JedricMontealegre/Peluqueri-APP.git](https://github.com/JedricMontealegre/Peluqueri-APP.git)
   cd Peluqueri-APP
   ```

2. **Levantar todos los servicios con Docker Compose:**
   ```bash
   docker compose up --build
   ```
   > El sistema orquesta automáticamente 4 contenedores (`db`, `redis`, `backend` y `frontend`) mediante *healthchecks* cada 5 segundos. Al iniciar, el backend crea las tablas en PostgreSQL y precarga datos de prueba (usuarios, servicios y horarios).

3. **Acceder a la aplicación en el navegador:**
   * **Interfaz Web (React):** http://localhost:3000
   * **Documentación interactiva API (Swagger UI):** http://localhost:8000/docs

---

## Credenciales de prueba precargadas

El sistema incluye datos iniciales (*seeders*) listos para probar cada rol de navegación:

| Rol | Correo electrónico | Contraseña | Funcionalidad principal |
| :--- | :--- | :--- | :--- |
| **Invitado** | *(No requiere cuenta)* | — | Agendar cita en 4 pasos con nombre y teléfono |
| **Cliente** | `user@system.com` | `User2026!` | Agendar citas y consultar historial (`Mis reservas`) |
| **Peluquero** | `carlos@peluqueriapp.com` | `Peluquero2026!` | Filtrar y consultar citas asignadas por fecha (`Mi agenda`) |
| **Administrador** | `admin@system.com` | `Admin2026!` | Crear/eliminar horarios por peluquero y cancelar citas (`Administración`) |

---

## Comandos útiles

* **Detener los contenedores conservando los datos:**
  ```bash
  docker compose down
  ```
* **Reiniciar desde cero (borrando el volumen `postgres_data` y recargando los datos de prueba):**
  ```bash
  docker compose down -v
  docker compose up --build
  ```

---

## Estructura del repositorio

```text
Peluqueri-APP/
├── backend/              # API REST en FastAPI (Python 3.11) + SQLAlchemy + Redis
├── frontend/             # Interfaz web en React 19 + Vite (Node 20)
├── docker-compose.yml    # Orquestación de contenedores, redes y volúmenes
└── README.md             # Guía de despliegue y uso del prototipo
```

---

## Equipo de desarrollo — Universidad Nacional de Colombia

* Jedric Julian Montealegre Contreras
* Camilo Andres Piñeros Ayala
* Daniel Mauricio Sanchez Tique
* Luis Eduardo Chaguezac
* Daniel Camilo Arias Martinez
