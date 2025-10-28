# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from werkzeug.utils import redirect
from odoo.tools import format_datetime, format_amount
import base64


class DistPortalController(CustomerPortal):

    @http.route(
        ['/my/distributor/orders', '/my/distributor/orders/page/<int:page>'],
        type='http', auth="user", website=True
    )
    def portal_dist_orders(self, page=1, search=None, sortby='date', search_in='client_ref', **kw):
        user_partner = request.env.user.partner_id.commercial_partner_id
        Sale = request.env['sale.order'].sudo()

        domain = [
            ('company_id', '=', request.env.company.id),
            ('partner_id.commercial_partner_id', '=', user_partner.id),
        ]
        # Búsqueda según selector (por defecto, referencia de cliente)
        if search:
            if search_in == 'order_name':
                domain += [('name', 'ilike', search)]
            else:
                domain += [('client_order_ref', 'ilike', search)]

        sort_mapping = {
            'date': 'date_order desc',
            'name': 'name desc',
            'amount': 'amount_total desc',
        }
        order = sort_mapping.get(sortby, 'date_order desc')

        total = Sale.search_count(domain)
        step = 20
        pager = portal_pager(
            url="/my/distributor/orders",
            url_args={'search': search or '', 'sortby': sortby, 'search_in': search_in},
            total=total, page=page, step=step
        )
        orders = Sale.search(domain, order=order, limit=step, offset=pager['offset'])

        tz = request.env.context.get('tz') or None
        order_dates = {}
        order_amounts = {}
        deliveries = {}
        for so in orders:
            order_dates[so.id] = format_datetime(request.env, so.date_order, tz=tz) if so.date_order else ""
            order_amounts[so.id] = format_amount(request.env, so.amount_total, so.currency_id)

            picks = so.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')
            states = set(p.state for p in picks)
            if not picks:
                delivery_state_label = "Sin albaranes"
            elif states == {'done'}:
                delivery_state_label = "Entregado"
            elif 'done' in states:
                delivery_state_label = "Parcialmente entregado"
            elif any(s in states for s in ('assigned', 'confirmed', 'waiting', 'scheduled')):
                delivery_state_label = "Pendiente de entrega"
            else:
                delivery_state_label = ", ".join(sorted(states))

            scheduled_dates = [p.scheduled_date for p in picks if p.scheduled_date]
            expected_date = min(scheduled_dates) if scheduled_dates else False
            expected_date_str = format_datetime(request.env, expected_date, tz=tz) if expected_date else ""
            carrier_name = so.carrier_id.name or ", ".join(sorted({p.carrier_id.name for p in picks if p.carrier_id}))
            tracking_refs = ", ".join(sorted({p.carrier_tracking_ref for p in picks if p.carrier_tracking_ref}))

            deliveries[so.id] = {
                'delivery_state': delivery_state_label,
                'expected_date_str': expected_date_str,
                'carrier_name': carrier_name,
                'tracking': tracking_refs,
            }

        values = self._prepare_portal_layout_values()
        values.update({
            'orders': orders,
            'order_dates': order_dates,
            'order_amounts': order_amounts,
            'deliveries': deliveries,
            'page_name': 'distributor_orders',
            'pager': pager,
            'search': search or "",
            'sortby': sortby,
            'search_in': search_in,  # <- importante
            'distributor_name': user_partner.display_name,
            'title': user_partner.display_name,
        })
        return request.render("website_dist_checkout.portal_dist_orders", values)

    @http.route(
        ['/my/orders/<int:order_id>/dist-shipping'],
        type='http', auth="user", website=True, methods=['GET', 'POST']
    )
    def portal_dist_shipping(self, order_id, **post):
        # ... tu método tal como lo tenías ...
        user_partner = request.env.user.partner_id.commercial_partner_id
        so = request.env['sale.order'].sudo().browse(order_id).exists()
        if not so or so.company_id != request.env.company:
            return request.not_found()
        if so.partner_id.commercial_partner_id.id != user_partner.id:
            return request.not_found()

        Param = request.env['ir.config_parameter'].sudo()
        dist_carrier_id = int(Param.get_param("website_dist_checkout.carrier_id", default="0") or 0)
        is_managed = bool(dist_carrier_id and so.carrier_id and so.carrier_id.id == dist_carrier_id)

        if request.httprequest.method == 'POST':
            if not is_managed:
                return redirect(f"/my/orders/{order_id}")

            vals = {
                "client_order_ref": post.get("client_order_ref") or False,
                "dist_carrier_name": post.get("dist_carrier_name") or False,
                "dist_carrier_account": post.get("dist_carrier_account") or False,
                "dist_pickup_slot": post.get("dist_pickup_slot") or False,
            }
            dt = post.get("dist_pickup_datetime")
            if dt:
                vals["dist_pickup_datetime"] = dt.replace("T", " ") + ":00"

            so.sudo().write(vals)

            files = request.httprequest.files

            def _save_b64(fileobj, fname_field):
                if fileobj and getattr(fileobj, "filename", ""):
                    content = fileobj.read()
                    if not content:
                        return
                    b64 = base64.b64encode(content).decode("ascii")
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': fileobj.filename,
                        'datas': b64,
                        'res_model': 'sale.order',
                        'res_id': so.id,
                        'mimetype': fileobj.mimetype or 'application/octet-stream',
                    })
                    so.sudo().write({fname_field: attachment.id})

            if files.get('dist_label_attachment'):
                _save_b64(files.get('dist_label_attachment'), "dist_label_attachment_id")
            if files.get('dist_packing_slip_attachment'):
                _save_b64(files.get('dist_packing_slip_attachment'), "dist_packing_slip_attachment_id")

            return redirect(f"/my/orders/{order_id}")

        return request.render("website_dist_checkout.portal_dist_form", {
            "sale_order": so,
            "is_managed": is_managed,
        })
