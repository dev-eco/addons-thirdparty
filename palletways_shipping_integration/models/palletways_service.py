from odoo import models, fields, api


class PalletwayService(models.Model):
    _name = "palletways.service"
    _rec_name = "service_name"

    service_group_code = fields.Char(string="Service Group Code")
    service_code = fields.Char(string="Service Code")
    service_name = fields.Char(string="Service Name")
    service_group_name = fields.Char(string="Service Group Name")
    service_days_min = fields.Char(string="Min Days")
    service_days_max = fields.Char(string="Max Days")
    sale_order_id = fields.Many2one("sale.order", string="Sales Order")

    def set_service(self):
        self.sale_order_id.palletways_service_id = self.id
