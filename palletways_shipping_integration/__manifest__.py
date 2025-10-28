# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{

    # App information
    'name': 'Palletways Shipping Integration',
    'category': 'Website',
    'version': '17.0.1.0',
    'summary': """At 𝗩𝗿𝗮𝗷𝗮 𝗧𝗲𝗰𝗵𝗻𝗼𝗹𝗼𝗴𝗶𝗲𝘀, we continue to innovate as a globally renowned 𝘀𝗵𝗶𝗽𝗽𝗶𝗻𝗴 𝗶𝗻𝘁𝗲𝗴𝗿𝗮𝘁𝗼𝗿 𝗮𝗻𝗱 𝗢𝗱𝗼𝗼 𝗰𝘂𝘀𝘁𝗼𝗺𝗶𝘇𝗮𝘁𝗶𝗼𝗻 𝗲𝘅𝗽𝗲𝗿𝘁. Our widely accepted shipping connections are made to easily interface with Odoo, simplifying everything from creating labels to tracking shipments—all from a single dashboard. We’re excited to introduce Palletways Odoo Connectors your one stop solution for seamless global shipping management, now available on the Odoo App Store! At Vraja Technologies, we continue to be at the forefront of Odoo shipping integrations, ensuring your logistics run smoothly across countries. Users also search using these keywords Vraja Odoo Shipping Integration, Vraja Odoo shipping Connector, Vraja Shipping Integration, Vraja shipping Connector, Palletways Odoo Shipping Integration, Palletways Odoo shipping Connector, Palletways Shipping Integration, Palletways shipping Connector, Palletways vraja technologies, Odoo Palletways.""",
    'license': 'OPL-1',

    # Dependencies
    'depends': ['delivery','stock','stock_delivery'],

    # Views
     'data': [
        'security/ir.model.access.csv',
        'data/bill_unit.xml',
        'views/res_company.xml',
        'views/sale_order.xml',
        'views/delivery_carrier.xml',
        'views/stock_picking.xml'],

    # Odoo Store Specific
    'images': ['static/description/cover.gif'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'http://www.vrajatechnologies.com/contactus',
    'price': '321',
    'currency': 'EUR',

}


