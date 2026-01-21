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
