from odoo import models, fields, api, _

class PalletwaysService(models.Model):
    _name = 'palletways.service'
    _description = 'Palletways Service'

    name = fields.Char(string='Nombre del servicio', required=True)
    service_code = fields.Char(string='Código del servicio', required=True)
    description = fields.Text(string='Descripción')
    active = fields.Boolean(default=True)

    # Campo necesario para compatibilidad con el módulo base
    sale_order_id = fields.Many2one("sale.order", string="Sales Order", ondelete='cascade')

    # Campos adicionales para compatibilidad
    service_group_code = fields.Char(string="Service Group Code")
    service_name = fields.Char(string="Service Name")
    service_group_name = fields.Char(string="Service Group Name")
    service_days_min = fields.Char(string="Min Days")
    service_days_max = fields.Char(string="Max Days")

    # Relación con transportistas
    carrier_ids = fields.Many2many(
        'delivery.carrier',
        relation='palletways_service_carrier_rel',
        column1='service_id',
        column2='carrier_id',
        string='Transportistas',
        help='Transportistas que ofrecen este servicio'
    )

    # Tiempos de entrega estimados
    delivery_time = fields.Integer(
        string='Tiempo de entrega (horas)',
        help='Tiempo estimado de entrega en horas'
    )

    # Información adicional
    is_express = fields.Boolean(string='Servicio Express')
    is_international = fields.Boolean(string='Servicio Internacional')

    _sql_constraints = [
        ('code_uniq', 'unique(service_code)', 'El código de servicio debe ser único')
    ]

    def set_service(self):
        """Establece este servicio en el pedido relacionado"""
        self.ensure_one()
        if self.sale_order_id:
            self.sale_order_id.write({'palletways_service_id': self.id})
        return True
