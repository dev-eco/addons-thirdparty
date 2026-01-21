from odoo import fields, models, _, api


class BillUnit(models.Model):
    _name = 'bill.unit'
    _rec_name = 'bill_unit_value'
    _description = 'Unidad de facturación para Palletways'

    name = fields.Char(string="Nombre", required=True, default="Unidad")
    bill_unit_key = fields.Char(string="Key")
    bill_unit_value = fields.Char(string="Pallet Bill unit")
    active = fields.Boolean(default=True)

    # Relación con transportistas
    carrier_ids = fields.Many2many(
        'delivery.carrier',
        relation='bill_unit_carrier_rel',
        column1='bill_unit_id',
        column2='carrier_id',
        string='Transportistas',
    )

    _sql_constraints = [
        ('bill_unit_key_uniq', 'unique(bill_unit_key)', 'La clave de unidad de facturación debe ser única')
    ]
