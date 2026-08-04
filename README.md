# Barrio Pizza AI

Dashboard interno para revisar ordenes de compra semanales de sucursales piloto de Barrio Pizza y generar alertas accionables sobre quiebres, sobre-pedidos y productos olvidados.

## Estado

Paso 1 implementado: estructura base del monorepo, configuracion local, Docker, backend FastAPI minimo y frontend Vite/React minimo.

## Correr local sin Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Correr con Docker

```bash
docker compose up --build
```

## Decisiones iniciales

- Backend monolitico modular con FastAPI, pandas y SQLAlchemy.
- SQLite local para simplificar evaluacion y despliegue free tier.
- Frontend SPA con Vite, React, TypeScript, Tailwind y shadcn/ui.
- La API de Anthropic se llamara solo desde el backend mediante `ANTHROPIC_API_KEY`.
- No se implementa login en esta fase; para produccion se agregaria autenticacion real y control de roles.

## Odoo en produccion

La integracion con Odoo se haria sincronizando ingredientes contra productos de Odoo mediante API/XML-RPC. Las alertas funcionarian como validacion previa antes de confirmar una orden de compra: el usuario revisa el pedido corregido, aprueba ajustes y luego se actualiza o confirma la orden en Odoo. En produccion tambien se agregaria autenticacion, auditoria, secrets manager para la key de IA y limites de gasto.

