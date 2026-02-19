import json
import uuid
import logging
import math
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    delivery_type = fields.Selection(selection_add=[
        ('palletways', 'Palletways')
    ], ondelete={'palletways': 'cascade'})
    
    palletways_api_client_id = fields.Many2one('palletways.api.client', 
                                               string='Cliente API Palletways')
    
    palletways_service_code = fields.Selection([
        ('A', 'Next Day Standard'),
        ('DH', 'Premium Timed Delivery PM (Pre-Booked)'),
        ('E', 'Next Day AM'),
        ('F', 'Saturday AM'),
        ('H', 'Timed Delivery (Pre-Booked)'),
        ('B', 'Economy'),
        ('J', 'Economy A.M'),
        ('K', 'Economy Timed'),
        ('Z', 'Saturday Economy A.M'),
        ('C', 'Collection - Premium'),
        ('V', 'Collection Premium 48hr'),
        ('I', 'Remote Contract Collection'),
        ('D', 'Collection - Economy'),
        ('N', 'Collection 3 Day'),
        ('P', 'Collection 5 Day'),
        ('X', 'Collection 4 Day'),
        ('0', 'Europe Collect Premium'),
        ('1', 'Europe Saturday Premium'),
        ('2', 'Europe 2 Day Premium'),
        ('3', 'Europe 3 Day Premium'),
        ('4', 'Europe 4+ Day Premium'),
        ('9', 'Europe Timed (Pre-Booked)'),
        ('5', 'Europe 5 Day Economy'),
        ('6', 'Europe 3 Day Economy'),
        ('7', 'Europe 4 Day Economy'),
        ('8', 'Europe Collect Economy'),
        ('O', 'Premium 48'),
        ('L', '3 Day Service'),
    ], string='Código Servicio', default='B')
    
    palletways_default_bill_unit = fields.Selection([
        ('MQP', 'Mini Quarter Pallet (150kg, 0.6m altura)'),
        ('QP', 'Quarter Pallet (300kg, 1.1m altura)'),
        ('HP', 'Half Pallet (600kg, 1.4m altura)'),
        ('LP', 'Light Pallet (750kg, 2.2m altura)'),
        ('FP', 'Full Pallet (1200kg, 2.2m altura)'),
    ], string='Unidad Facturable por Defecto', default='FP')
    
    palletways_auto_book_in = fields.Boolean('Solicitar Cita Automática', 
                                            default=True,
                                            help='Solicitar cita previa para productos pesados')
    palletways_auto_taillift = fields.Boolean('Trampilla Automática', 
                                             default=True,
                                             help='Activar trampilla automática si peso > 300kg')
    palletways_auto_handball = fields.Boolean('Despaletización Automática',
                                             default=False,
                                             help='Activar despaletización para productos específicos')
    
    tail_lift = fields.Boolean(string="Tail Lift?", 
                              help="DEPRECATED: Usar palletways_auto_taillift")
    bill_unit_ids = fields.Many2many('bill.unit', 'delivery_carrier_bill_unit_rel', 
                                    'carrier_id', 'bill_unit_id', 'Bill Unit',
                                    help="DEPRECATED: Configurar en API Client")
    notification = fields.Boolean('Notification?',
                                 help="DEPRECATED: Configurar en API Client")
    
    @api.constrains('delivery_type', 'palletways_api_client_id')
    def _check_palletways_config(self):
        for carrier in self:
            if carrier.delivery_type == 'palletways' and not carrier.palletways_api_client_id:
                raise ValidationError("Debe configurar un Cliente API de Palletways")

    def palletways_send_shipping(self, pickings):
        """
        ✅ CORRECCIÓN v2.1.4: Retornar formato compatible con delivery.carrier base
        """
        _logger.info(f"palletways_send_shipping() iniciado para {len(pickings)} albaranes")
        
        self.ensure_one()
        
        if not self.palletways_api_client_id:
            raise UserError("Transportista Palletways sin cliente API configurado")
        
        api_client = self.palletways_api_client_id
        results = []
        
        for picking in pickings:
            try:
                _logger.info(f"Procesando albarán {picking.name}")
                
                self._validate_palletways_picking(picking)
                _logger.info(f"✓ Validación exitosa para {picking.name}")
                
                shipment_data = self._prepare_palletways_shipment_data(picking)
                _logger.info(f"✓ Datos preparados para {picking.name}")
                _logger.debug(f"Datos envío: {json.dumps(shipment_data, indent=2, default=str)}")
                
                api_response = api_client.create_consignment(shipment_data)
                _logger.info(f"✓ Respuesta API recibida para {picking.name}")
                _logger.debug(f"Respuesta API: {json.dumps(api_response, indent=2, default=str)}")
                
                tracking_id, response_id = self._process_api_response(api_response, picking, api_client)
                _logger.info(f"✓ Tracking ID generado: {tracking_id}")
                
                shipment = self._create_palletways_shipment(
                    picking, 
                    tracking_id, 
                    response_id, 
                    shipment_data,
                    api_response
                )
                _logger.info(f"✓ Registro palletways.shipment creado: {shipment.id}")
                
                picking.write({
                    'palletways_shipment_id': shipment.id,
                    'carrier_tracking_ref': tracking_id,
                })
                _logger.info(f"✓ Picking actualizado con shipment_id y tracking_ref")
                
                picking.message_post(
                    body=f"✅ Envío Palletways creado exitosamente<br/>"
                         f"<strong>Tracking ID:</strong> {tracking_id}<br/>"
                         f"<strong>Servicio:</strong> {shipment.service_name}<br/>"
                         f"<strong>Peso:</strong> {shipment.weight}kg<br/>"
                         f"<strong>Pallets:</strong> {shipment.pallets}",
                    message_type='comment'
                )
                
                results.append({
                    'exact_price': 0.0,
                    'tracking_number': tracking_id,
                    'labels': [],
                })
                
            except UserError as e:
                error_msg = str(e)
                _logger.error(f"✗ Error de validación para {picking.name}: {error_msg}")
                picking.message_post(
                    body=f"❌ Error creando envío Palletways:<br/>{error_msg}",
                    message_type='comment'
                )
                raise
                
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                _logger.error(f"✗ Error inesperado para {picking.name}: {error_msg}", exc_info=True)
                picking.message_post(
                    body=f"❌ Error inesperado creando envío:<br/>{error_msg}",
                    message_type='comment'
                )
                raise UserError(error_msg)
        
        _logger.info(f"palletways_send_shipping() completado. Resultados: {len(results)}")
        return results

    def _process_api_response(self, api_response, picking, api_client):
        """
        ✅ CORRECCIÓN v2.3.0:
        Procesar respuesta XML de Palletways
        """
        _logger.info("="*80)
        _logger.info("RESPUESTA API (XML):")
        _logger.info(f"{json.dumps(api_response, indent=2, default=str)}")
        _logger.info("="*80)
        
        if not api_response:
            raise UserError("Respuesta vacía de la API")
        
        status = api_response.get('Status', {})
        if isinstance(status, list):
            status = status[0] if status else {}
        
        if isinstance(status, str):
            status_code = status
            status_desc = ''
        else:
            status_code = status.get('Code', status.get('_text', ''))
            status_desc = status.get('Description', '')
        
        _logger.info(f"Status Code: {status_code}")
        _logger.info(f"Status Description: {status_desc}")
        
        if status_code != 'OK':
            raise UserError(f"Error API: {status_code} - {status_desc}")
        
        detail = api_response.get('Detail', {})
        if isinstance(detail, list):
            detail = detail[0] if detail else {}
        
        import_detail = detail.get('ImportDetail', {})
        if isinstance(import_detail, list):
            import_detail = import_detail[0] if import_detail else {}
        
        response_id = import_detail.get('ResponseID', import_detail.get('_text', ''))
        
        if not response_id:
            data = detail.get('Data', {})
            if isinstance(data, list):
                data = data[0] if data else {}
            response_id = data.get('ResponseID', data.get('_text', ''))
        
        if not response_id:
            message = detail.get('Message', detail.get('_text', ''))
            
            if api_client and api_client.test_mode:
                raise UserError(
                    f"❌ MODO PRUEBA - No se crea envío real\n\n"
                    f"Mensaje: {message}\n\n"
                    f"Para crear envíos reales:\n"
                    f"1. Desactivar 'Modo Prueba' en Cliente API\n"
                    f"2. Volver a validar el albarán"
                )
            else:
                raise UserError(f"❌ No se recibió ResponseID\n\nMensaje: {message}")
        
        tracking_id = response_id
        
        _logger.info(f"✓ Tracking ID: {tracking_id}, Response ID: {response_id}")
        
        return tracking_id, response_id

    def _create_palletways_shipment(self, picking, tracking_id, response_id, shipment_data, api_response):
        """
        Crear registro palletways.shipment
        """
        shipment_vals = {
            'tracking_id': tracking_id,
            'picking_id': picking.id,
            'response_id': response_id,
            'status': 'created',
            'service_code': shipment_data.get('service_code', ''),
            'weight': shipment_data.get('weight', 0),
            'pallets': shipment_data.get('pallets', 1),
            'bill_unit_type': shipment_data.get('bill_unit_type', 'FP'),
            'collection_date': shipment_data.get('collection_date', ''),
            'delivery_date': shipment_data.get('delivery_date', ''),
            'api_response': json.dumps(api_response, indent=2, default=str),
            'notes': f"Envío creado automáticamente al validar albarán {picking.name}",
        }
        
        shipment = self.env['palletways.shipment'].create(shipment_vals)
        _logger.info(f"Shipment creado: {shipment.id}")
        
        return shipment

    def palletways_rate_shipment(self, order):
        """Calcular precio envío Palletways"""
        try:
            total_weight = sum(
                line.product_uom_qty * line.product_id.weight 
                for line in order.order_line 
                if line.product_id.weight
            ) or 1.0
            
            base_prices = {
                'A': 80.0,
                'B': 50.0,
                'DH': 85.0,
                'E': 90.0,
                'F': 100.0,
                'H': 120.0,
                'C': 75.0,
                'V': 60.0,
                'D': 45.0,
                'L': 40.0,
                'O': 60.0,
            }
            
            base_price = base_prices.get(self.palletways_service_code, 50.0)
            
            if total_weight > 1000:
                base_price *= 2.0
            elif total_weight > 500:
                base_price *= 1.5
            elif total_weight > 200:
                base_price *= 1.2
            
            if self.palletways_auto_taillift and total_weight > 300:
                base_price += 15.0
            
            if self.palletways_auto_book_in:
                base_price += 10.0
            
            return {
                'success': True,
                'price': base_price,
                'error_message': False,
                'warning_message': False
            }
            
        except Exception as e:
            _logger.error(f"Error calculando precio Palletways: {e}")
            return {
                'success': False,
                'price': 0.0,
                'error_message': str(e),
                'warning_message': False
            }

    def _validate_palletways_picking(self, picking):
        """Validar picking antes de enviar a Palletways"""
        errors = []
        
        if not picking.partner_id:
            errors.append("El albarán debe tener dirección de entrega")
        else:
            if not picking.partner_id.zip:
                errors.append("La dirección de entrega debe tener código postal")
            if not picking.partner_id.country_id:
                errors.append("La dirección de entrega debe tener país")
            if not picking.partner_id.city:
                errors.append("La dirección de entrega debe tener ciudad")
            if not picking.partner_id.name:
                errors.append("La dirección de entrega debe tener nombre de contacto")
            if not picking.partner_id.phone and not picking.partner_id.mobile:
                errors.append("La dirección de entrega DEBE tener teléfono (requerido por Palletways)")
        
        if not picking.move_line_ids:
            errors.append("El albarán debe tener líneas de productos")
        
        origin_partner = picking.company_id.partner_id
        if not origin_partner:
            errors.append("La empresa debe tener dirección configurada")
        elif not origin_partner.zip or not origin_partner.country_id:
            errors.append("La dirección de origen debe tener código postal y país")
        elif not origin_partner.city:
            errors.append("La dirección de origen debe tener ciudad")
        elif not origin_partner.phone and not origin_partner.mobile:
            errors.append("La dirección de origen debe tener teléfono")
        
        total_weight = sum(
            line.quantity * line.product_id.weight 
            for line in picking.move_line_ids 
            if line.product_id.weight
        )
        
        if total_weight < 1:
            errors.append("El peso total debe ser mayor a 1kg")
        
        bill_unit_type = self._calculate_bill_unit_type(total_weight, len(picking.move_line_ids))
        try:
            self._validate_pallet_constraints(total_weight, bill_unit_type)
        except UserError as e:
            errors.append(str(e))
        
        if errors:
            error_msg = "Errores de validación:\n• " + "\n• ".join(errors)
            _logger.error(f"Validación fallida para {picking.name}: {error_msg}")
            raise UserError(error_msg)
        
        _logger.info(f"Validación exitosa para {picking.name} - Peso: {total_weight}kg, Tipo: {bill_unit_type}")
    
    def _validate_pallet_constraints(self, weight, bill_unit_type):
        """
        Validar restricciones de peso según tipo de pallet
        ✅ CORRECCIÓN v2.1.1: Según documentación oficial página 14 (España)
        """
        pallet_limits = {
            'MQP': {'max_weight': 150, 'max_height': 0.6, 'name': 'Mini Quarter Pallet'},
            'QP': {'max_weight': 300, 'max_height': 1.1, 'name': 'Quarter Pallet'},
            'HP': {'max_weight': 600, 'max_height': 1.4, 'name': 'Half Pallet'},
            'LP': {'max_weight': 750, 'max_height': 2.2, 'name': 'Light Pallet'},
            'FP': {'max_weight': 1200, 'max_height': 2.2, 'name': 'Full Pallet'},
        }
        
        if bill_unit_type in pallet_limits:
            limit = pallet_limits[bill_unit_type]
            if weight > limit['max_weight']:
                raise UserError(
                    f"El peso {weight}kg excede el límite de {limit['max_weight']}kg "
                    f"para {limit['name']}. Seleccione un tipo de pallet mayor."
                )
    
    def _calculate_bill_unit_type(self, total_weight, total_qty):
        """
        Calcular tipo de unidad facturable según peso
        ✅ CORRECCIÓN v2.1.1: Según documentación oficial página 14 (España)
        """
        if total_weight <= 150:
            return 'MQP'
        elif total_weight <= 300:
            return 'QP'
        elif total_weight <= 600:
            return 'HP'
        elif total_weight <= 750:
            return 'LP'
        else:
            return 'FP'
    
    def _prepare_palletways_shipment_data(self, picking):
        """Preparar datos para envío Palletways según especificación oficial"""
        total_weight = sum(
            line.quantity * line.product_id.weight 
            for line in picking.move_line_ids 
            if line.product_id.weight
        ) or 1.0
        
        total_qty = sum(line.quantity for line in picking.move_line_ids)
        
        consignment_number = str(uuid.uuid4().int)[:10]
        
        shipment_type = 'D'
        
        bill_unit_type = self._calculate_bill_unit_type(total_weight, total_qty)
        
        needs_taillift = self._needs_taillift(picking, total_weight)
        needs_handball = self._needs_handball(picking)
        needs_book_in = self._needs_book_in(picking, total_weight)
        
        collection_date = fields.Date.today()
        delivery_date = self._calculate_delivery_date(collection_date)
        
        if not picking.company_id.partner_id:
            raise UserError("La empresa debe tener dirección configurada")
        
        if not picking.partner_id:
            raise UserError("El albarán debe tener dirección de entrega")
        
        return {
            'type': shipment_type,
            'import_id': picking.name,
            'reference': picking.name,
            'client_reference': picking.origin or picking.name,
            'pallets': max(1, int(math.ceil(total_weight / 500))),
            'weight': int(total_weight),
            'handball': needs_handball,
            'taillift': needs_taillift,
            'classification': 'B2B',
            'book_in_request': needs_book_in,
            'manifest_note': picking.note or '',
            'collection_date': collection_date.strftime('%Y-%m-%d'),
            'delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'service_code': self.palletways_service_code,
            'bill_unit_type': bill_unit_type,
            'bill_unit_amount': 1,
            'collection_address': picking.company_id.partner_id,
            'delivery_address': picking.partner_id,
            'contact_name': picking.partner_id.name,
            'contact_phone': picking.partner_id.phone or picking.partner_id.mobile or '',
            'book_in_instructions': f"Contactar a {picking.partner_id.name}",
            'notification_emails': picking.partner_id.email or '',
        }
    
    def _needs_taillift(self, picking, weight):
        """Determinar si se necesita trampilla elevadora"""
        if not self.palletways_auto_taillift:
            return False
        
        return weight > 300
    
    def _needs_handball(self, picking):
        """Determinar si se necesita despaletización"""
        if not self.palletways_auto_handball:
            return False
        
        return False
    
    def _needs_book_in(self, picking, weight):
        """Determinar si se necesita cita previa"""
        if not self.palletways_auto_book_in:
            return False
        
        return weight > 200
    
    def _calculate_delivery_date(self, collection_date):
        """Calcular fecha de entrega según servicio"""
        service_days = {
            'A': 1,
            'B': 2,
            'DH': 1,
            'E': 1,
            'F': 2,
            'H': 1,
            'C': 1,
            'D': 2,
            'L': 3,
            'O': 2,
        }
        
        days = service_days.get(self.palletways_service_code, 2)
        return collection_date + timedelta(days=days)
