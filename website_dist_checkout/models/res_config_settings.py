from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dist_carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Carrier para 'Envío gestionado por el distribuidor'",
        config_parameter="website_dist_checkout.carrier_id",
        help="Método de envío que representa 'gestiona distribuidor'.",
    )
    dist_require_label = fields.Boolean(
        string="Exigir etiqueta para validar albarán",
        config_parameter="website_dist_checkout.require_label",
        help="Si está activo y el carrier es el de 'gestiona distribuidor', bloquea validar albarán si no hay etiqueta adjunta.",
    )