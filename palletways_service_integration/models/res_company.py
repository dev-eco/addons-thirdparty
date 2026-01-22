from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Campos Palletways con valores por defecto seguros
    use_palletways_shipping_provider = fields.Boolean(
        string="¿Usar Proveedor de Envío Palletways?",
        help="Activar cuando necesite usar el proveedor de envío Palletways",
        default=False, 
        copy=False
    )
    
    palletways_api_url = fields.Char(
        string='URL API Palletways',
        default="https://api.palletways.com/",
        help="URL oficial del API de Palletways: https://api.palletways.com/"
    )
    
    palletways_api_key = fields.Char(
        string='Clave API Palletways',
        help="Clave API codificada proporcionada por Palletways"
    )

    @api.model
    def _auto_init(self):
        """Asegurar que los campos se crean correctamente"""
        try:
            result = super(ResCompany, self)._auto_init()
            _logger.info("Campos Palletways añadidos a res.company correctamente")
            return result
        except Exception as e:
            _logger.error(f"Error inicializando campos Palletways en res.company: {e}")
            raise
