# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError


class PalletwaysPortal(CustomerPortal):

    @http.route(['/distribuidor/pedidos'], type='http', auth="user", website=True)
    def portal_distribuidor_pedidos(self, **kw):
        """Vista principal de pedidos para distribuidor"""
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        # Filtrar pedidos donde este partner es el distribuidor
        domain = [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('state', 'in', ['sale', 'done']),
        ]

        orders = SaleOrder.search(domain, order='date_order desc')

        # Preparar información de tracking
        deliveries = {}
        for order in orders:
            picking = order.picking_ids.filtered(
                lambda p: p.picking_type_code == 'outgoing' and p.carrier_tracking_ref
            )[:1]
            if picking:
                deliveries[order.id] = {
                    'tracking': picking.carrier_tracking_ref,
                    'carrier': picking.carrier_id.name if picking.carrier_id else '',
                }

        values = {
            'orders': orders,
            'deliveries': deliveries,
        }

        return request.render('palletways_shipping_integration_ext.portal_dist_orders', values)
