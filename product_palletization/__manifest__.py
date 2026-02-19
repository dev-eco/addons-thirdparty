{
    'name': 'Product Palletization',
    'version': '17.0.1.0.0',
    'summary': 'Gestión de paletización de productos',
    'category': 'Inventory/Delivery',
    'author': 'EcoCaucho',
    'website': 'https://www.ecocaucho.com',
    'license': 'LGPL-3',
    'depends': ['product'],
    'data': [
        'views/product_template.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'sequence': 10,  # Carga temprana
}
