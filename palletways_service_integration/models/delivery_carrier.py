import json
import uuid
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    delivery_type = fields.Selection(selection_add=[
        ('palletways', 'Palletways')
    ], ondelete={'palletways': 'cascade'})
    
    # NUEVA CONFIGURACIÓN API
    palletways_api_client_id = fields.Many2one('palletways.api.client', 
                                               string='Cliente API Palletways')
    
    # CONFIGURACIÓN SERVICIOS - Actualizado según documentación web oficial
    palletways_service_code = fields.Selection([
        # ENTREGAS Premium - Según documentación web oficial
        ('A', 'Next Day Standard'),
        ('DH', 'Premium Timed Delivery PM (Pre-Booked)'),
        ('E', 'Next Day AM'),
        ('F', 'Saturday AM'),
        ('H', 'Timed Delivery (Pre-Booked)'),
        
        # ENTREGAS Economy
        ('B', 'Economy'),
        ('J', 'Economy A.M'),
        ('K', 'Economy Timed'),
        ('Z', 'Saturday Economy A.M'),
        
        # RECOGIDAS Premium
        ('C', 'Collection - Premium'),
        ('V', 'Collection Premium 48hr'),
        ('I', 'Remote Contract Collection'),
        
        # RECOGIDAS Economy  
        ('D', 'Collection - Economy'),
        ('N', 'Collection 3 Day'),
        ('P', 'Collection 5 Day'),
        ('X', 'Collection 4 Day'),
        
        # INTERNACIONALES Premium
        ('0', 'Europe Collect Premium'),
        ('1', 'Europe Saturday Premium'),
        ('2', 'Europe 2 Day Premium'),
        ('3', 'Europe 3 Day Premium'),
        ('4', 'Europe 4+ Day Premium'),
        ('9', 'Europe Timed (Pre-Booked)'),
        
        # INTERNACIONALES Economy
        ('5', 'Europe 5 Day Economy'),
        ('6', 'Europe 3 Day Economy'),
        ('7', 'Europe 4 Day Economy'),
        ('8', 'Europe Collect Economy'),
        
        # IRLANDESES
        ('O', 'Premium 48'),
        ('L', '3 Day Service'),
    ], string='Código Servicio', default='B')
    
    palletways_default_bill_unit = fields.Selection([
        ('FP', 'Full Pallet (1.2 x 1 x 2.2m - 1200kg)'),
        ('LP', 'Light Pallet (1.2 x 1 x 2.2m - 750kg)'),
        ('HP', 'Half Pallet (1.2 x 1 x 1.1m - 250kg)'),
        ('QP', 'Quarter Pallet (1.2 x 1 x 0.8m - 250kg)'),
        ('MQP', 'Mini Quarter Pallet (1.2 x 1 x 0.6m - 150kg)'),
    ], string='Unidad Facturable por Defecto', default='FP')
    
    # CONFIGURACIONES ESPECÍFICAS ECOCAUCHO
    palletways_auto_book_in = fields.Boolean('Solicitar Cita Automática', 
                                            default=True,
                                            help='Solicitar cita previa para productos pesados')
    palletways_auto_taillift = fields.Boolean('Trampilla Automática', 
                                             default=True,
                                             help='Activar trampilla automática si peso > 300kg')
    palletways_auto_handball = fields.Boolean('Despaletización Automática',
                                             default=False,
                                             help='Activar despaletización para productos específicos')
    
    # CAMPOS LEGACY (mantener compatibilidad)
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

    def palletways_rate_shipment(self, order):
        """Calcular precio envío Palletways"""
        try:
            # Calcular peso total
            total_weight = sum(
                line.product_uom_qty * line.product_id.weight 
                for line in order.order_line 
                if line.product_id.weight
            ) or 1.0
            
            # Precio base según servicio (actualizado según documentación oficial)
            base_prices = {
                'A': 80.0,   # Premium 24H (Next Day Standard)
                'B': 50.0,   # Economy 48H
                'DY': 85.0,  # Premium 14H
                'E': 90.0,   # Premium 12H (Next Day AM)
                'F': 100.0,  # Premium Sábado (Saturday AM)
                'H': 120.0,  # Premium Timed (Pre-Booked)
                'C': 75.0,   # Premium Collection
                'AB': 55.0,  # Premium 48H Collection
                'D': 45.0,   # Economy Collection
                'L': 40.0,   # Economy 72H
                'O': 60.0,   # Premium 48H
            }
            
            base_price = base_prices.get(self.palletways_service_code, 50.0)
            
            # Ajuste por peso (productos pesados EcoCaucho)
            if total_weight > 1000:
                base_price *= 2.0
            elif total_weight > 500:
                base_price *= 1.5
            elif total_weight > 200:
                base_price *= 1.2
            
            # Ajuste por servicios adicionales
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
        
        # Validar dirección de entrega
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
        
        # Validar líneas de productos
        if not picking.move_line_ids:
            errors.append("El albarán debe tener líneas de productos")
        
        # Validar dirección origen
        origin_partner = picking.company_id.partner_id
        if not origin_partner:
            errors.append("La empresa debe tener dirección configurada")
        elif not origin_partner.zip or not origin_partner.country_id:
            errors.append("La dirección de origen debe tener código postal y país")
        elif not origin_partner.city:
            errors.append("La dirección de origen debe tener ciudad")
        
        # Validaciones específicas EcoCaucho
        total_weight = sum(
            line.quantity * line.product_id.weight 
            for line in picking.move_line_ids 
            if line.product_id.weight
        )
        
        if total_weight < 1:
            errors.append("El peso total debe ser mayor a 1kg")
        
        # Validar según tipo de unidad facturable
        bill_unit_type = self._calculate_bill_unit_type(total_weight, len(picking.move_line_ids))
        try:
            self._validate_pallet_constraints(total_weight, bill_unit_type)
        except UserError as e:
            errors.append(str(e))
        
        # Lanzar todos los errores juntos
        if errors:
            error_msg = "Errores de validación:\n• " + "\n• ".join(errors)
            _logger.error(f"Validación fallida para {picking.name}: {error_msg}")
            raise UserError(error_msg)
        
        _logger.info(f"Validación exitosa para {picking.name} - Peso: {total_weight}kg, Tipo: {bill_unit_type}")
    
    def _prepare_palletways_shipment_data(self, picking):
        """Preparar datos para envío Palletways según especificación oficial"""
        # Calcular peso y cantidades
        total_weight = sum(
            line.quantity * line.product_id.weight 
            for line in picking.move_line_ids 
            if line.product_id.weight
        ) or 1.0
        
        total_qty = sum(line.quantity for line in picking.move_line_ids)
        
        # Generar número de consignación único
        consignment_number = str(uuid.uuid4().int)[:10]
        
        # Determinar tipo de envío según documentación oficial
        shipment_type = 'D'  # D=Delivery por defecto (más común)
        
        # Lógica inteligente para unidad facturable
        bill_unit_type = self._calculate_bill_unit_type(total_weight, total_qty)
        
        # Determinar servicios especiales
        needs_taillift = self._needs_taillift(picking, total_weight)
        needs_handball = self._needs_handball(picking)
        needs_book_in = self._needs_book_in(picking, total_weight)
        
        # Fechas
        collection_date = fields.Date.today()
        delivery_date = self._calculate_delivery_date(collection_date)
        
        # Validar direcciones antes de preparar datos
        if not picking.company_id.partner_id:
            raise UserError("La empresa debe tener dirección configurada")
        
        if not picking.partner_id:
            raise UserError("El albarán debe tener dirección de entrega")
        
        return {
            'type': shipment_type,
            'import_id': picking.origin or consignment_number,
            'reference': consignment_number,
            'client_reference': picking.name,
            'weight': int(total_weight),
            'pallets': max(1, int(total_qty / 50)),  # Estimación pallets
            'service_code': self.palletways_service_code,
            'surcharge_code': self.palletways_service_code,
            'bill_unit_type': bill_unit_type,
            'bill_unit_amount': 1,
            'classification': 'B2B',
            'handball': needs_handball,
            'taillift': needs_taillift,
            'book_in_request': needs_book_in,
            'contact_name': picking.partner_id.name or '',
            'contact_phone': picking.partner_id.phone or picking.partner_id.mobile or '',
            'contact_note': 'Productos pesados - llamar antes' if total_weight > 300 else '',
            'instructions': 'Cita previa requerida para descarga' if needs_book_in else '',
            'manifest_note': f'Envío {picking.name} - {len(picking.move_line_ids)} productos',
            'collection_address': picking.company_id.partner_id,
            'delivery_address': picking.partner_id,
            'collection_date': collection_date.strftime('%Y-%m-%d'),
            'delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'notification_emails': picking.partner_id.email if picking.partner_id.email else None,
        }
    
    def _calculate_bill_unit_type(self, weight, quantity):
        """Calcular tipo de unidad facturable según peso y cantidad"""
        # Usar configuración por defecto si está definida
        if self.palletways_default_bill_unit:
            return self.palletways_default_bill_unit
        
        # Lógica automática basada en peso según documentación oficial
        if weight <= 150:
            return 'MQP'
        elif weight <= 300:
            return 'QP' 
        elif weight <= 450:
            return 'ELP'
        elif weight <= 600:
            return 'SELP'  # o 'HP' - ambos soportan 600kg
        elif weight <= 750:
            return 'LP'
        else:
            return 'FP'
    
    def _needs_taillift(self, picking, total_weight):
        """Determinar si necesita trampilla elevadora"""
        if self.palletways_auto_taillift and total_weight > 300:
            return True
        
        # Compatibilidad con campo legacy
        if hasattr(self, 'tail_lift') and self.tail_lift:
            return True
        
        # Lógica específica por productos
        for line in picking.move_line_ids:
            if 'caucho' in (line.product_id.name or '').lower():
                return True
        
        return False
    
    def _needs_handball(self, picking):
        """Determinar si necesita despaletización"""
        if self.palletways_auto_handball:
            return True
        
        # Lógica específica por categorías de producto
        for line in picking.move_line_ids:
            if line.product_id.categ_id and 'caucho' in line.product_id.categ_id.name.lower():
                return True
        
        return False
    
    def _needs_book_in(self, picking, total_weight):
        """Determinar si necesita cita previa"""
        if self.palletways_auto_book_in:
            return True
        
        # Siempre para productos pesados
        if total_weight > 500:
            return True
        
        return False
    
    def _validate_pallet_constraints(self, weight, bill_unit_type):
        """Validar restricciones de peso según tipo de pallet - Según documentación oficial"""
        pallet_limits = {
            'MQP': 150,    # Mini Quarter Pallet
            'QP': 300,     # Quarter Pallet
            'SELP': 600,   # Super Euro Light Pallet
            'HP': 600,     # Half Pallet
            'ELP': 450,    # Extra Light Pallet
            'LP': 750,     # Light Pallet
            'FP': 1200,    # Full Pallet
        }
        
        max_weight = pallet_limits.get(bill_unit_type, 1200)
        
        if weight > max_weight:
            raise UserError(
                f"El peso {weight}kg excede el límite para {bill_unit_type} ({max_weight}kg)"
            )
    
    def get_available_palletways_services(self, origin_postcode, dest_postcode, consignment_type='D'):
        """Obtener servicios disponibles desde Palletways"""
        if not self.palletways_api_client_id:
            return []
        
        try:
            # Usar códigos de país por defecto
            origin_country = self.env.company.country_id.code or 'ES'
            dest_country = 'ES'  # Por defecto España
            
            services_data = self.palletways_api_client_id.get_available_services(
                origin_country, origin_postcode,
                dest_country, dest_postcode,
                consignment_type
            )
            
            if services_data.get('success'):
                return services_data.get('services', [])
            else:
                _logger.warning(f"Error obteniendo servicios: {services_data.get('error')}")
                return []
                
        except Exception as e:
            _logger.error(f"Error obteniendo servicios disponibles: {e}")
            return []
    
    def _calculate_delivery_date(self, collection_date):
        """Calcular fecha de entrega según servicio - Actualizado según documentación oficial"""
        days_mapping = {
            # Premium Delivery
            'A': 1,   # Premium 24H
            'DY': 1,  # Premium 14H
            'E': 1,   # Premium 12H
            'F': 1,   # Premium Sábado
            'H': 1,   # Premium Timed
            'O': 2,   # Premium 48H
            'A1': 7,  # Premium Islas 7D
            'A2': 9,  # Premium Islas 9D
            # Economy Delivery
            'B': 2,   # Economy 48H
            'L': 3,   # Economy 72H
            # Collections
            'C': 1,   # Premium Collection
            'AB': 2,  # Premium 48H Collection
            'D': 2,   # Economy Collection
            'A3': 7,  # Premium Islas Canarias Collection
            # International Premium
            '0': 1,   # Premium Collect
            '1': 1,   # Premium Saturday
            '2': 2,   # Premium 2 Day
            '3': 3,   # Premium 3 Day
            '4': 4,   # Premium 4+ Day
            '9': 1,   # Premium Timed
            # International Economy
            '5': 5,   # Economy 5 Day
            '6': 3,   # Economy 3 Day
            '7': 4,   # Economy 4 Day
            '8': 1,   # Economy Collect
        }
        
        days_to_add = days_mapping.get(self.palletways_service_code, 2)
        return collection_date + timedelta(days=days_to_add)
    
    def _is_successful_response(self, api_response):
        """Verificar si la respuesta de la API es exitosa"""
        if not api_response:
            return False
        
        # CAMBIO: Manejar Status como lista o dict
        status = api_response.get('Status', {})
        if isinstance(status, list):
            status = status[0] if status else {}
        
        return status.get('Code') == 'OK'
    
    def _extract_error_message(self, api_response):
        """Extraer mensaje de error de la respuesta API según documentación oficial"""
        if not api_response:
            return "Respuesta vacía de la API"
        
        # Manejar Status como lista o dict
        status = api_response.get('Status', {})
        if isinstance(status, list):
            status = status[0] if status else {}
        
        if status.get('Code') != 'OK':
            error_description = status.get('Description', 'Error desconocido')
            
            # Procesar errores de validación según estructura documentada
            validation_errors = api_response.get('ValidationErrors', {})
            if validation_errors:
                error_details = []
                
                # Errores de consignación según documentación oficial
                consignment_errors = validation_errors.get('Consignment', [])
                if not isinstance(consignment_errors, list):
                    consignment_errors = [consignment_errors] if consignment_errors else []
                
                for cons_error in consignment_errors:
                    if isinstance(cons_error, dict):
                        index = cons_error.get('Index', 'N/A')
                        import_id = cons_error.get('ImportID', 'Sin ID')
                        errors = cons_error.get('Error', [])
                        
                        if not isinstance(errors, list):
                            errors = [errors] if errors else []
                        
                        for error in errors:
                            if isinstance(error, dict):
                                error_code = error.get('Code', 'ERROR_UNKNOWN')
                                error_desc = error.get('Description', 'Error sin descripción')
                                error_details.append(f"Consignación {index} [{import_id}]: {error_code} - {error_desc}")
                
                # Errores de cuenta
                account_errors = validation_errors.get('Account', [])
                if not isinstance(account_errors, list):
                    account_errors = [account_errors] if account_errors else []
                
                for acc_error in account_errors:
                    if isinstance(acc_error, dict):
                        errors = acc_error.get('Error', [])
                        if not isinstance(errors, list):
                            errors = [errors] if errors else []
                        
                        for error in errors:
                            if isinstance(error, dict):
                                error_code = error.get('Code', 'ERROR_UNKNOWN')
                                error_desc = error.get('Description', 'Error sin descripción')
                                error_details.append(f"Cuenta: {error_code} - {error_desc}")
                
                if error_details:
                    return f"{error_description}\n\nDetalles de validación:\n• " + "\n• ".join(error_details)
            
            return error_description
        
        return "Error procesando respuesta"
    
    def _process_successful_shipment(self, picking, api_response, shipment_data):
        """Procesar respuesta exitosa y crear registro de envío"""
        detail = api_response.get('Detail', {})
        import_detail = detail.get('ImportDetail', {})
        
        if isinstance(import_detail, list):
            import_detail = import_detail[0] if import_detail else {}
        
        response_id = import_detail.get('ResponseID')
        tracking_id = import_detail.get('TrackingID')
        
        if not response_id:
            raise UserError("No se recibió ResponseID de Palletways")
        
        # Generar tracking ID temporal si no viene en respuesta
        if not tracking_id:
            tracking_id = f"PW-{response_id}"
        
        # Crear registro local del envío
        shipment = self.env['palletways.shipment'].create({
            'picking_id': picking.id,
            'response_id': response_id,
            'tracking_id': tracking_id,
            'api_response': json.dumps(api_response),
            'status': 'created',
            'service_code': self.palletways_service_code,
            'consignment_number': shipment_data.get('reference'),
            'weight': shipment_data.get('weight'),
            'pallets': shipment_data.get('pallets'),
        })
        
        # Actualizar picking con relación al envío y tracking
        picking.write({
            'palletways_shipment_id': shipment.id,
            'carrier_tracking_ref': tracking_id
        })
        
        # Mensaje en picking
        picking.message_post(
            body=f"Envío creado en Palletways:<br/>"
                 f"• Tracking ID: {tracking_id}<br/>"
                 f"• Response ID: {response_id}<br/>"
                 f"• Servicio: {self.palletways_service_code}<br/>"
                 f"• Peso: {shipment_data.get('weight')}kg"
        )
        
        return tracking_id
    
    def palletways_send_shipping(self, pickings):
        """Crear envío en Palletways - MÉTODO PRINCIPAL"""
        res = []
        
        for picking in pickings:
            try:
                # LOGS TEMPORALES PARA DIAGNÓSTICO
                _logger.info(f"CARRIER ID: {picking.carrier_id}")
                _logger.info(f"CARRIER DELIVERY TYPE: {picking.carrier_id.delivery_type}")
                
                # Forzar recarga del transportista con todos los campos
                carrier = self.env['delivery.carrier'].browse(picking.carrier_id.id)
                _logger.info(f"PALLETWAYS API CLIENT: {carrier.palletways_api_client_id}")
                _logger.info(f"API CLIENT TEST MODE: {carrier.palletways_api_client_id.test_mode if carrier.palletways_api_client_id else 'NO CLIENT'}")
                
                # Verificar configuración
                if not self.palletways_api_client_id:
                    raise UserError("No hay cliente API Palletways configurado para este transportista")
                
                # Validaciones previas
                self._validate_palletways_picking(picking)
                
                # Preparar datos del envío
                shipment_data = self._prepare_palletways_shipment_data(picking)
                
                # Crear envío via API usando método real
                api_response = self.palletways_api_client_id.create_consignment(shipment_data)
                
                # Procesar respuesta
                if self._is_successful_response(api_response):
                    tracking_id = self._process_successful_shipment(picking, api_response, shipment_data)
                    
                    res.append({
                        'exact_price': 0.0,  # Palletways no retorna precio en creación
                        'tracking_number': tracking_id
                    })
                    
                    _logger.info(f"Envío Palletways creado: {tracking_id} para {picking.name}")
                    
                else:
                    error_msg = self._extract_error_message(api_response)
                    raise UserError(f"Error Palletways: {error_msg}")
                    
            except Exception as e:
                _logger.error(f"Error enviando a Palletways picking {picking.name}: {e}")
                raise UserError(f"Error creando envío Palletways: {e}")
        
        return res

    def palletways_get_tracking_link(self, picking):
        """Obtener enlace de seguimiento"""
        if not picking.carrier_tracking_ref:
            return ""
        
        # Extraer tracking ID real si es formato temporal
        tracking_id = picking.carrier_tracking_ref
        if tracking_id.startswith('PW-'):
            # Buscar el tracking ID real en el shipment
            shipment = self.env['palletways.shipment'].search([
                ('picking_id', '=', picking.id)
            ], limit=1)
            if shipment and shipment.tracking_id != tracking_id:
                tracking_id = shipment.tracking_id
        
        return f"https://track2.palletways.com/?dc_syscon={tracking_id}"

    def palletways_cancel_shipment(self, picking):
        """Cancelar envío - Palletways no proporciona API de cancelación"""
        raise UserError(
            "No se puede cancelar el envío automáticamente.\n"
            "Palletways no proporciona API de cancelación.\n"
            "Contacte directamente con su depot de Palletways."
        )

    # MÉTODOS LEGACY PARA COMPATIBILIDAD
    def palletways_shipping_request_data(self, picking, consignment_number):
        """Construir datos de envío según especificación oficial de Palletways"""

        # Validar servicio
        if not self.palletways_api_client_id.validate_service_code(self.palletways_service_code):
            raise UserError(f"Código de servicio inválido: {self.palletways_service_code}")

        # Determinar tipo de consignación según documentación
        consignment_type = '3'  # Third party por defecto
        if hasattr(self, 'palletways_consignment_type'):
            consignment_type = self.palletways_consignment_type

        shipment_data = {
            'type': consignment_type,
            'import_id': consignment_number,
            'reference': picking.name,
            'client_reference': picking.origin or picking.name,
            'pallets': self._calculate_pallets(picking),
            'weight': self._calculate_weight(picking),
            'handball': self.palletways_handball,
            'taillift': self.palletways_taillift,
            'classification': 'B2B',  # Por defecto B2B
            'book_in_request': self.palletways_book_in_request,
            'manifest_note': self.palletways_manifest_note or '',
            'collection_date': fields.Date.today().strftime('%Y-%m-%d'),
            'delivery_date': self._calculate_delivery_date(picking),
            'service_code': self.palletways_service_code,
            'surcharge_code': self.palletways_surcharge_code or self.palletways_service_code,
            'bill_unit_type': self.palletways_bill_unit_type or 'FP',
            'bill_unit_amount': 1,
            'collection_address': picking.picking_type_id.warehouse_id.partner_id,
            'delivery_address': picking.partner_id,
        }

        # Añadir datos de cita si es necesaria
        if self.palletways_book_in_request:
            shipment_data.update({
                'contact_name': picking.partner_id.name,
                'contact_phone': picking.partner_id.phone or picking.partner_id.mobile,
                'contact_note': 'Llamar antes de la entrega',
                'instructions': self.palletways_manifest_note or 'Cita previa requerida'
            })

        # Añadir notificaciones si están configuradas
        if picking.partner_id.email:
            shipment_data['notification_emails'] = [picking.partner_id.email]

        return shipment_data
    
    @api.model
    def palletways_send_shipping_legacy(self, pickings):
        """DEPRECATED: Usar palletways_send_shipping"""
        _logger.warning("Método palletways_send_shipping_legacy está deprecated")
        return self.palletways_send_shipping(pickings)

    def _palletways_send_shipping(self, pickings):
        """Método alternativo que Odoo puede buscar"""
        return self.palletways_send_shipping(pickings)
