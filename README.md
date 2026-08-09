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
- `ALLOWED_ORIGINS`: origen permitido del frontend, por defecto `http://localhost:5173`. Acepta varios origenes separados por coma.
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

Variable principal del frontend:

- `VITE_API_BASE_URL`: URL base del backend, por ejemplo `http://localhost:8000` en desarrollo local.

## Correr con Docker

```bash
docker compose up --build
```

## Tests

Desde la raiz del repo, en Windows:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_data_api.py backend\tests\test_recommendations_api.py -q
```

Para correr solo los tests de datos:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_data_api.py -q
```

Si pytest muestra un warning de cache en `.pytest_cache`, los tests igual son validos si terminan en `passed`. Para ocultar ese warning:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_data_api.py -q -p no:cacheprovider
```

## Deploy

Backend en Render:

- Root Directory: `backend`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- `GEMINI_API_KEY`: API key de Google AI Studio para el chat de IA.
- `ALLOWED_ORIGINS`: dominio publico del frontend en Vercel. Si hay mas de uno, separarlos por coma.

Frontend en Vercel:

- Root Directory: `frontend`
- `VITE_API_BASE_URL`: URL publica del backend en Render, por ejemplo `https://barrio-pizza-api.onrender.com`.

### Limitacion conocida: SQLite en Render free tier

El proyecto usa SQLite para simplificar el despliegue del reto. En el free tier de Render el disco del servicio es efimero: si el archivo SQLite se pierde al dormir o reiniciar el servicio, el backend vuelve a crear la base y la siembra desde `backend/sample_data/`. Por eso las ediciones manuales del CRUD en produccion pueden no persistir entre sesiones largas.

Al iniciar, los logs del backend indican si la base estaba vacia y se sembro desde `sample_data/`, o si ya tenia datos y no se resembro.

## Captura manual de datos

La captura manual actualiza registros existentes cuando la clave de negocio ya existe, en vez de fallar con un error de SQLite:

- Inventario: sucursal + ingrediente.
- Ordenes: sucursal + ingrediente.
- Consumo: sucursal + ingrediente + semana.
- Ingredientes: ID de ingrediente.

La respuesta del backend indica `status: "created"` o `status: "updated"`, y el frontend muestra el mensaje correspondiente. Esto mantiene vivas las alertas y la orden agrupada por proveedor despues de cambios manuales, incluyendo cambios de proveedor de un ingrediente existente.

## Decisiones iniciales

- Backend monolitico modular con FastAPI, pandas y SQLAlchemy.
- SQLite local para simplificar evaluacion y despliegue free tier.
- Frontend SPA con Vite, React, TypeScript, Tailwind, TanStack Query, Recharts y lucide-react.
- La API de Gemini se llamara solo desde el backend mediante `GEMINI_API_KEY`.
- No se implementa login en esta fase; para produccion se agregaria autenticacion real y control de roles.
- Las preferencias puramente visuales se guardan en `localStorage`; los datos de negocio viven en SQLite y se pueden restaurar desde los CSV originales.

## Odoo en produccion

La integracion con Odoo se haria sincronizando ingredientes contra productos de Odoo mediante API/XML-RPC. Las alertas funcionarian como validacion previa antes de confirmar una orden de compra: el usuario revisa el pedido corregido, aprueba ajustes y luego se actualiza o confirma la orden en Odoo. En produccion tambien se agregaria autenticacion, auditoria, secrets manager para la key de IA y limites de gasto.
