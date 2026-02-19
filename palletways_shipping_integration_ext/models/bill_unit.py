# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class BillUnit(models.Model):
    _name = 'bill.unit'
    _description = 'Unidad de facturación para Palletways'

    name = fields.Char(string='Nombre', required=True)
    bill_unit_key = fields.Char(string='Clave API', required=True,
                               help='Clave utilizada en la API de Palletways')
    description = fields.Text(string='Descripción')
    active = fields.Boolean(default=True)

    # Dimensiones y peso máximo
    max_weight = fields.Float(string='Peso máximo (kg)')
    max_height = fields.Float(string='Altura máxima (cm)')
    max_width = fields.Float(string='Anchura máxima (cm)')
    max_length = fields.Float(string='Longitud máxima (cm)')

    # Relación con transportistas
    carrier_ids = fields.Many2many(
        'delivery.carrier',
        relation='bill_unit_carrier_rel',
        column1='bill_unit_id',
        column2='carrier_id',
        string='Transportistas',
        help='Transportistas que utilizan esta unidad de facturación'
    )
    # Relación calculada con pedidos, sin almacenamiento en BD
    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Pedidos relacionados',
        compute='_compute_sale_orders',
        store=False,
        compute_sudo=True,
        relation=None,  # Importante: sin tabla de relación
    )

    def _compute_sale_orders(self):
        """Calcula los pedidos relacionados con esta unidad de facturación"""
        SaleOrder = self.env['sale.order']
        for record in self:
            if record.carrier_ids:
                record.sale_order_ids = SaleOrder.search([
                    ('carrier_id', 'in', record.carrier_ids.ids),
                    ('state', 'not in', ['cancel', 'draft'])
                ])
            else:
                record.sale_order_ids = SaleOrder.browse()

    _sql_constraints = [
        ('bill_unit_key_uniq', 'unique(bill_unit_key)', 'La clave de unidad de facturación debe ser única')
    ]
