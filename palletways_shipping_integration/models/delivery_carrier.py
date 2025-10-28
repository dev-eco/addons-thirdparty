# -*- coding: utf-8 -*-
import json
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

import requests
import datetime
import uuid
import logging
from urllib.parse import quote_plus

_logger = logging.getLogger("Palletways")

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.constrains('delivery_type', 'company_id', 'bill_unit_ids')
    def _check_palletways_carrier_config(self):
        for carrier in self:
            if carrier.delivery_type == 'palletways':
                if not carrier.company_id:
                    raise ValidationError(_("Select a Company on the Palletways carrier."))
                if not carrier.bill_unit_ids:
                    raise ValidationError(_("Select at least one Bill Unit on the Palletways carrier."))

    delivery_type = fields.Selection(selection_add=[("palletways", "Palletways")],
                                     ondelete={'palletways': 'set default'})
    tail_lift = fields.Boolean(string="Tail Lift?", help="if pallets need tail lift mark this as a true")
    bill_unit_ids = fields.Many2many('bill.unit', 'delivery_carrier_bill_unit_rel', 'carrier_id', 'bill_unit_id',
                                     'Bill Unit')
    notification = fields.Boolean('Notification?')

    def palletways_rate_shipment(self, orders):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def palletways_shipping_request_data(self, picking, consignment_number):
        receiver_address = picking.partner_id
        sender_address = picking.picking_type_id.warehouse_id.partner_id

        if not sender_address.name or not sender_address.zip or not sender_address.city or not sender_address.country_id:
            raise ValidationError(_("Please Define Proper Sender Address like name,zip,city,country!"))
        if not receiver_address.name or not receiver_address.zip or not receiver_address.city or not receiver_address.country_id:
            raise ValidationError(_("Please Define Proper Recipient Address like name,zip,city,country!"))

        bill_unit_ls = []
        for bill_unt in self.bill_unit_ids:
            bill_unit_ls.append({"Type": bill_unt.bill_unit_key, "Amount": "1"})

        payload = {
            "Manifest": {
                "Date": datetime.datetime.now().strftime("%Y-%m-%d"),
                # mantenemos el formato original por compatibilidad
                "Time": datetime.datetime.now().strftime("%H-%M-%S"),
                "Confirm": "yes",
                "Depot": {
                    "Account": {
                        "Consignment": {
                            "Type": "D",
                            "ImportID": picking.origin or '',
                            "Number": consignment_number,
                            "Reference": picking.name or '',
                            "Lifts": picking.number_of_lifts or '',
                            # mantenemos entero por compatibilidad
                            "Weight": str(int(picking.shipping_weight)) or 0.0,
                            "Handball": "",
                            "TailLift": self.tail_lift,
                            "Insurance": "",
                            "BookInRequest": "",
                            "BookInInstructions": "",
                            "ManifestNote": "",
                            "CollectionDate": picking.scheduled_date.strftime("%Y-%m-%d"),
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

    @api.model
    def palletways_send_shipping(self, pickings):
        for picking in pickings:
            consignment_number_local = str((uuid.uuid4().int))[:7]
            if not picking.sale_id.palletways_service_id:
                raise ValidationError(_("Please Select Any Palletways Service From Sale Order"))
            if picking.shipping_weight < 1.0:
                raise ValidationError(_("Shipment weight less than 1 is not allowed"))

            shipping_request_data = self.palletways_shipping_request_data(picking, consignment_number_local)
            _logger.info("Shipping Request Data: %s", shipping_request_data)

            base = (self.company_id.palletways_api_url or "").rstrip('/')
            if not base:
                raise ValidationError(_("Palletways API URL no configurada en la Compañía."))
            if not self.company_id.palletways_api_key:
                raise ValidationError(_("Palletways API Key no configurada en la Compañía."))

            # URL con data url-encoded (seguro y compatible)
            data_qs = quote_plus(shipping_request_data)
            api_url = f"{base}/createconsignment?apikey={self.company_id.palletways_api_key}&inputformat=json&outputformat=json&data={data_qs}&commit=true"

            # 1) Crear consignment
            try:
                # no forzamos Accept para no condicionar la negociación de contenido del servidor
                response = requests.post(api_url, timeout=30)
                _logger.info("Shipping Response (%s): %s", response.status_code, response.text[:2000])
            except Exception as e:
                raise ValidationError(_("Error de comunicación con Palletways (createconsignment): %s") % e)

            # Parseo robusto: JSON primero, fallback a XML
            try:
                response_data = response.json()
            except ValueError:
                try:
                    from odoo.addons.palletways_shipping_integration.models.palletways_response import Response as PResponse
                    response_data = PResponse(response).dict()
                except Exception:
                    raise ValidationError(_("Respuesta inesperada de Palletways (createconsignment): %s") % response.text[:1000])

            # Compat: errores
            errors = response_data.get('ValidationErrors') or (response_data.get('Response', {}).get('ValidationErrors') if isinstance(response_data.get('Response'), dict) else None)
            if errors:
                raise ValidationError(str(errors))

            # Extraer detalles
            detail_container = response_data.get('Detail') or response_data.get('Response', {}).get('Detail', {})
            response_details = None
            if isinstance(detail_container, dict):
                response_details = detail_container.get('ImportDetail') or detail_container.get('Data') or detail_container
            else:
                response_details = detail_container

            if not response_details:
                raise ValidationError(_("Respuesta inesperada (sin detalles): %s") % str(response_data)[:1000])

            if isinstance(response_details, dict):
                response_details = [response_details]

            tracking_ls = []
            con_no_from_api = None
            for rd in response_details:
                if isinstance(rd, dict):
                    if rd.get('TrackingID'):
                        tracking_ls.append(str(rd.get('TrackingID')))
                    con_no_from_api = con_no_from_api or rd.get('ConsignmentNo') or rd.get('ConNo') or rd.get('Number')

            final_con_no = con_no_from_api or consignment_number_local

            # 2) Obtener etiqueta: intentamos GET (preferido), si falla probamos POST (comportamiento original)
            label_api_url = f"{base}/getLabelsByConNo/{final_con_no}?apikey={self.company_id.palletways_api_key}"
            label_response = None
            err_get = err_post = None
            try:
                label_response = requests.get(label_api_url, headers={"Accept": "application/pdf"}, timeout=30)
                if label_response.status_code not in (200, 201) or not label_response.content:
                    raise Exception(f"GET status={label_response.status_code}")
            except Exception as e:
                err_get = e
                try:
                    label_response = requests.post(label_api_url, headers={"Accept": "application/pdf"}, timeout=30)
                    if label_response.status_code not in (200, 201) or not label_response.content:
                        raise Exception(f"POST status={label_response.status_code}")
                except Exception as e2:
                    err_post = e2

            if not label_response or not label_response.content:
                raise ValidationError(_("No se pudo obtener la etiqueta (GET: %s, POST: %s)") % (err_get, err_post))

            logmessage = _("Label Created  %s") % (picking.name)
            pickings.message_post(body=logmessage, attachments=[(f"{picking.name}.pdf", label_response.content)])

            return [{'exact_price': 0.0, 'tracking_number': ', '.join(tracking_ls)}]

    def palletways_get_tracking_link(self, picking):
        return "https://track2.palletways.com/?dc_syscon={0}".format(picking.carrier_tracking_ref)

    def palletways_cancel_shipment(self, picking):
        raise ValidationError(_("You Can Not Cancel Order!  Because Palletways Did Not Provide Cancel API"))
