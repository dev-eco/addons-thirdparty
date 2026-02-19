from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # CAMBIO: Hacer el campo relacionado más robusto
    delivery_type = fields.Char(
        string='Tipo de Entrega',
        compute='_compute_delivery_type',
        readonly=True,
        store=False
    )

    # Campos relacionados con Palletways
    palletways_shipment_id = fields.Many2one('palletways.shipment', 
                                           string='Envío Palletways',
                                           readonly=True)
    palletways_tracking_id = fields.Char(related='palletways_shipment_id.tracking_id',
                                       string='Tracking ID Palletways',
                                       readonly=True)
    palletways_status = fields.Selection(related='palletways_shipment_id.status',
                                       string='Estado Palletways',
                                       readonly=True)

    palletways_shipment_count = fields.Integer(
        string='Número de Envíos Palletways',
        compute='_compute_palletways_shipment_count'
    )

    palletways_tracking_url = fields.Char(
        string='URL Seguimiento',
        compute='_compute_palletways_tracking_url'
    )

    def _compute_delivery_type(self):
        """Calcular tipo de entrega de forma segura sin @depends problemático"""
        for picking in self:
            try:
                # Verificar si el campo carrier_id existe y tiene valor
                if hasattr(picking, 'carrier_id') and picking.carrier_id:
                    picking.delivery_type = picking.carrier_id.delivery_type or False
                else:
                    picking.delivery_type = False
            except Exception as e:
                _logger.warning(f"Error calculando delivery_type para picking {picking.id}: {e}")
                picking.delivery_type = False

    @api.depends('palletways_shipment_id')
    def _compute_palletways_shipment_count(self):
        for picking in self:
            picking.palletways_shipment_count = 1 if picking.palletways_shipment_id else 0

    @api.depends('palletways_tracking_id')
    def _compute_palletways_tracking_url(self):
        for picking in self:
            if picking.palletways_tracking_id:
                picking.palletways_tracking_url = f"https://track2.palletways.com/?dc_syscon={picking.palletways_tracking_id}"
            else:
                picking.palletways_tracking_url = False

    def button_validate(self):
        """
        ✅ CORRECCIÓN v2.1.8: Capturar excepción correctamente con 'as e'
        
        El método palletways_send_shipping() devuelve una LISTA de diccionarios:
        [
            {
                'exact_price': float,
                'tracking_number': str,
                'labels': [],  # Vacío - se descargan después con botón
            }
        ]
        
        Se llama automáticamente al validar albaranes con transportista Palletways
        """
        _logger.info(f"button_validate() iniciado para {self.name}")
        
        # Verificar si este picking tiene transportista Palletways
        if self.carrier_id and self.carrier_id.delivery_type == 'palletways':
            _logger.info(f"Picking {self.name} usa transportista Palletways")
            
            try:
                # Llamar al método de envío de Palletways ANTES de validar
                _logger.info(f"Llamando a palletways_send_shipping() para {self.name}")
                
                # ✅ CORRECCIÓN v2.1.8: El método devuelve una LISTA de diccionarios
                results = self.carrier_id.palletways_send_shipping([self])
                
                # ✅ CORRECCIÓN v2.1.8: Verificar que results sea una lista
                if not results:
                    raise UserError("Error: palletways_send_shipping() devolvió lista vacía")
                
                if not isinstance(results, list):
                    _logger.error(f"Error: results no es lista, es {type(results)}: {results}")
                    raise UserError(f"Error: palletways_send_shipping() devolvió tipo inválido: {type(results)}")
                
                # ✅ CORRECCIÓN v2.1.8: Tomar el primer resultado
                result = results[0]
                _logger.info(f"Resultado recibido: {result}")
                
                # ✅ CORRECCIÓN v2.1.8: Verificar estructura del resultado
                if not isinstance(result, dict):
                    _logger.error(f"Error: result no es dict, es {type(result)}: {result}")
                    raise UserError(f"Error: Resultado inesperado de palletways_send_shipping(): {type(result)}")
                
                # ✅ CORRECCIÓN v2.1.8: Verificar tracking_number
                tracking_number = result.get('tracking_number')
                if not tracking_number:
                    _logger.error(f"Error: No hay tracking_number en resultado: {result}")
                    raise UserError("Error: No se recibió tracking_number del envío Palletways")
                
                _logger.info(f"✓ Envío Palletways creado exitosamente: {tracking_number}")
                
                # ✅ CORRECCIÓN v2.1.8: Mensaje de éxito en picking
                self.message_post(
                    body=f"✅ Envío Palletways creado exitosamente<br/>"
                         f"<strong>Tracking ID:</strong> {tracking_number}",
                    message_type='comment'
                )
                
            except UserError as e:
                # ✅ CORRECCIÓN CRÍTICA v2.1.8: Capturar excepción con 'as e'
                # Re-lanzar errores de usuario
                _logger.error(f"Error de usuario en button_validate: {str(e)}")
                raise
                
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                _logger.error(f"✗ Error inesperado para {self.name}: {error_msg}", exc_info=True)
                self.message_post(
                    body=f"❌ Error inesperado creando envío:<br/>{error_msg}",
                    message_type='comment'
                )
                raise UserError(error_msg)
        else:
            _logger.info(f"Picking {self.name} no usa Palletways, continuando validación normal")
        
        # Llamar al método original de validación
        _logger.info(f"Llamando a super().button_validate() para {self.name}")
        return super().button_validate()

    def action_palletways_track(self):
        """Abrir seguimiento de Palletways"""
        self.ensure_one()
        if not self.palletways_tracking_url:
            raise UserError("No hay tracking ID de Palletways para este albarán")

        return {
            'type': 'ir.actions.act_url',
            'url': self.palletways_tracking_url,
            'target': 'new',
        }

    def action_palletways_update_status(self):
        """Actualizar estado desde Palletways"""
        self.ensure_one()
        if self.palletways_shipment_id:
            return self.palletways_shipment_id.action_update_status()
        else:
            raise UserError("No hay envío de Palletways asociado a este albarán")

    def action_open_palletways_shipment(self):
        """Abrir formulario del envío Palletways"""
        self.ensure_one()
        if not self.palletways_shipment_id:
            raise UserError("No hay envío de Palletways asociado a este albarán")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'palletways.shipment',
            'res_id': self.palletways_shipment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
