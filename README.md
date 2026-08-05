# Barrio Pizza AI

Dashboard interno para revisar ordenes de compra semanales de sucursales piloto de Barrio Pizza y generar alertas accionables sobre quiebres, sobre-pedidos y productos olvidados.

## Estado

Dashboard funcional con backend FastAPI, frontend React/Vite, CRUD de datos, alertas de compra, pedido corregido por proveedor, chat IA con Gemini y ajustes configurables.

## Correr local sin Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Variables principales del backend:

- `DATABASE_URL`: base SQLite local por defecto.
- `BACKEND_CORS_ORIGINS`: origen permitido del frontend, por defecto `http://localhost:5173`.
- `GEMINI_API_KEY`: key de Gemini, solo se usa desde el backend.
- `GEMINI_MODEL`: modelo activo de Gemini.
- `GEMINI_DAILY_LIMIT`: limite diario mostrado en Ajustes como contador local aproximado; la cuota real se revisa en Google AI Studio.

Frontend:

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

## Correr con Docker

```bash
docker compose up --build
```

## Decisiones iniciales

- Backend monolitico modular con FastAPI, pandas y SQLAlchemy.
- SQLite local para simplificar evaluacion y despliegue free tier.
- Frontend SPA con Vite, React, TypeScript, Tailwind, TanStack Query, Recharts y lucide-react.
- La API de Gemini se llamara solo desde el backend mediante `GEMINI_API_KEY`.
- No se implementa login en esta fase; para produccion se agregaria autenticacion real y control de roles.
- Las preferencias puramente visuales se guardan en `localStorage`; los datos de negocio viven en SQLite y se pueden restaurar desde los CSV originales.

## Odoo en produccion

La integracion con Odoo se haria sincronizando ingredientes contra productos de Odoo mediante API/XML-RPC. Las alertas funcionarian como validacion previa antes de confirmar una orden de compra: el usuario revisa el pedido corregido, aprueba ajustes y luego se actualiza o confirma la orden en Odoo. En produccion tambien se agregaria autenticacion, auditoria, secrets manager para la key de IA y limites de gasto.
