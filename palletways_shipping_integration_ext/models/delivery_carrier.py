# -*- coding: utf-8 -*-
import json
import math
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    # Mapeo de cada categoría a un bill.unit existente
    palletways_bill_full_id = fields.Many2one('bill.unit', string="Bill Unit - Full pallet")
    palletways_bill_light_id = fields.Many2one('bill.unit', string="Bill Unit - Light pallet")
    palletways_bill_half_id = fields.Many2one('bill.unit', string="Bill Unit - Half pallet")
    palletways_bill_extra_light_id = fields.Many2one('bill.unit', string="Bill Unit - Extra light pallet")
    palletways_bill_quarter_id = fields.Many2one('bill.unit', string="Bill Unit - Quarter pallet")
    palletways_bill_mini_quarter_id = fields.Many2one('bill.unit', string="Bill Unit - Mini quarter pallet")

    # Umbrales (kg) por Bill Unit
    palletways_full_max = fields.Float(string="Full max (kg)", default=1200.0)
    palletways_light_max = fields.Float(string="Light max (kg)", default=750.0)
    palletways_half_max = fields.Float(string="Half max (kg)", default=600.0)
    palletways_extra_light_max = fields.Float(string="Extra light max (kg)", default=450.0)
    palletways_quarter_max = fields.Float(string="Quarter max (kg)", default=300.0)
    palletways_mini_quarter_max = fields.Float(string="Mini quarter max (kg)", default=150.0)

    def _get_picking_weight(self, picking):
        # Usa shipping_weight si está; si no, calcula por líneas
        weight = float(getattr(picking, 'shipping_weight', 0.0) or 0.0)
        if weight > 0:
            return weight
        total = 0.0
        for mv in picking.move_ids_without_package:
            if mv.product_uom_qty and mv.product_id and mv.product_id.weight:
                total += mv.product_uom_qty * mv.product_id.weight
        return total

    def _compute_bill_units_by_weight(self, total_weight_kg):
        """
        Agrupa por “mini” de 150kg (1 mini = 150kg) y factoriza:
        full=8, light=5, half=4, extra_light=3, quarter=2, mini_quarter=1
        Devuelve dict con cantidades por categoría.
        """
        if total_weight_kg <= 0:
            return {}
        mini_unit = self.palletways_mini_quarter_max or 150.0
        mini = int(math.ceil(total_weight_kg / mini_unit))
        counts = {'full': 0, 'light': 0, 'half': 0, 'extra_light': 0, 'quarter': 0, 'mini_quarter': 0}
        table = [('full', 8), ('light', 5), ('half', 4), ('extra_light', 3), ('quarter', 2), ('mini_quarter', 1)]
        for name, factor in table:
            n, mini = divmod(mini, factor)
            counts[name] = n
        return counts

    def _bill_unit_payload_from_counts(self, counts):
        """
        Devuelve [{"Type": <bill_unit_key>, "Amount": "<n>"}] según el mapeo configurado.
        """
        mapping = {
            'full': self.palletways_bill_full_id,
            'light': self.palletways_bill_light_id,
            'half': self.palletways_bill_half_id,
            'extra_light': self.palletways_bill_extra_light_id,
            'quarter': self.palletways_bill_quarter_id,
            'mini_quarter': self.palletways_bill_mini_quarter_id,
        }
        result = []
        for key, rec in mapping.items():
            n = counts.get(key, 0) or 0
            if n:
                if not rec or not rec.bill_unit_key:
                    raise ValidationError(_("Configure the Bill Unit mapping for '%s' on the Palletways carrier.") % key)
                result.append({"Type": rec.bill_unit_key, "Amount": str(int(n))})
        return result

    def palletways_shipping_request_data(self, picking, consignment_number):
        """
        Override del método del conector:
        - Inyecta Depot/Account (para Depot API key)
        - Calcula Bill Units por peso del picking
        """
        receiver_address = picking.partner_id
        sender_address = picking.picking_type_id.warehouse_id.partner_id

        if not sender_address.name or not sender_address.zip or not sender_address.city or not sender_address.country_id:
            raise ValidationError(_("Please Define Proper Sender Address like name,zip,city,country!"))
        if not receiver_address.name or not receiver_address.zip or not receiver_address.city or not receiver_address.country_id:
            raise ValidationError(_("Please Define Proper Recipient Address like name,zip,city,country!"))

        total_weight = self._get_picking_weight(picking)
        if total_weight < 1.0:
            raise ValidationError(_("Shipment weight less than 1 is not allowed"))

        counts = self._compute_bill_units_by_weight(total_weight)
        bill_unit_ls = self._bill_unit_payload_from_counts(counts)
        if not bill_unit_ls:
            raise ValidationError(_("No Bill Units could be computed. Check weight and Bill Unit mapping."))

        # Fechas/hora
        today = fields.Date.context_today(self)
        # str(today) -> 'YYYY-MM-DD'
        time_str = fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime("%H-%M-%S")

        payload = {
            "Manifest": {
                "Date": str(today),
                "Time": time_str,
                "Confirm": "yes",
                "Depot": {
                    "Code": self.company_id.palletways_depot_code or "",
                    "Account": {
                        "Code": self.company_id.palletways_account_code or "",
                        "Consignment": {
                            "Type": "D",
                            "ImportID": picking.origin or '',
                            "Number": consignment_number,
                            "Reference": picking.name or '',
                            "Lifts": getattr(picking, 'number_of_lifts', "") or '',
                            "Weight": str(int(total_weight)) or "0",
                            "Handball": "",
                            "TailLift": bool(getattr(self, 'tail_lift', False)),
                            "Insurance": "",
                            "BookInRequest": "",
                            "BookInInstructions": "",
                            "ManifestNote": "",
                            "CollectionDate": picking.scheduled_date.strftime("%Y-%m-%d") if picking.scheduled_date else str(today),
                            "DeliveryDate": "",
                            "DeliveryTime": "",
                            "Service": {
                                "Type": "delivery",
                                "Code": picking.sale_id and picking.sale_id.palletways_service_id and picking.sale_id.palletways_service_id.service_group_code or '',
                                "Surcharge": picking.sale_id and picking.sale_id.palletways_service_id and picking.sale_id.palletways_service_id.service_code or ''
                            },
                            "Address": {
                                "Type": "Delivery",
                                "ContactName": receiver_address.name or '',
                                "Telephone": receiver_address.phone or '',
                                "Fax": "",
                                "CompanyName": receiver_address.parent_id.name if receiver_address.parent_id else receiver_address.name,
                                "Line": receiver_address.street or '',
                                "Town": receiver_address.city or '',
                                "County": receiver_address.state_id and receiver_address.state_id.name or '',
                                "PostCode": receiver_address.zip or '',
                                "Country": receiver_address.country_id and receiver_address.country_id.code
                            },
                            "BillUnit": bill_unit_ls,
                        }
                    }
                }
            }
        }
        return json.dumps(payload)
