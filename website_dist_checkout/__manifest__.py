{
    "name": "Website Distributor Checkout",
    "description": "Portal B2B para envíos gestionados por el distribuidor (datos, adjuntos y bloqueo opcional).",
    "version": "17.0.1.0.0",
    "author": "ECOCAUCHO SL",
    "website": "https://ecocaucho.org",
    "license": "LGPL-3",
    "category": "Website/Website",
    "depends": [
	"base_setup",
        "sale_management",
        "website_sale",
        "delivery",
        "portal",
        "stock",
        "mail",
    ],
    "data": [
        "views/res_config_settings_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking_view.xml",
        "views/portal_templates.xml",
	"views/portal_dist_orders.xml",
	"views/portal_home_tile.xml",
        "data/sample_carrier.xml",
    ],
    "demo": [
        "demo/demo_data.xml"
    ],
    "assets": {
    	"web.assets_frontend": [
             "website_dist_checkout/static/src/js/portal_button.js",
             # estilo de tiles
             "website_dist_checkout/static/src/scss/portal_tiles.scss",
    	],
    },
    "installable": True,
    "application": False,
}
