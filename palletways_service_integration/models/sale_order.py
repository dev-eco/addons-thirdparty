from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
import datetime
import json
import logging
import time

_logger = logging.getLogger("palletways")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    palletways_service_ids = fields.One2many("palletways.service", "sale_order_id",
                                             string="Available Services")
    palletways_service_id = fields.Many2one("palletways.service", string="Palletways Service",
                                            help="palletways service", copy=False, ondelete='set null')

    def get_service(self):
        """Obtener servicios disponibles usando el nuevo cliente API"""
        order = self
        recipient_address = order.partner_shipping_id
        sender_address = order and order.warehouse_id and order.warehouse_id.partner_id

        if not sender_address.zip or not sender_address.country_id:
            raise ValidationError(
                "Para obtener servicios se requiere código postal y país del remitente")
        if not recipient_address.zip or not recipient_address.country_id:
            raise ValidationError(
                "Para obtener servicios se requiere código postal y país del destinatario")

        # Buscar transportista Palletways configurado
        palletways_carrier = self.env['delivery.carrier'].search([
            ('delivery_type', '=', 'palletways'),
            ('palletways_api_client_id', '!=', False)
        ], limit=1)
        
        if not palletways_carrier:
            raise ValidationError("No hay transportista Palletways configurado con cliente API")

        try:
            # Usar el nuevo cliente API
            api_client = palletways_carrier.palletways_api_client_id
            services_data = api_client.get_available_services(
                sender_address.country_id.code,
                sender_address.zip,
                recipient_address.country_id.code,
                recipient_address.zip,
                'D'  # Delivery
            )
            
            _logger.info(f"Respuesta servicios: {json.dumps(services_data, indent=2)}")
            
            # CAMBIO PRINCIPAL: Manejar respuesta directa como lista
            available_services = []
            
            if isinstance(services_data, list):
                # Respuesta directa como lista (formato actual)
                available_services = services_data
            elif isinstance(services_data, dict):
                # Formato estándar con Status/Detail
                if services_data.get('Status', {}).get('Code') == 'OK':
                    detail = services_data.get('Detail', {})
                    available_services = detail.get('Data', [])
                    
                    # Manejar tanto lista como objeto único
                    if isinstance(available_services, dict):
                        available_services = [available_services]
                else:
                    error_msg = services_data.get('Status', {}).get('Description', 'Error desconocido')
                    raise ValidationError(f"Error Palletways: {error_msg}")
            else:
                raise ValidationError("Formato de respuesta inesperado de la API")
            
            if not available_services:
                raise ValidationError("No se encontraron servicios disponibles para esta ruta")
            
            # Limpiar servicios existentes
            existing_records = self.env['palletways.service'].search([
                ('sale_order_id', '=', self.id)
            ])
            existing_records.sudo().unlink()
            
            # Crear registros de servicios
            for service in available_services:
                service_data = {
                    'service_group_code': service.get('ServiceGroupCode', ''),
                    'service_code': service.get('ServiceCode', ''),
                    'service_name': service.get('ServiceName', ''),
                    'service_group_name': service.get('ServiceGroupName', ''),
                    'service_days_min': str(service.get('ServiceDaysMin', '')),
                    'service_days_max': str(service.get('ServiceDaysMax', '')),
                    'sale_order_id': self.id
                }
                
                _logger.info(f"Creando servicio: {service_data}")
                self.env['palletways.service'].sudo().create(service_data)
                
            # Mensaje de éxito
            self.message_post(
                body=f"Se encontraron {len(available_services)} servicios disponibles para la ruta {sender_address.zip} -> {recipient_address.zip}"
            )
                
        except Exception as e:
            _logger.error(f"Error obteniendo servicios Palletways: {e}")
            raise ValidationError(f"Error obteniendo servicios: {e}")


