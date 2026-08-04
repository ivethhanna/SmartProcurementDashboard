# Integracion con Odoo

En produccion, Barrio Pizza podria conectar esta herramienta a Odoo como una capa de validacion previa para compras.

1. Sincronizar ingredientes con productos de Odoo.
2. Leer ordenes de compra borrador desde Odoo.
3. Ejecutar proyecciones, conversiones y alertas.
4. Enviar el pedido corregido a Odoo para aprobacion o actualizacion.

Cambios necesarios para produccion:

- Autenticacion y roles.
- Manejo de secretos con un secrets manager.
- Auditoria de cambios.
- Limites de gasto para IA.
- CORS restringido al dominio desplegado.

