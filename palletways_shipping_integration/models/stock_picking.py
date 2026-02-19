from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    number_of_lifts = fields.Char(string="Number Of Lifts",copy=False,default="1")


