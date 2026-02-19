from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    dist_is_managed = fields.Boolean(
        string="Envío gestionado por distribuidor",
        compute="_compute_dist_is_managed",
    )
    dist_carrier_name = fields.Char("Transportista (nombre)")
    dist_carrier_account = fields.Char("Nº de cuenta transportista")
    dist_pickup_datetime = fields.Datetime("Fecha/hora de recogida")
    dist_pickup_slot = fields.Selection(
        [("morning", "Mañana"), ("afternoon", "Tarde")],
        string="Franja de recogida",
    )
    dist_label_attachment_id = fields.Many2one("ir.attachment", string="Etiqueta del distribuidor")
    dist_packing_slip_attachment_id = fields.Many2one("ir.attachment", string="Albarán del distribuidor")

    @api.depends("carrier_id")
    def _compute_dist_is_managed(self):
        Param = self.env["ir.config_parameter"].sudo()
        carrier_id = int(Param.get_param("website_dist_checkout.carrier_id", default="0") or 0)
        for so in self:
            so.dist_is_managed = bool(carrier_id) and so.carrier_id and so.carrier_id.id == carrier_id

    def action_confirm(self):
        res = super().action_confirm()
        self._propagate_dist_fields_to_pickings()
        return res

    def _propagate_dist_fields_to_pickings(self):
        for so in self:
            if not so.dist_is_managed:
                continue
            for picking in so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing"):
                vals = {
                    "dist_carrier_name": so.dist_carrier_name,
                    "dist_carrier_account": so.dist_carrier_account,
                    "dist_pickup_datetime": so.dist_pickup_datetime,
                    "dist_pickup_slot": so.dist_pickup_slot,
                }
                if so.dist_label_attachment_id and not picking.dist_label_attachment_id:
                    vals["dist_label_attachment_id"] = so._copy_attachment_to_picking(
                        so.dist_label_attachment_id, picking
                    ).id
                if so.dist_packing_slip_attachment_id and not picking.dist_packing_slip_attachment_id:
                    vals["dist_packing_slip_attachment_id"] = so._copy_attachment_to_picking(
                        so.dist_packing_slip_attachment_id, picking
                    ).id
                picking.write(vals)

    def _copy_attachment_to_picking(self, attachment, picking):
        return attachment.copy({
            "res_model": "stock.picking",
            "res_id": picking.id,
            "name": attachment.name,
        })