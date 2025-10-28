# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    palletways_depot_code = fields.Char(string="Palletways Depot Code")
    palletways_account_code = fields.Char(string="Palletways Account Code")

    @api.constrains('use_palletways_shipping_provider', 'palletways_api_url', 'palletways_api_key',
                    'palletways_depot_code', 'palletways_account_code')
    def _check_palletways_depot_account(self):
        for rec in self:
            if getattr(rec, 'use_palletways_shipping_provider', False):
                missing = []
                if not rec.palletways_api_url:
                    missing.append("API URL")
                if not rec.palletways_api_key:
                    missing.append("API Key")
                # Si tu API key es de tipo Depot, se requieren estos dos:
                if not rec.palletways_depot_code:
                    missing.append("Depot Code")
                if not rec.palletways_account_code:
                    missing.append("Account Code")
                if missing:
                    raise ValidationError(_("When using Palletways provider you must configure: %s.") % ", ".join(missing))
