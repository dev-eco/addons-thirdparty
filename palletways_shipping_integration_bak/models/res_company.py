from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    use_palletways_shipping_provider = fields.Boolean(
        string="Is Use Palletways Shipping Provider?",
        help="True when we need to use palletways shipping provider",
        default=False, copy=False
    )
    palletways_api_url = fields.Char(
        string='Palletways API URL',
        default="https://api.palletways.com",
        help="Get URL details from palletways"
    )
    palletways_api_key = fields.Char(
        string='Palletways API Key',
        help="You need to enter encoded api key here ,which is given by paletways"
    )

    @api.constrains('use_palletways_shipping_provider', 'palletways_api_url', 'palletways_api_key')
    def _check_palletways_config(self):
        for rec in self:
            if rec.use_palletways_shipping_provider and (not rec.palletways_api_url or not rec.palletways_api_key):
                raise ValidationError(_("When using Palletways provider you must configure API URL and API Key."))
