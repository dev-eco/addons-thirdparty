from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    dist_carrier_name = fields.Char("Transportista (nombre)")
    dist_carrier_account = fields.Char("Nº de cuenta transportista")
    dist_pickup_datetime = fields.Datetime("Fecha/hora de recogida")
    dist_pickup_slot = fields.Selection(
        [("morning", "Mañana"), ("afternoon", "Tarde")],
        string="Franja de recogida",
    )
    dist_label_attachment_id = fields.Many2one("ir.attachment", string="Etiqueta del distribuidor")
    dist_packing_slip_attachment_id = fields.Many2one("ir.attachment", string="Albarán del distribuidor")

    def button_validate(self):
        Param = self.env["ir.config_parameter"].sudo()
        require_label = Param.get_param("website_dist_checkout.require_label") in ("1", "True", "true")
        carrier_id = int(Param.get_param("website_dist_checkout.carrier_id", default="0") or 0)
        for picking in self:
            if (
                picking.picking_type_code == "outgoing"
                and require_label
                and carrier_id
                and picking.carrier_id
                and picking.carrier_id.id == carrier_id
                and not picking.dist_label_attachment_id
            ):
                raise UserError(_("No se puede validar: falta la etiqueta del distribuidor en el albarán."))
        return super().button_validate()