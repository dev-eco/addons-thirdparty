# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    portal_tracking = fields.Char(string="Tracking (Portal)", compute="_compute_portal_tracking", store=False)

    @api.depends('picking_ids.carrier_tracking_ref', 'picking_ids.picking_type_code', 'picking_ids.state')
    def _compute_portal_tracking(self):
        for order in self:
            picks = order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing' and p.carrier_tracking_ref)
            order.portal_tracking = ', '.join(sorted(set(picks.mapped('carrier_tracking_ref')))) if picks else ''
