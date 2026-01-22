# -*- coding: utf-8 -*-
{
    'name': 'Palletways Shipping Integration',
    'version': '17.0.2.1.0',
    'category': 'Inventory/Delivery',
    'summary': 'Integración completa con API oficial de Palletways para envíos',
    'description': '''
    Integración completa con la API oficial de Palletways:

    🚚 Funcionalidades Principales:
    • Creación automática de envíos vía API oficial
    • Seguimiento en tiempo real de estados
    • Descarga de etiquetas PDF
    • Comprobantes de entrega (POD)
    • Gestión de servicios Palletways
    • Rate limiting automático (100 llamadas/min)

    📦 Optimizado para EcoCaucho:
    • Productos pesados y pallets
    • Citas previas automáticas
    • Trampillas elevadoras inteligentes
    • Multi-empresa support
    • Lógica inteligente de unidades facturables

    🔧 Características Técnicas:
    • Compatible con configuraciones existentes
    • Modo test/producción
    • Logging completo para debugging
    • Manejo robusto de errores
    • Actualización automática de estados
    • Migración desde versiones anteriores

    📋 Endpoints API Soportados:
    • createConsignment - Crear envíos
    • getConsignment - Detalles de envío
    • conStatusByTrackingId - Estado del envío
    • getLabelsByTID - Descargar etiquetas
    • getPodByTrackingId - Comprobante entrega
    • availableServices - Servicios disponibles
    • getNotes - Notas del envío
    
    ✅ Correcciones v2.1.0:
    • Endpoint API corregido a https://api.palletways.com/
    • Half Pallet corregido a 600kg (España)
    • Estructura Manifest según documentación oficial
    • Parámetros createConsignment en query string
    • Códigos de servicio actualizados
    • Tipos de pallet con límites correctos
    ''',
    'author': 'EcoCaucho Tech Team',
    'website': 'https://www.ecocaucho.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'delivery',
        'sale_stock',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        # Seguridad
        'security/ir.model.access.csv',

        # Datos básicos
        'data/bill_unit.xml',
        'data/palletways_pallet_types.xml',

        # Vistas principales
        'views/palletways_api_client_views.xml',
        'views/delivery_carrier_views.xml',
        'views/stock_picking_views.xml',
        'views/palletways_shipment_views.xml',

        # Vistas existentes actualizadas
        'views/res_company.xml',
        'views/sale_order.xml',

        # Menús
        'views/menu_views.xml',

        # Cron (opcional)
        'data/cron_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
