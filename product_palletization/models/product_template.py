# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Opcionales: por si quieres forzar paletización por unidades (no usado en el cálculo por peso)
    units_full_pallet = fields.Integer(string="Unidades por palet (Full)", help="Opcional, informativo")
    units_light_pallet = fields.Integer(string="Unidades por palet (Light)", help="Opcional, informativo")
    units_half_pallet = fields.Integer(string="Unidades por palet (Half)", help="Opcional, informativo")
    units_extra_light_pallet = fields.Integer(string="Unidades por palet (Extra)", help="Opcional, informativo")
    units_quarter_pallet = fields.Integer(string="Unidades por palet (Quarter)", help="Opcional, informativo")
    units_mini_quarter_pallet = fields.Integer(string="Unidades por palet (Mini Quarter Pallet)", help="Opcional, informativo")