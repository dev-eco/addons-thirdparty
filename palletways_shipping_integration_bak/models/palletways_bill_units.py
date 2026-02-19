from odoo import fields, models, _, api


class BillUnit(models.Model):
    _name = 'bill.unit'
    _rec_name = 'bill_unit_value'

    bill_unit_key = fields.Char(string="Key")
    bill_unit_value = fields.Char(string="Pallet Bill unit")

