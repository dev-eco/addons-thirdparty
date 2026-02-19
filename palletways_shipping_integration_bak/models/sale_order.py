# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from requests import request
from odoo.addons.palletways_shipping_integration.models.palletways_response import Response
import logging

_logger = logging.getLogger("palletways")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    palletways_service_ids = fields.One2many("palletways.service", "sale_order_id", string="Available Services")
    palletways_service_id = fields.Many2one("palletways.service", string="Palletways Service",
                                            help="palletways service", copy=False)

    def get_service(self):
        order = self
        recipient_address = order.partner_shipping_id
        sender_address = order.warehouse_id.partner_id if order.warehouse_id else order.company_id.partner_id

        if not sender_address.zip or not sender_address.country_id:
            raise ValidationError(_("For Get Service Sender Zip Code and Country Is Required Please Enter Zip Code and Country OF Sender"))
        if not recipient_address.zip or not recipient_address.country_id:
            raise ValidationError(_("For Get Service Receiver Zip Code and Country Is Required Please Enter Zip Code and Country OF Receiver"))

        base = (self.company_id.palletways_api_url or "").rstrip('/')
        if not base:
            raise ValidationError(_("Palletways API URL no configurada en la Compañía."))
        if not self.company_id.palletways_api_key:
            raise ValidationError(_("Palletways API Key no configurada en la Compañía."))

        api_url = "{0}/availableServices/D/{1}/{2}/{3}/{4}?apikey={5}".format(
            base,
            sender_address.country_id.code,
            sender_address.zip,
            recipient_address.country_id.code,
            recipient_address.zip,
            self.company_id.palletways_api_key)

        # 1) Intento POST (comportamiento actual), fallback a GET si falla
        try:
            response_data = request(method='POST', url=api_url, timeout=30)
        except Exception as e:
            _logger.warning("POST availableServices falló: %s", e)
            response_data = None

        if not response_data or response_data.status_code not in (200, 201):
            try:
                response_data = request(method='GET', url=api_url, timeout=30)
            except Exception as e:
                raise ValidationError(_("Error de comunicación con Palletways (availableServices): %s") % e)

        _logger.info("availableServices (%s): %s", response_data.status_code, response_data.text[:2000])

        # 2) Parseo robusto: JSON -> dict; si no, XML -> dict
        try:
            if 'application/json' in (response_data.headers.get('Content-Type') or '').lower() or response_data.text.strip().startswith('{'):
                results = response_data.json()
            else:
                api = Response(response_data)
                results = api.dict()
        except Exception:
            api = Response(response_data)
            results = api.dict()

        # 3) Verificación de estado y extracción de servicios
        resp_root = results.get('Response', results) if isinstance(results, dict) else {}
        status = resp_root.get('Status', {}) if isinstance(resp_root, dict) else {}
        code = status.get('Code')
        if code and code != 'OK':
            raise ValidationError(str(results))

        detail = resp_root.get('Detail', {}) if isinstance(resp_root, dict) else {}
        available_services = detail.get('Data') if isinstance(detail, dict) else None
        if isinstance(available_services, dict):
            available_services = [available_services]

        if not available_services:
            # si la estructura difiere, devolvemos el dict para inspección
            raise ValidationError(_("Respuesta de servicios inesperada: %s") % str(results)[:1000])

        palletways_services = self.env['palletways.service']
        existing_records = palletways_services.search([('sale_order_id', '=', order.id)])
        existing_records.sudo().unlink()

        for service in available_services:
            if not isinstance(service, dict):
                continue
            palletways_services.sudo().create({
                'service_group_code': "%s" % service.get('ServiceGroupCode'),
                'service_code': "%s" % service.get('ServiceCode'),
                'service_name': service.get('ServiceName'),
                'service_group_name': service.get('ServiceGroupName'),
                'service_days_min': service.get('ServiceDaysMin'),
                'service_days_max': service.get('ServiceDaysMax'),
                'sale_order_id': self.id
            })