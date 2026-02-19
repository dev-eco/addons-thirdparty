# website_dist_checkout/controllers/portal.py

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class PortalDistribuidor(CustomerPortal):
    
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
        
        # Obtener pedidos y entregas
        orders = SaleOrder.search(domain, order='date_order desc')
        deliveries = {}
        
        # Preparar datos de tracking
        for so in orders:
            picking = so.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing')[:1]
            if picking:
                deliveries[so.id] = {
                    'name': picking.name,
                    'state': picking.state,
                    'carrier_name': picking.carrier_id.name if picking.carrier_id else '',
                    'tracking': picking.carrier_tracking_ref or '',
                    'can_upload': picking.state not in ('done', 'cancel'),
                }
        
        return request.render('website_dist_checkout.portal_dist_pedidos', {
            'orders': orders,
            'deliveries': deliveries,
        })
        
    @http.route(['/distribuidor/pedido/<int:order_id>/envio'], type='http', auth="user", website=True)
    def portal_distribuidor_detalles_envio(self, order_id, **kw):
        """Formulario para editar detalles de envío"""
        order = request.env['sale.order'].browse(order_id)
        
        # Verificar acceso
        if not self._check_distribuidor_access(order):
            return request.redirect('/mi/inicio')
            
        if request.httprequest.method == 'POST':
            # Validar y guardar cambios
            values = {
                'dist_carrier_name': kw.get('dist_carrier_name'),
                'dist_carrier_account': kw.get('dist_carrier_account'),
                'dist_pickup_slot': kw.get('dist_pickup_slot'),
            }
            
            # Adjuntar archivos si los hay
            if request.httprequest.files:
                for file_key in ('shipping_label', 'distributor_slip'):
                    uploaded_file = request.httprequest.files.get(file_key)
                    if uploaded_file:
                        # Guardar adjunto y vincular con orden
                        attachment_value = {
                            'name': uploaded_file.filename,
                            'datas': base64.b64encode(uploaded_file.read()),
                            'res_model': 'sale.order',
                            'res_id': order.id,
                            'type': 'binary',
                        }
                        attachment = request.env['ir.attachment'].sudo().create(attachment_value)
                        # Añadir tag para identificar tipo
                        values[f'{file_key}_attachment_id'] = attachment.id
            
            # Actualizar orden y picking
            order.write(values)
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                picking_values = {k: v for k, v in values.items() if k in picking._fields}
                if picking_values:
                    picking.write(picking_values)
                    
            return request.redirect('/distribuidor/pedidos')
        
        return request.render('website_dist_checkout.portal_dist_envio', {
            'order': order,
        })
        
    def _check_distribuidor_access(self, order):
        """Verifica que el usuario actual tenga acceso a esta orden"""
        partner = request.env.user.partner_id
        return order.partner_id.commercial_partner_id == partner.commercial_partner_id
