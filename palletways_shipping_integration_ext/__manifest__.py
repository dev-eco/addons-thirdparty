{
    'name': 'Palletways Shipping Integration Extension',
    'version': '17.0.1.0.0',
    'summary': 'Extensión y mejoras para la integración con Palletways',
    'category': 'Inventory/Delivery',
    'author': 'EcoCaucho',
    'website': 'https://www.ecocaucho.com',
    'license': 'LGPL-3',
    'depends': [
        'palletways_shipping_integration',
        'product_palletization',
        'website_dist_checkout',
        'portal',
    ],
    'data': [
        'views/res_company.xml',
        'views/delivery_carrier.xml',
        'views/portal.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
