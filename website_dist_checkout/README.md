# Website Distributor Checkout (Odoo 17)
Portal B2B para que el distribuidor gestione su envío:
- Seleccionar el método “Envío gestionado por el distribuidor”
- Rellenar datos de recogida (transportista, cuenta, fecha/franja)
- Subir etiqueta (PDF/ZPL) y albarán propio (PDF)
- Copia automática al albarán
- Bloqueo de validación si falta etiqueta (opcional)

## Requisitos
- Odoo 17
- Módulos: sale_management, website_sale, delivery, portal, stock, mail

## Instalación
1. Copia `website_dist_checkout` en tu ruta de addons (por ejemplo `addons/custom/website_dist_checkout`).
2. Añade la ruta a `addons_path` y reinicia Odoo.
3. Apps > Actualizar lista > Instalar “Website Distributor Checkout”.

## Configuración
Ajustes > General > Portal Distribuidores:
- Carrier “Envío gestionado por el distribuidor”
- Exigir etiqueta para validar albarán (opcional)

Se incluye un carrier de ejemplo y parámetros por defecto en `data/sample_carrier.xml`.

## Uso
1. El distribuidor hace pedido en el portal y selecciona el carrier “gestiona distribuidor”.
2. En el portal del pedido, botón “Envío del distribuidor”:
   - Rellena transportista, cuenta, fecha/franja.
   - Sube etiqueta y su albarán propio.
3. Al confirmar el pedido, Odoo copia datos y adjuntos al albarán.
4. Si está activado el bloqueo, sin etiqueta no se puede validar.

## Tests
Ejecuta: