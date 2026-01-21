import json
import base64
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PalletwaysShipment(models.Model):
    _name = 'palletways.shipment'
    _description = 'Envío Palletways'
    _order = 'create_date desc'
    _rec_name = 'tracking_id'
    
    # Identificadores
    tracking_id = fields.Char('Tracking ID', required=True, index=True)
    picking_id = fields.Many2one('stock.picking', string='Albarán', 
                                required=True, ondelete='cascade')
    response_id = fields.Char('Response ID', index=True)
    consignment_number = fields.Char('Número Consignación')
    
    # Estado
    status = fields.Selection([
        ('created', 'Creado'),
        ('confirmed', 'Confirmado'),
        ('collected', 'Recogido'),
        ('in_transit', 'En Tránsito'), 
        ('at_depot', 'En Depot'),
        ('out_delivery', 'En Reparto'),
        ('delivered', 'Entregado'),
        ('error', 'Error'),
    ], string='Estado', default='created', index=True)
    
    # Información del servicio
    service_code = fields.Char('Código Servicio')
    service_name = fields.Char('Nombre Servicio', compute='_compute_service_name')
    
    # Datos del envío
    weight = fields.Float('Peso (kg)')
    pallets = fields.Integer('Pallets')
    bill_unit_type = fields.Char('Tipo Unidad Facturable')
    
    # Respuestas API
    api_response = fields.Text('Respuesta API Creación')
    last_status_response = fields.Text('Última Respuesta Estado')
    notes = fields.Text('Notas')
    
    # Archivos
    label_pdf = fields.Binary('Etiqueta PDF')
    label_filename = fields.Char('Nombre Etiqueta', compute='_compute_filenames')
    pod_pdf = fields.Binary('Comprobante Entrega')
    pod_filename = fields.Char('Nombre POD', compute='_compute_filenames')
    
    # Estados detallados Palletways
    palletways_status_code = fields.Char('Código Estado PW')
    palletways_status_desc = fields.Char('Descripción Estado PW')
    last_update = fields.Datetime('Última Actualización')
    
    # Información adicional
    collection_date = fields.Date('Fecha Recogida')
    delivery_date = fields.Date('Fecha Entrega')
    actual_delivery_date = fields.Datetime('Fecha Entrega Real')
    
    # Relaciones
    company_id = fields.Many2one('res.company', related='picking_id.company_id', store=True)
    partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', store=True)
    
    @api.depends('service_code')
    def _compute_service_name(self):
        for record in self:
            if record.picking_id and record.picking_id.carrier_id and record.picking_id.carrier_id.palletways_api_client_id:
                client = record.picking_id.carrier_id.palletways_api_client_id
                record.service_name = client.get_service_description(record.service_code)
            else:
                # Fallback a nombres básicos según documentación oficial página 6
                service_names = {
                    # Servicios según documentación web oficial
                    'A': 'Next Day Standard',
                    'B': 'Economy',
                    'C': 'Collection - Premium',
                    'D': 'Collection - Economy',
                    'DH': 'Premium Timed Delivery PM (Pre-Booked)',
                    'E': 'Next Day AM',
                    'F': 'Saturday AM',
                    'H': 'Timed Delivery (Pre-Booked)',
                    'I': 'Remote Contract Collection',
                    'J': 'Economy A.M',
                    'K': 'Economy Timed',
                    'L': '3 Day Service',
                    'N': 'Collection 3 Day',
                    'O': 'Premium 48',
                    'P': 'Collection 5 Day',
                    'V': 'Collection Premium 48hr',
                    'X': 'Collection 4 Day',
                    'Z': 'Saturday Economy A.M',
                    '0': 'Europe Collect Premium',
                    '1': 'Europe Saturday Premium',
                    '2': 'Europe 2 Day Premium',
                    '3': 'Europe 3 Day Premium',
                    '4': 'Europe 4+ Day Premium',
                    '5': 'Europe 5 Day Economy',
                    '6': 'Europe 3 Day Economy',
                    '7': 'Europe 4 Day Economy',
                    '8': 'Europe Collect Economy',
                    '9': 'Europe Timed (Pre-Booked)',
                }
                record.service_name = service_names.get(record.service_code, record.service_code or '')
    
    @api.depends('tracking_id')
    def _compute_filenames(self):
        for record in self:
            if record.tracking_id:
                safe_tracking = record.tracking_id.replace('/', '_').replace('\\', '_')
                record.label_filename = f'etiqueta_{safe_tracking}.pdf'
                record.pod_filename = f'pod_{safe_tracking}.pdf'
            else:
                record.label_filename = 'etiqueta.pdf'
                record.pod_filename = 'pod.pdf'
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.tracking_id} - {record.partner_id.name}"
            result.append((record.id, name))
        return result
    
    def action_update_status(self):
        """Actualizar estado desde Palletways"""
        updated_count = 0
        error_count = 0
        
        for shipment in self:
            try:
                # Verificar si es un envío TEST
                if shipment.tracking_id.startswith('TEST-'):
                    # Para envíos TEST, simular actualización de estado
                    shipment._simulate_test_status_update()
                    updated_count += 1
                    continue
                
                client = shipment._get_api_client()
                status_data = client.get_consignment_status(shipment.tracking_id)
                shipment._update_status_from_api(status_data)
                updated_count += 1
                
            except Exception as e:
                error_count += 1
                _logger.error(f"Error actualizando estado {shipment.tracking_id}: {e}")
                shipment.message_post(
                    body=f"Error actualizando estado: {e}",
                    message_type='comment'
                )
        
        # Mensaje personalizado según resultados
        if error_count == 0:
            message = f'Todos los estados actualizados correctamente ({updated_count})'
            msg_type = 'success'
        elif updated_count > 0:
            message = f'{updated_count} estados actualizados, {error_count} errores'
            msg_type = 'warning'
        else:
            message = f'Error actualizando todos los estados ({error_count} errores)'
            msg_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': msg_type,
            }
        }
    
    def _update_status_from_api(self, api_data):
        """Actualizar estado local desde respuesta API"""
        if not api_data or not api_data.get('Status', {}).get('Code') == 'OK':
            return
        
        detail = api_data.get('Detail', {}).get('Data', {})
        if isinstance(detail, list):
            detail = detail[0] if detail else {}
        
        # Mapear códigos de estado Palletways según documentación oficial página 14
        status_mapping = {
            # Estados de recogida
            '15': 'error',        # REJECTED - Petición de recogida rechazada
            '25': 'created',      # TO REQUEST - Petición de recogida a ser solicitada
            '30': 'created',      # AWAITING ACCEPT - Petición de recogida esperando aceptación
            '50': 'confirmed',    # REQUESTED - Petición de recogida aceptada
            
            # Estados de procesamiento
            '100': 'confirmed',   # NOT BARCODED - Sin código de barras
            '300': 'collected',   # IN COLLECTION DEPOT - En Depot de recogida
            '350': 'in_transit',  # TRUNKED TO HUB - De camino al HUB
            '500': 'in_transit',  # AT THE HUB - En HUB
            '525': 'in_transit',  # AT INTERNATIONAL HUB - En HUB internacional
            '530': 'in_transit',  # DEPART INTERNATIONAL HUB - Salió del HUB internacional
            '550': 'in_transit',  # DEPARTED HUB - Salió del HUB
            
            # Estados de entrega
            '675': 'at_depot',    # STOCK HELD - Bloqueado en destino
            '700': 'at_depot',    # AT DELIVERY DEPOT - En Depot de entrega
            '800': 'out_delivery', # OUT FOR DELIVERY - En reparto
            '900': 'delivered',   # JOB COMPLETE - Trabajo finalizado
        }
        
        pw_status = str(detail.get('StatusCode', ''))
        new_status = status_mapping.get(pw_status, self.status)
        
        # Datos adicionales
        update_vals = {
            'status': new_status,
            'palletways_status_code': pw_status,
            'palletways_status_desc': detail.get('StatusDescription', ''),
            'last_update': fields.Datetime.now(),
            'last_status_response': json.dumps(api_data),
        }
        
        # Actualizar número de consignación si viene
        if detail.get('ConNo'):
            update_vals['consignment_number'] = detail.get('ConNo')
        
        # Fecha de entrega real si está entregado
        if new_status == 'delivered' and detail.get('DeliveryDate'):
            try:
                delivery_datetime = datetime.strptime(
                    f"{detail.get('DeliveryDate')} {detail.get('DeliveryTime', '00:00')}",
                    '%Y-%m-%d %H:%M'
                )
                update_vals['actual_delivery_date'] = delivery_datetime
            except (ValueError, TypeError):
                pass
        
        self.write(update_vals)
        
        # Mensaje en picking si hay cambio de estado
        if new_status != self.status:
            status_names = dict(self._fields['status'].selection)
            self.picking_id.message_post(
                body=f"Estado Palletways actualizado: {status_names.get(new_status, new_status)}<br/>"
                     f"Código PW: {pw_status} - {detail.get('StatusDescription', '')}"
            )
    
    def action_download_labels(self):
        """Descargar etiquetas PDF"""
        self.ensure_one()
        
        # Verificar si es un envío TEST
        if self.tracking_id.startswith('TEST-'):
            raise UserError(
                "No se pueden descargar etiquetas de envíos TEST.\n"
                "Las etiquetas solo están disponibles para envíos reales creados en producción.\n"
                "Configure su API Key con permisos de creación y desactive el modo test."
            )
        
        try:
            client = self._get_api_client()
            pdf_data = client.get_labels(self.tracking_id)
            
            self.write({
                'label_pdf': base64.b64encode(pdf_data),
            })
            
            self.message_post(
                body="Etiquetas descargadas correctamente",
                message_type='comment'
            )
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/palletways.shipment/{self.id}/label_pdf/{self.label_filename}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error descargando etiquetas {self.tracking_id}: {e}")
            raise UserError(f"Error descargando etiquetas: {e}")
    
    def action_download_pod(self):
        """Descargar comprobante de entrega"""
        self.ensure_one()
        
        # Verificar si es un envío TEST
        if self.tracking_id.startswith('TEST-'):
            raise UserError(
                "No se pueden descargar PODs de envíos TEST.\n"
                "Los comprobantes solo están disponibles para envíos reales entregados.\n"
                "Configure su API Key con permisos de creación y desactive el modo test."
            )
        
        if self.status != 'delivered':
            raise UserError("El comprobante de entrega solo está disponible cuando el envío ha sido entregado")
        
        try:
            client = self._get_api_client()
            pod_data = client.get_pod(self.tracking_id)
            
            self.write({
                'pod_pdf': base64.b64encode(pod_data),
            })
            
            self.message_post(
                body="Comprobante de entrega descargado correctamente",
                message_type='comment'
            )
            
            return {
                'type': 'ir.actions.act_url', 
                'url': f'/web/content/palletways.shipment/{self.id}/pod_pdf/{self.pod_filename}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error descargando POD {self.tracking_id}: {e}")
            raise UserError(f"Error descargando POD: {e}")
    
    def action_get_tracking_link(self):
        """Abrir enlace de seguimiento"""
        self.ensure_one()
        
        url = f"https://track2.palletways.com/?dc_syscon={self.tracking_id}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
    
    def _get_api_client(self):
        """Obtener cliente API configurado"""
        carrier = self.picking_id.carrier_id
        if not carrier or carrier.delivery_type != 'palletways':
            raise UserError("El albarán no tiene un transportista Palletways configurado")
        
        if not carrier.palletways_api_client_id:
            raise UserError("El transportista no tiene cliente API configurado")
        
        return carrier.palletways_api_client_id
    
    @api.model
    def cron_update_shipment_status(self):
        """Cron para actualizar estados automáticamente"""
        # Buscar envíos no entregados de los últimos 30 días
        domain = [
            ('status', 'not in', ['delivered', 'error']),
            ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))
        ]
        
        shipments = self.search(domain, limit=50)  # Limitar para no exceder rate limit
        
        _logger.info(f"Actualizando {len(shipments)} envíos Palletways")
        
        for shipment in shipments:
            try:
                shipment.action_update_status()
                self.env.cr.commit()  # Commit individual para evitar rollback total
            except Exception as e:
                _logger.error(f"Error en cron actualizando {shipment.tracking_id}: {e}")
                continue
        
        return True
    
    def _simulate_test_status_update(self):
        """Simular actualización de estado para envíos TEST"""
        import random
        from datetime import datetime, timedelta
        
        # Estados simulados progresivos
        test_statuses = ['created', 'confirmed', 'collected', 'in_transit', 'at_depot', 'out_delivery']
        
        # Avanzar al siguiente estado si es posible
        current_index = test_statuses.index(self.status) if self.status in test_statuses else 0
        if current_index < len(test_statuses) - 1:
            new_status = test_statuses[current_index + 1]
            
            self.write({
                'status': new_status,
                'palletways_status_code': f'TEST-{random.randint(100, 900)}',
                'palletways_status_desc': f'Estado simulado: {new_status.upper()}',
                'last_update': fields.Datetime.now(),
            })
            
            status_names = dict(self._fields['status'].selection)
            self.picking_id.message_post(
                body=f"Estado TEST actualizado: {status_names.get(new_status, new_status)}<br/>"
                     f"Nota: Este es un envío de prueba"
            )
    
    def action_get_notes(self):
        """Obtener notas del envío desde Palletways"""
        self.ensure_one()
        
        try:
            client = self._get_api_client()
            notes_data = client.get_notes(self.tracking_id)
            
            if notes_data.get('Status', {}).get('Code') == 'OK':
                detail = notes_data.get('Detail', {}).get('Data', [])
                if not isinstance(detail, list):
                    detail = [detail] if detail else []
                
                notes_text = []
                for note in detail:
                    note_date = note.get('NoteDate', '')
                    note_time = note.get('NoteTime', '')
                    note_text = note.get('NoteText', '')
                    
                    if note_text:
                        notes_text.append(f"{note_date} {note_time}: {note_text}")
                
                if notes_text:
                    self.notes = '\n'.join(notes_text)
                    self.message_post(
                        body=f"Notas actualizadas desde Palletways:\n{self.notes}",
                        message_type='comment'
                    )
                else:
                    self.message_post(
                        body="No hay notas disponibles en Palletways",
                        message_type='comment'
                    )
            else:
                raise UserError("Error obteniendo notas desde Palletways")
                
        except Exception as e:
            _logger.error(f"Error obteniendo notas {self.tracking_id}: {e}")
            raise UserError(f"Error obteniendo notas: {e}")
