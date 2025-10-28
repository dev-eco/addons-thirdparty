# -*- coding: utf-8 -*-
{
    'name': 'Palletways Shipping Integration - Ext',
    'version': '17.0.1.0',
    'summary': 'Bill Units por peso, Depot/Account y tracking portal (website_dist_checkout)',
    'category': 'Inventory/Shipping',
    'license': 'LGPL-3',
    'depends': [
        'palletways_shipping_integration',  # módulo de terceros
        'sale',
        'stock',
        'website',
        'website_dist_checkout',  # tu módulo de portal
    ],
    'data': [
        'views/res_company.xml',
        'views/delivery_carrier.xml',
        'views/portal.xml',
    ],
    'installable': True,
}
