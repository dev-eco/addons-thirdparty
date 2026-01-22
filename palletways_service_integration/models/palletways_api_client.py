import requests
import json
import base64
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class PalletwaysApiClient(models.Model):
    _name = 'palletways.api.client'
    _description = 'Cliente API Palletways'
    _rec_name = 'name'
    
    name = fields.Char('Nombre', required=True)
    
    api_endpoint_type = fields.Selection([
        ('api', 'API Global (api.palletways.com) - Para cuentas CUSTOMER y DEPOT'),
        ('portal', 'Portal API (portal.palletways.com/api) - Para cuentas DEPOT (legacy)')
    ], string='Tipo de Endpoint', 
       default='api', 
       required=True,
       help='Seleccione según su preferencia:\n'
            '• API Global: Recomendado para createConsignment\n'
            '• Portal API: Para métodos legacy o si API Global falla')
    
    api_endpoint = fields.Char('URL Endpoint', 
                              compute='_compute_api_endpoint',
                              store=True,
                              help='URL completa del endpoint seleccionado')
    
    api_key = fields.Char('API Key', required=True)
    account_code = fields.Char('Código Cliente', required=True) 
    test_mode = fields.Boolean('Modo Prueba', default=True)
    company_id = fields.Many2one('res.company', string='Empresa',
                                default=lambda self: self.env.company)
    active = fields.Boolean('Activo', default=True)
    
    last_request_time = fields.Datetime('Última Petición')
    request_count = fields.Integer('Contador Peticiones')
    
    @api.depends('api_endpoint_type')
    def _compute_api_endpoint(self):
        """
        ✅ CORRECCIÓN v2.5.0:
        Calcular URL del endpoint según tipo seleccionado
        NO auto-detectar por código de cuenta - respetar selección manual
        """
        for record in self:
            # ✅ CORRECCIÓN v2.5.0: Respetar la selección manual del usuario
            # NO cambiar automáticamente según el formato del código
            
            if record.api_endpoint_type == 'portal':
                record.api_endpoint = 'https://portal.palletways.com/api/'
                _logger.info(f"Endpoint configurado: Portal API para cuenta {record.account_code}")
            else:
                record.api_endpoint = 'https://api.palletways.com/'
                _logger.info(f"Endpoint configurado: API Global para cuenta {record.account_code}")
    
    @api.constrains('api_endpoint')
    def _check_api_endpoint(self):
        for record in self:
            if not record.api_endpoint.startswith(('http://', 'https://')):
                raise ValidationError("El endpoint debe comenzar con http:// o https://")
    
    def _check_rate_limit(self):
        """Verificar límite de 100 peticiones por minuto"""
        now = fields.Datetime.now()
        
        if self.last_request_time:
            time_diff = (now - self.last_request_time).total_seconds()
            
            if time_diff >= 60:
                self.request_count = 0
            elif self.request_count >= 100:
                raise UserError(
                    "Límite de API alcanzado (100 peticiones/minuto). "
                    "Espere antes de realizar más peticiones."
                )
        
        self.write({
            'last_request_time': now,
            'request_count': self.request_count + 1
        })
    
    def _get_mapped_endpoint(self, endpoint):
        """
        ✅ CORRECCIÓN CRÍTICA v2.1.2:
        Mapear nombres de métodos según tipo de endpoint
        """
        portal_method_mapping = {
            'createConsignment': 'pc_psief',
            'createConsignmentTest': 'pc_psief_test',
            'getConsignment': 'getConsignment',
            'conStatusByTrackingId': 'conStatusByTrackingId',
            'conStatusByConNo': 'conStatusByConNo',
            'getLabelsByTID': 'getLabelsByTID',
            'getLabelsByConNo': 'getLabelsByConNo',
            'getPodByTrackingId': 'getPodByTrackingId',
            'availableServices': 'availableServices',
            'getNotes': 'getNotes',
            'getTrackingNotes': 'getTrackingNotes',
        }
        
        if self.api_endpoint_type == 'portal' and endpoint in portal_method_mapping:
            mapped = portal_method_mapping[endpoint]
            _logger.info(f"Portal API: Mapeando método '{endpoint}' → '{mapped}'")
            return mapped
        
        return endpoint
    
    def _make_api_request(self, method, endpoint, data=None, params=None, timeout=30, _retry_with_portal=True):
        """
        ✅ CORRECCIÓN v2.5.0:
        Realizar petición HTTP a la API de Palletways
        Respetar configuración del usuario - NO forzar cambio de endpoint
        """
        self._check_rate_limit()
        
        mapped_endpoint = self._get_mapped_endpoint(endpoint)
        
        # ✅ CORRECCIÓN v2.5.0: Respetar configuración del usuario
        # NO forzar Portal automáticamente
        use_portal = (self.api_endpoint_type == 'portal')
        
        # Lista de métodos que SOLO funcionan en Portal API
        portal_exclusive_methods = [
            'version',
            'keytest',
            'pc_psief',
            'pc_psief_test',
            'pc_confirm',
            'outstandingCons',
            'palletconnect',
            'consEntered',
            'customer_invoice_detail',
            'customer_invoice_pdf',
            'customer_invoices',
        ]
        
        endpoint_lower = mapped_endpoint.lower()
        
        # Solo advertir si se intenta usar método exclusivo de Portal con API2
        if not use_portal:
            for portal_method in portal_exclusive_methods:
                if portal_method.lower() in endpoint_lower:
                    _logger.warning(
                        f"⚠️ ADVERTENCIA: Método '{mapped_endpoint}' puede requerir Portal API. "
                        f"Si falla, cambie 'Tipo de Endpoint' a 'Portal API'"
                    )
                    break
        
        if use_portal:
            base_url = 'https://portal.palletways.com/api/'
        else:
            base_url = 'https://api.palletways.com/'
        
        url = f"{base_url.rstrip('/')}/{mapped_endpoint}"
        
        base_params = params or {}
        if 'apikey' not in base_params:
            base_params['apikey'] = self.api_key
        
        if 'outputformat' not in base_params and 'output' not in base_params:
            base_params['outputformat'] = 'xml'
        
        try:
            safe_params = base_params.copy()
            if 'apikey' in safe_params:
                safe_params['apikey'] = f"{safe_params['apikey'][:10]}..."
            if 'data' in safe_params:
                safe_params['data'] = f"{safe_params['data'][:50]}..."
            
            _logger.info(f"Palletways API {method} {url}")
            _logger.info(f"Endpoint usado: {'PORTAL' if use_portal else 'API GLOBAL'}")
            _logger.info(f"Método mapeado: {mapped_endpoint}")
            _logger.info(f"Parámetros: {safe_params}")
            
            if method.upper() == 'GET':
                response = requests.get(url, params=base_params, timeout=timeout)
                
            elif method.upper() == 'POST':
                headers = {}
                if data:
                    # ✅ CORRECCIÓN v2.4.1: XML va en el body del POST
                    if isinstance(data, str) and data.strip().startswith('<?xml'):
                        headers['Content-Type'] = 'application/xml; charset=UTF-8'
                        headers['Accept'] = 'application/xml'
                        
                        if isinstance(data, str):
                            data_bytes = data.encode('utf-8')
                        else:
                            data_bytes = data
                        
                        _logger.info(f"XML original length: {len(data)} chars")
                        _logger.info(f"XML encoded length: {len(data_bytes)} bytes")
                        _logger.info(f"XML inicio: {data[:200]}")
                        _logger.info(f"XML final: {data[-200:]}")
                        
                        _logger.info("="*80)
                        _logger.info("VERIFICACIÓN FINAL PRE-ENVÍO:")
                        _logger.info(f"URL: {url}")
                        _logger.info(f"Params: {safe_params}")
                        _logger.info(f"Headers: {headers}")
                        _logger.info(f"Body size: {len(data_bytes)} bytes")
                        _logger.info(f"Body type: {type(data_bytes)}")
                        
                        try:
                            body_preview = data_bytes.decode('utf-8')
                            _logger.info(f"Body preview (primeros 500 chars):")
                            _logger.info(body_preview[:500])
                            _logger.info(f"Body preview (últimos 500 chars):")
                            _logger.info(body_preview[-500:])
                            
                            if not body_preview.strip().endswith('</Manifest>'):
                                _logger.error("❌ ERROR: XML INCOMPLETO - No termina con </Manifest>")
                                raise UserError("XML del manifest está incompleto")
                                
                        except Exception as e:
                            _logger.error(f"Error verificando body: {e}")
                        
                        _logger.info("="*80)
                    else:
                        headers['Content-Type'] = 'application/json'
                        data_bytes = data if isinstance(data, bytes) else data.encode('utf-8')
                    
                    _logger.info(f"POST data size: {len(data_bytes)} bytes")
                    _logger.info(f"Content-Type: {headers['Content-Type']}")
                    _logger.debug(f"POST body preview: {data_bytes[:500]}")
                    
                    response = requests.post(
                        url, 
                        params=base_params,
                        data=data_bytes,
                        headers=headers,
                        timeout=timeout
                    )
                else:
                    response = requests.post(
                        url,
                        params=base_params,
                        timeout=timeout
                    )
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            _logger.info(f"Palletways API Response: {response.status_code}")
            _logger.info(f"Response Content-Type: {response.headers.get('content-type', 'unknown')}")
            _logger.info(f"Response preview: {response.text[:500]}")
            
            if response.status_code not in [200, 201]:
                _logger.error(f"Error HTTP {response.status_code}: {response.text}")
                
                if response.status_code == 404 and _retry_with_portal and not use_portal:
                    _logger.warning(f"Método {mapped_endpoint} no disponible en API Global, intentando con Portal...")
                    try:
                        temp_client = self.copy({'api_endpoint_type': 'portal'})
                        result = temp_client._make_api_request(
                            method, endpoint, data, params, timeout, 
                            _retry_with_portal=False
                        )
                        return result
                    except Exception as e:
                        _logger.warning(f"Portal tampoco disponible: {e}")
                
                if response.status_code == 404:
                    raise UserError(
                        f"Método API no disponible: {mapped_endpoint}\n\n"
                        f"Endpoint usado: {base_url}\n"
                        f"Sugerencia: Intente cambiar el 'Tipo de Endpoint' en la configuración del Cliente API."
                    )
                
                raise UserError(f"Error HTTP {response.status_code}: {response.text}")
            
            content_type = response.headers.get('content-type', '').lower()
            
            # ✅ CORRECCIÓN v2.3.1: Intentar parsear como XML primero
            if 'xml' in content_type or response.text.strip().startswith('<?xml'):
                try:
                    root = ET.fromstring(response.content)
                    xml_dict = self._xml_to_dict(root)
                    
                    _logger.info(f"XML parseado exitosamente")
                    _logger.debug(f"XML dict: {json.dumps(xml_dict, indent=2, default=str)}")
                    
                    return xml_dict
                    
                except ET.ParseError as e:
                    _logger.error(f"Error parseando XML: {e}")
                    _logger.error(f"Contenido: {response.text[:500]}")
                    raise UserError(f"Error parseando respuesta XML: {e}")
            
            # Fallback a JSON
            try:
                json_response = response.json() if response.content else {}
                _logger.info(f"JSON parseado exitosamente")
                return json_response
            except json.JSONDecodeError:
                if 'application/pdf' in content_type:
                    return response.content
                else:
                    _logger.error(f"Respuesta inesperada: {response.text[:500]}")
                    raise UserError(f"Respuesta inesperada de la API")
                    
        except requests.exceptions.Timeout:
            raise UserError("Timeout conectando con Palletways API")
        except requests.exceptions.ConnectionError:
            raise UserError("Error de conexión con Palletways API")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error API Palletways: {e}")
            raise UserError(f"Error conectando con Palletways: {e}")
    
    def _xml_to_dict(self, element):
        """
        ✅ NUEVO v2.3.0:
        Convertir elemento XML a diccionario para compatibilidad
        """
        result = {}
        
        if element.text and element.text.strip():
            result['_text'] = element.text.strip()
        
        if element.attrib:
            result['_attributes'] = element.attrib
        
        for child in element:
            child_data = self._xml_to_dict(child)
            
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else: 
                result[child.tag] = child_data
        
        if len(result) == 1 and '_text' in result:
            return result['_text']
        
        return result
    
    def create_consignment(self, shipment_data):
        """
        ✅ CORRECCIÓN v2.5.0:
        Crear consignación usando XML en parámetro 'data' de la URL
        Soporta tanto API Global como Portal API
        """
        try: 
            _logger.info("="*80)
            _logger.info("DIAGNÓSTICO PRE-ENVÍO:")
            _logger.info(f"  Cliente API: {self.name}")
            _logger.info(f"  Account Code: '{self.account_code}'")
            _logger.info(f"  Account Code type: {type(self.account_code)}")
            _logger.info(f"  Account Code length: {len(str(self.account_code)) if self.account_code else 0}")
            _logger.info(f"  Test Mode: {self.test_mode}")
            _logger.info(f"  Endpoint: {self.api_endpoint}")
            _logger.info(f"  Endpoint Type: {self.api_endpoint_type}")
            _logger.info("="*80)
            
            manifest_xml = self._build_manifest(shipment_data)
            
            commit_param = 'no' if self.test_mode else 'yes'
            
            # ✅ CORRECCIÓN v2.5.0: NO codificar manualmente
            # requests.get() codificará automáticamente los parámetros UNA SOLA VEZ
            params = {
                'commit': commit_param,
                'inputformat': 'xml',
                'outputformat': 'xml',
                'data': manifest_xml,  # ✅ XML SIN codificar - requests lo codificará automáticamente
            }
            
            _logger.info("="*80)
            _logger.info("CREANDO CONSIGNACIÓN (requests codificará automáticamente)")
            _logger.info(f"Endpoint Type: {self.api_endpoint_type}")
            _logger.info(f"Test Mode: {self.test_mode}")
            _logger.info(f"Commit: {commit_param}")
            _logger.info(f"XML size: {len(manifest_xml)} caracteres")
            _logger.info("="*80)
            
            endpoint = 'createConsignment'
            
            # ✅ CORRECCIÓN v2.5.0: GET con params - requests codificará automáticamente
            response = self._make_api_request(
                'GET',
                endpoint,
                params=params,  # ← requests.get() codificará automáticamente
                timeout=60
            )
            
            _logger.info("="*80)
            _logger.info("RESPUESTA RECIBIDA DE PALLETWAYS:")
            _logger.info(json.dumps(response, indent=2, default=str))
            _logger.info("="*80)
            
            return response
            
        except Exception as e:
            _logger.error(f"Error creando consignación Palletways: {e}")
            raise UserError(f"Error creando consignación: {e}")

    def _build_manifest(self, shipment_data):
        """
        ✅ CORRECCIÓN v2.5.0:
        Construir manifest en formato XML según documentación oficial PDF página 3-4
        ESTRUCTURA CORRECTA:
        1. Manifest (root)
        2. Date, Time, Confirm
        3. Depot > Account > Code (⚠️ OBLIGATORIO)
        4. Consignment (dentro de Account)
        5. Type, ImportID, Number, Reference, Lifts, Weight, etc.
        6. Service
        7. Address Type="Delivery" (PRIMERO)
        8. Address Type="Collection" (DESPUÉS)
        9. BillUnit
        10. NotificationSet
        """
        
        # ✅ VERIFICACIÓN CRÍTICA: Account Code debe existir
        if not self.account_code or self.account_code.strip() == '':
            raise UserError(
                "❌ ERROR DE CONFIGURACIÓN\n\n"
                "El Cliente API no tiene 'Código Cliente' configurado.\n\n"
                "Solución:\n"
                "1. Ir a: Inventario > Palletways > Configuración > Clientes API\n"
                "2. Editar el cliente API\n"
                "3. Completar el campo 'Código Cliente' (ej: 5181460 o D518-1-DAYO)\n"
                "4. Guardar y volver a intentar"
            )
        
        _logger.info(f"✓ Account Code válido: {self.account_code}")
        
        collection_addr = shipment_data.get('collection_address')
        delivery_addr = shipment_data.get('delivery_address')
        
        # ✅ CORRECCIÓN v2.5.0: Construir XML con estructura CORRECTA
        manifest = ET.Element('Manifest')
        
        # 1. Date, Time, Confirm (opcionales pero recomendados)
        ET.SubElement(manifest, 'Date').text = fields.Date.today().strftime('%Y-%m-%d')
        ET.SubElement(manifest, 'Time').text = datetime.now().strftime('%H:%M:%S')
        
        confirm_value = "no" if self.test_mode else "yes"
        ET.SubElement(manifest, 'Confirm').text = confirm_value
        
        # 2. Depot > Account > Code (⚠️ ESTRUCTURA OBLIGATORIA)
        depot = ET.SubElement(manifest, 'Depot')
        account = ET.SubElement(depot, 'Account')
        
        # ⚠️ CRÍTICO: El elemento <Code> es OBLIGATORIO
        if not self.account_code:
            raise UserError(
                "❌ ERROR CRÍTICO: No hay código de cliente configurado.\n\n"
                "El campo 'Código Cliente' es OBLIGATORIO según Palletways.\n\n"
                "Solución:\n"
                "1. Ir a: Inventario > Palletways > Configuración > Clientes API\n"
                "2. Editar el cliente API\n"
                "3. Completar el campo 'Código Cliente' (ej: 434481 o D518-1-DAYO)\n"
                "4. Guardar y volver a intentar"
            )
        
        code_element = ET.SubElement(account, 'Code')
        code_element.text = str(self.account_code).strip()
        _logger.info(f"✓ <Code> añadido con valor: {self.account_code}")
        
        # 3. Consignment (dentro de Account)
        consignment = ET.SubElement(account, 'Consignment')
        
        # 4. Datos del consignment
        ET.SubElement(consignment, 'Type').text = shipment_data.get('type', 'D')
        ET.SubElement(consignment, 'ImportID').text = shipment_data.get('import_id', '')
        ET.SubElement(consignment, 'Number').text = shipment_data.get('reference', '')
        ET.SubElement(consignment, 'Reference').text = shipment_data.get('client_reference', '')
        ET.SubElement(consignment, 'Lifts').text = str(shipment_data.get('pallets', 1))
        ET.SubElement(consignment, 'Weight').text = str(int(shipment_data.get('weight', 1)))
        
        ET.SubElement(consignment, 'Handball').text = "yes" if shipment_data.get('handball') else "no"
        ET.SubElement(consignment, 'TailLift').text = "yes" if shipment_data.get('taillift') else "no"
        ET.SubElement(consignment, 'Classification').text = shipment_data.get('classification', 'B2B')
        ET.SubElement(consignment, 'BookInRequest').text = "yes" if shipment_data.get('book_in_request') else "no"
        
        if shipment_data.get('book_in_request'):
            ET.SubElement(consignment, 'BookInContactName').text = shipment_data.get('contact_name', '')
            ET.SubElement(consignment, 'BookInContactPhone').text = shipment_data.get('contact_phone', '')
            ET.SubElement(consignment, 'BookInInstructions').text = shipment_data.get('book_in_instructions', '')
        
        ET.SubElement(consignment, 'ManifestNote').text = shipment_data.get('manifest_note', '')
        ET.SubElement(consignment, 'CollectionDate').text = shipment_data.get('collection_date', '')
        ET.SubElement(consignment, 'DeliveryDate').text = shipment_data.get('delivery_date', '')
        
        # 5. Service
        service = ET.SubElement(consignment, 'Service')
        ET.SubElement(service, 'Type').text = 'Delivery'
        ET.SubElement(service, 'Code').text = shipment_data.get('service_code', 'B')
        ET.SubElement(service, 'Surcharge').text = shipment_data.get('service_code', 'B')
        
        # 6. ⚠️ CRÍTICO: Address DELIVERY PRIMERO (según documentación)
        if delivery_addr:
            address_delivery = ET.SubElement(consignment, 'Address')
            ET.SubElement(address_delivery, 'Type').text = 'Delivery'
            ET.SubElement(address_delivery, 'ContactName').text = delivery_addr.name or ''
            ET.SubElement(address_delivery, 'Telephone').text = delivery_addr.phone or delivery_addr.mobile or ''
            if delivery_addr.fax:
                ET.SubElement(address_delivery, 'Fax').text = delivery_addr.fax
            ET.SubElement(address_delivery, 'CompanyName').text = delivery_addr.commercial_company_name or delivery_addr.name or ''
            
            if delivery_addr.street:
                ET.SubElement(address_delivery, 'Line').text = delivery_addr.street
            if delivery_addr.street2:
                ET.SubElement(address_delivery, 'Line').text = delivery_addr.street2
            
            ET.SubElement(address_delivery, 'Town').text = delivery_addr.city or ''
            ET.SubElement(address_delivery, 'County').text = delivery_addr.state_id.name if delivery_addr.state_id else ''
            ET.SubElement(address_delivery, 'PostCode').text = delivery_addr.zip or ''
            ET.SubElement(address_delivery, 'Country').text = delivery_addr.country_id.code if delivery_addr.country_id else 'ES'
        
        # 7. ⚠️ CRÍTICO: Address COLLECTION DESPUÉS (según documentación)
        if collection_addr:
            address_collection = ET.SubElement(consignment, 'Address')
            ET.SubElement(address_collection, 'Type').text = 'Collection'
            ET.SubElement(address_collection, 'ContactName').text = collection_addr.name or ''
            ET.SubElement(address_collection, 'Telephone').text = collection_addr.phone or collection_addr.mobile or ''
            if collection_addr.fax:
                ET.SubElement(address_collection, 'Fax').text = collection_addr.fax
            ET.SubElement(address_collection, 'CompanyName').text = collection_addr.commercial_company_name or collection_addr.name or ''
            
            if collection_addr.street:
                ET.SubElement(address_collection, 'Line').text = collection_addr.street
            if collection_addr.street2:
                ET.SubElement(address_collection, 'Line').text = collection_addr.street2
            
            ET.SubElement(address_collection, 'Town').text = collection_addr.city or ''
            ET.SubElement(address_collection, 'County').text = collection_addr.state_id.name if collection_addr.state_id else ''
            ET.SubElement(address_collection, 'PostCode').text = collection_addr.zip or ''
            ET.SubElement(address_collection, 'Country').text = collection_addr.country_id.code if collection_addr.country_id else 'ES'
        
        # 8. BillUnit
        bill_unit = ET.SubElement(consignment, 'BillUnit')
        ET.SubElement(bill_unit, 'Type').text = shipment_data.get('bill_unit_type', 'FP')
        ET.SubElement(bill_unit, 'Amount').text = str(shipment_data.get('bill_unit_amount', 1))
        
        # 9. NotificationSet (si existe)
        if shipment_data.get('notification_emails'):
            notification_set = ET.SubElement(consignment, 'NotificationSet')
            ET.SubElement(notification_set, 'SysGroup').text = '1'
            ET.SubElement(notification_set, 'SysGroup').text = '3'
            ET.SubElement(notification_set, 'Email').text = shipment_data.get('notification_emails')
        
        # ✅ CORRECCIÓN v2.5.0: Generar XML con declaración correcta
        xml_bytes = ET.tostring(manifest, encoding='utf-8', xml_declaration=True)
        xml_string = xml_bytes.decode('utf-8')
        
        _logger.info("="*80)
        _logger.info("MANIFEST XML CONSTRUIDO:")
        _logger.info(f"  Longitud total: {len(xml_string)} caracteres")
        _logger.info(f"  Account Code: {self.account_code}")
        _logger.info(f"  Confirm: {confirm_value}")
        _logger.info(f"  Type: {shipment_data.get('type', 'D')}")
        _logger.info("="*80)
        
        # ✅ VERIFICACIÓN CRÍTICA: Verificar que <Code> está presente
        if f'<Code>{self.account_code}</Code>' not in xml_string:
            _logger.error("❌ ERROR CRÍTICO: El XML no contiene <Code> con el account_code")
            _logger.error(f"XML generado:\n{xml_string}")
            raise UserError(
                "❌ ERROR INTERNO: El XML no contiene el elemento <Code> obligatorio.\n"
                "Contacte con soporte técnico."
            )
        
        # ✅ VERIFICACIÓN: Verificar que termina correctamente
        if not xml_string.strip().endswith('</Manifest>'):
            _logger.error("❌ ERROR CRÍTICO: El XML no termina con </Manifest>")
            raise UserError("❌ ERROR: XML incompleto o malformado")
        
        _logger.info("XML COMPLETO:")
        _logger.info(xml_string)
        _logger.info("="*80)
        
        return xml_string
    
    def get_available_services(self, origin_country, origin_postal, destination_country, destination_postal, con_type='D'):
        """
        Obtener servicios disponibles según documentación oficial página 13
        """
        try:
            endpoint = f"availableServices/{con_type}/{origin_country}/{origin_postal}/{destination_country}/{destination_postal}"
            
            response = self._make_api_request('GET', endpoint)
            
            if response.get('Status', {}).get('Code') == 'OK':
                detail = response.get('Detail', {})
                services = detail.get('Data', [])
                
                if isinstance(services, dict):
                    services = [services]
                
                return services
            else:
                error_msg = response.get('Status', {}).get('Description', 'Error desconocido')
                raise UserError(f"Error obteniendo servicios: {error_msg}")
                
        except Exception as e:
            _logger.error(f"Error obteniendo servicios disponibles: {e}")
            raise UserError(f"Error obteniendo servicios: {e}")
    
    def get_consignment_status(self, tracking_id):
        """
        Obtener estado de consignación según documentación oficial página 9
        """
        try:
            endpoint = f"getConsignment/{tracking_id}"
            
            response = self._make_api_request('GET', endpoint)
            
            return response
            
        except Exception as e:
            _logger.error(f"Error obteniendo estado {tracking_id}: {e}")
            raise UserError(f"Error obteniendo estado: {e}")
    
    def get_labels(self, tracking_id):
        """
        Descargar etiquetas PDF según documentación oficial página 12
        """
        try:
            endpoint = f"getLabelsByTID/{tracking_id}"
            
            pdf_data = self._make_api_request('GET', endpoint)
            
            if isinstance(pdf_data, bytes):
                return pdf_data
            else:
                raise UserError("Error descargando etiquetas: respuesta no es PDF")
                
        except Exception as e:
            _logger.error(f"Error descargando etiquetas {tracking_id}: {e}")
            raise UserError(f"Error descargando etiquetas: {e}")
    
    def get_pod(self, tracking_id):
        """
        Descargar comprobante de entrega (POD) según documentación oficial página 12
        """
        try:
            endpoint = f"getPodByTrackingId/{tracking_id}"
            
            pod_data = self._make_api_request('GET', endpoint)
            
            if isinstance(pod_data, bytes):
                return pod_data
            else:
                raise UserError("Error descargando POD: respuesta no es PDF")
                
        except Exception as e:
            _logger.error(f"Error descargando POD {tracking_id}: {e}")
            raise UserError(f"Error descargando POD: {e}")
    
    def get_notes(self, tracking_id):
        """
        Obtener notas de envío según documentación oficial página 11
        """
        try:
            endpoint = f"getNotes/trackingId/{tracking_id}"
            
            response = self._make_api_request('GET', endpoint)
            
            return response
            
        except Exception as e:
            _logger.error(f"Error obteniendo notas {tracking_id}: {e}")
            raise UserError(f"Error obteniendo notas: {e}")
    
    def action_test_connection(self):
        """
        ✅ CORRECCIÓN v2.5.0:
        Test de conectividad con API - Respeta configuración del usuario
        """
        messages = []
        
        try:
            _logger.info(f"Probando endpoint configurado: {self.api_endpoint}")
            
            if self.api_endpoint_type == 'portal':
                response = self._make_api_request('GET', 'version', _retry_with_portal=False)
            else:
                response = self._make_api_request(
                    'GET', 
                    'availableServices/D/ES/28001/ES/28002',
                    _retry_with_portal=False
                )
            
            if response:
                messages.append(f"✓ Conexión exitosa con {self.api_endpoint_type.upper()}")
                messages.append(f"  Endpoint: {self.api_endpoint}")
                messages.append(f"  Código Cuenta: {self.account_code}")
            
        except Exception as e:
            error_msg = str(e)[:150]
            messages.append(f"✗ Error en {self.api_endpoint_type.upper()}: {error_msg}")
        
        other_type = 'portal' if self.api_endpoint_type == 'api' else 'api'
        other_url = 'https://portal.palletways.com/api/' if other_type == 'portal' else 'https://api.palletways.com/'
        
        try:
            _logger.info(f"Probando endpoint alternativo: {other_url}")
            
            temp_client = self.copy({'api_endpoint_type': other_type})
            
            if other_type == 'portal':
                response = temp_client._make_api_request('GET', 'version', _retry_with_portal=False)
            else:
                response = temp_client._make_api_request(
                    'GET', 
                    'availableServices/D/ES/28001/ES/28002',
                    _retry_with_portal=False
                )
            
            if response:
                messages.append(f"✓ {other_type.upper()} también disponible")
                messages.append(f"  Endpoint: {other_url}")
            
        except Exception as e:
            error_msg = str(e)[:150]
            messages.append(f"✗ {other_type.upper()} no disponible: {error_msg}")
        
        success_count = sum(1 for m in messages if m.startswith('✓'))
        
        if success_count >= 1:
            msg_type = 'success'
            title = 'Test de Conexión Exitoso ✅'
        else:
            msg_type = 'danger'
            title =  'Test de Conexión Fallido ❌'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': '\n'.join(messages),
                'type': msg_type,
                'sticky': True,
            }
        }
    
    def get_service_description(self, service_code):
        """Obtener descripción del servicio según código"""
        service_names = {
            'A': 'Next Day Standard',
            'DH': 'Premium Timed Delivery PM (Pre-Booked)',
            'E': 'Next Day AM',
            'F': 'Saturday AM',
            '': 'Timed Delivery (Pre-Booked)',
            'B': 'Economy',
            'J': 'Economy A.M',
            'K': 'Economy Timed',
            'Z': 'Saturday Economy A.M',
            'C': 'Collection - Premium',
            'V': 'Collection Premium 48hr',
            'I': 'Remote Contract Collection',
            'D': 'Collection - Economy',
            'N': 'Collection 3 Day',
            'P': 'Collection 5 Day',
            'X': 'Collection 4 Day',
            '0': 'Europe Collect Premium',
            '1': 'Europe Saturday Premium',
            '2': 'Europe 2 Day Premium',
            '3': 'Europe 3 Day Premium',
            '4': 'Europe 4+ Day Premium',
            '9': 'Europe Timed (Pre-Booked)',
            '5': 'Europe 5 Day Economy',
            '6': 'Europe 3 Day Economy',
            '7': 'Europe 4 Day Economy',
            '8': 'Europe Collect Economy',
            'O': 'Premium 48',
            'L': '3 Day Service',
        }
        
        return service_names.get(service_code, service_code or '')
