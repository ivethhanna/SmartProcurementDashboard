# Arquitectura

La aplicacion se divide en un backend FastAPI monolitico por dominios y un frontend React SPA.

- `backend/app/api`: routers HTTP.
- `backend/app/models`: modelos SQLAlchemy.
- `backend/app/database`: conexion, sesiones y seed.
- `backend/app/services`: logica de negocio por dominio.
- `frontend/src/pages`: pantallas principales.
- `frontend/src/components`: componentes reutilizables.

