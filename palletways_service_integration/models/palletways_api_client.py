import requests
import json
import base64
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class PalletwaysApiClient(models.Model):
    _name = 'palletways.api.client'
    _description = 'Cliente API Palletways'
    _rec_name = 'name'
    
    name = fields.Char('Nombre', required=True)
    api_endpoint = fields.Char('Endpoint API', 
                              default='https://api.palletways.com/',
                              required=True)
    api_key = fields.Char('API Key', required=True)
    account_code = fields.Char('Código Cliente', required=True) 
    test_mode = fields.Boolean('Modo Prueba', default=True)
    company_id = fields.Many2one('res.company', string='Empresa',
                                default=lambda self: self.env.company)
    active = fields.Boolean('Activo', default=True)
    
    # Rate limiting
    last_request_time = fields.Datetime('Última Petición')
    request_count = fields.Integer('Contador Peticiones')
    
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
            
            # Reset contador si ha pasado más de 1 minuto
            if time_diff >= 60:
                self.request_count = 0
            elif self.request_count >= 100:
                raise UserError(
                    "Límite de API alcanzado (100 peticiones/minuto). "
                    "Espere antes de realizar más peticiones."
                )
        
        # Actualizar contadores
        self.write({
            'last_request_time': now,
            'request_count': self.request_count + 1
        })
    
    def _make_api_request(self, method, endpoint, data=None, params=None, timeout=30):
        """Realizar petición HTTP a la API de Palletways"""
        self._check_rate_limit()
        
        url = f"{self.api_endpoint.rstrip('/')}/{endpoint}"
        
        # Parámetros base según documentación oficial web
        base_params = {
            'apikey': self.api_key,
        }
        if params:
            base_params.update(params)
        
        # CAMBIO: Manejar outputformat por defecto
        if 'outputformat' not in base_params:
            base_params['outputformat'] = 'json'
            
        try:
            # Log con API key censurada para seguridad
            safe_params = base_params.copy()
            if 'apikey' in safe_params:
                safe_params['apikey'] = f"{safe_params['apikey'][:10]}..."
            
            _logger.info(f"Palletways API {method} {url}")
            _logger.info(f"Parámetros: {safe_params}")
            
            if method.upper() == 'GET':
                response = requests.get(url, params=base_params, timeout=timeout)
            elif method.upper() == 'POST':
                # CAMBIO: Para createconsignment, enviar data como parámetro según documentación web
                if 'createconsignment' in endpoint.lower():
                    base_params['data'] = json.dumps(data) if data else '{}'
                    response = requests.post(url, data=base_params, timeout=timeout)
                else:
                    response = requests.post(url, params=base_params, json=data, timeout=timeout)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
                
            _logger.info(f"Palletways API Response: {response.status_code}")
            _logger.info(f"Response Content-Type: {response.headers.get('content-type', 'unknown')}")
            _logger.info(f"Response URL final: {response.url}")
            
            # Log primeros 500 caracteres de respuesta para debugging
            _logger.info(f"Response preview: {response.text[:500]}")
            
            # Verificar respuesta HTTP
            if response.status_code not in [200, 201]:
                _logger.error(f"Error HTTP {response.status_code}: {response.text}")
                raise UserError(f"Error HTTP {response.status_code}: {response.text}")
            
            # Manejar diferentes tipos de respuesta
            content_type = response.headers.get('content-type', '').lower()
        
            # MEJORA: Manejo específico según documentación oficial
            try:
                json_response = response.json() if response.content else {}
                _logger.info(f"JSON parseado exitosamente: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
                
                # Verificar estructura de respuesta según documentación
                if 'Status' in json_response:
                    status = json_response['Status']
                    if isinstance(status, list):
                        status = status[0] if status else {}
                    
                    # Manejar códigos específicos según documentación página 8
                    status_code = status.get('Code', '')
                    if status_code == 'ERROR_FORMAT_INVALID':
                        raise UserError("Formato de datos inválido. Verifique la estructura XML/JSON.")
                    elif status_code == 'ERROR_VALIDATION':
                        # Procesar errores de validación detallados
                        validation_errors = json_response.get('ValidationErrors', {})
                        error_details = self._extract_validation_errors(validation_errors)
                        raise UserError(f"Errores de validación:\n{error_details}")
                
                return json_response
            
            except json.JSONDecodeError:
                # Si no es JSON válido, entonces manejar según Content-Type
                if 'application/pdf' in content_type:
                    # Respuesta PDF (para etiquetas y PODs)
                    return response.content
                
                elif 'text/html' in content_type:
                    # Respuesta HTML - probablemente un error
                    _logger.error(f"Respuesta HTML (error): {response.text[:500]}")
                
                    # Verificar errores específicos según documentación página 13
                    if "does not exist" in response.text:
                        raise UserError(f"Método API no válido: {endpoint}")
                    elif "not authorised" in response.text:
                        raise UserError("API Key no autorizada. Verifique sus credenciales.")
                    elif "not specified" in response.text:
                        raise UserError("API Key no especificada.")
                    elif "consignment data not found" in response.text:
                        raise UserError("Datos de consignación no encontrados")
                    elif "not configured to produce labels" in response.text:
                        raise UserError("Cuenta no configurada para producir etiquetas")
                    else:
                        raise UserError(f"Error API: {response.text[:200]}")
                else:
                    # Si no es JSON, PDF o HTML, es un error
                    _logger.error(f"Respuesta inesperada: {response.text}")
                    raise UserError(f"Respuesta inesperada de la API: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            raise UserError("Timeout conectando con Palletways API")
        except requests.exceptions.ConnectionError:
            raise UserError("Error de conexión con Palletways API")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error API Palletways: {e}")
            raise UserError(f"Error conectando con Palletways: {e}")
    
    def create_consignment(self, shipment_data):
        """Crear envío en Palletways"""
        manifest_data = self._build_manifest(shipment_data)
        
        params = {
            'commit': 'no' if self.test_mode else 'yes',
            'inputformat': 'json',  # AÑADIR: Especificar formato de entrada
            'outputformat': 'json'  # AÑADIR: Especificar formato de salida
        }
        
        # Logs de debugging para verificar configuración
        _logger.info(f"CREANDO ENVÍO REAL - MODO TEST: {self.test_mode}")
        _logger.info(f"COMMIT PARAM: {params['commit']}")
        _logger.info(f"API KEY (primeros 10 chars): {self.api_key[:10]}...")
        _logger.info(f"ACCOUNT CODE: {self.account_code}")
        
        _logger.info(f"Creando consignación REAL: {json.dumps(manifest_data, indent=2)}")
        
        # CAMBIO: Usar el endpoint correcto según documentación web
        response = self._make_api_request('POST', 'createconsignment', 
                                        data=manifest_data, params=params)
        
        _logger.info(f"Respuesta creación REAL: {json.dumps(response, indent=2)}")
        return response
    
    def get_consignment_status(self, tracking_id):
        """Obtener estado de envío"""
        return self._make_api_request('GET', f'conStatusByTrackingId/{tracking_id}')
    
    def get_consignment_details(self, tracking_id):
        """Obtener detalles completos del envío según documentación web"""
        return self._make_api_request('GET', f'getconsignment/{tracking_id}')
    
    def get_labels(self, tracking_id, degrees=0):
        """Descargar etiquetas PDF según documentación web oficial"""
        if degrees:
            endpoint = f'getLabelsById/{tracking_id}/{degrees}'
        else:
            endpoint = f'getLabelsById/{tracking_id}'
        
        # Para PDFs, hacer petición directa
        url = f"{self.api_endpoint.rstrip('/')}/{endpoint}"
        params = {'apikey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/pdf' in content_type:
                return response.content
            else:
                # Manejar errores según documentación web
                raise UserError(f"Error obteniendo etiquetas: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error descargando etiquetas: {e}")
    
    def get_pod(self, tracking_id):
        """Obtener comprobante de entrega (POD) según documentación web"""
        url = f"{self.api_endpoint.rstrip('/')}/getPodByTrackingId/{tracking_id}"
        params = {'apikey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/pdf'):
                return response.content
            else:
                raise UserError(f"POD no disponible: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error descargando POD: {e}")
    
    def get_available_services(self, origin_country, origin_postcode, 
                              dest_country, dest_postcode, consignment_type='D'):
        """Obtener servicios disponibles según documentación oficial"""
        endpoint = f'availableServices/{consignment_type}/{origin_country}/{origin_postcode}/{dest_country}/{dest_postcode}'
        
        _logger.info(f"Solicitando servicios: {endpoint}")
        
        try:
            response = self._make_api_request('GET', endpoint)
            
            # Manejar diferentes formatos de respuesta según documentación
            if isinstance(response, dict):
                # Formato con Status/Detail/Data
                if response.get('Status', {}).get('Code') == 'OK':
                    detail = response.get('Detail', {})
                    data = detail.get('Data', [])
                    
                    # Data puede ser un objeto único o array
                    if isinstance(data, dict):
                        data = [data]
                    
                    return {
                        'success': True,
                        'services': data,
                        'count': response.get('Status', {}).get('Count', len(data))
                    }
                else:
                    return {
                        'success': False,
                        'error': response.get('Status', {}).get('Description', 'Error desconocido'),
                        'services': []
                    }
            
            # Si es array directo
            elif isinstance(response, list):
                return {
                    'success': True,
                    'services': response,
                    'count': len(response)
                }
            
            else:
                _logger.error(f"Formato de respuesta inesperado: {type(response)}")
                return {
                    'success': False,
                    'error': 'Formato de respuesta inesperado',
                    'services': []
                }
                
        except Exception as e:
            _logger.error(f"Error obteniendo servicios disponibles: {e}")
            return {
                'success': False,
                'error': str(e),
                'services': []
            }
    
    def get_notes(self, tracking_id):
        """Obtener notas del envío según documentación web"""
        return self._make_api_request('GET', f'getnotes/trackingid/{tracking_id}')
    
    def _build_manifest(self, data):
        """Construir JSON manifest según especificación API oficial"""
        # Validar datos obligatorios según documentación
        if not data.get('collection_address') or not data.get('delivery_address'):
            raise UserError("Direcciones de recogida y entrega son obligatorias")
        
        if not data.get('reference'):
            raise UserError("Número de referencia es obligatorio")
        
        # ESTRUCTURA CORREGIDA según documentación oficial PDF página 4
        manifest = {
            'Manifest': {
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Time': datetime.now().strftime('%H:%M:%S'),
                'Confirm': 'yes',
                'Depot': {
                    'Account': {
                        'Code': self.account_code,
                        'Consignment': {
                            'Type': str(data.get('type', 'D')),  # D=Delivery, C=Collection, 3=Third Party
                            'ImportID': str(data.get('import_id', '')),
                            'Number': str(data.get('reference')),
                            'Reference': str(data.get('client_reference', '')),
                            'Lifts': str(data.get('pallets', 1)),
                            'Weight': str(int(data.get('weight', 0))),
                            'Handball': 'yes' if data.get('handball') else 'no',
                            'TailLift': 'yes' if data.get('taillift') else 'no',
                            'Classification': data.get('classification', 'B2B'),
                            'BookInRequest': 'yes' if data.get('book_in_request') else 'no',
                            'ManifestNote': str(data.get('manifest_note', '')),
                            'CollectionDate': data.get('collection_date'),
                            'DeliveryDate': data.get('delivery_date', ''),
                            'Service': {
                                'Type': 'Delivery',  # Según documentación oficial
                                'Code': data.get('service_code', 'B'),
                                'Surcharge': data.get('surcharge_code', data.get('service_code', 'B'))
                            },
                            'Address': [
                                self._build_address(data['collection_address'], 'Collection'),
                                self._build_address(data['delivery_address'], 'Delivery')
                            ],
                            'BillUnit': {
                                'Type': data.get('bill_unit_type', 'FP'),
                                'Amount': str(data.get('bill_unit_amount', 1))
                            }
                        }
                    }
                }
            }
        }
        
        # Añadir información de cita si es necesaria
        consignment = manifest['Manifest']['Depot']['Account']['Consignment']
        if data.get('book_in_request'):
            consignment.update({
                'BookInContactName': str(data.get('contact_name', ''))[:50],
                'BookInContactPhone': str(data.get('contact_phone', ''))[:20],
                'BookInContactNote': str(data.get('contact_note', 'Llamar antes'))[:100],
                'BookInInstructions': str(data.get('instructions', 'Cita previa requerida'))[:200]
            })
        
        # Añadir información de contacto para entrega
        if data.get('contact_name') or data.get('contact_phone'):
            consignment.update({
                'DeliveryAddressContactName': str(data.get('contact_name', ''))[:50],
                'DeliveryAddressContactNumber': str(data.get('contact_phone', ''))[:20]
            })
        
        # Añadir NotificationSet si hay emails o SMS - Mejorado según documentación oficial
        if data.get('notification_emails') or data.get('notification_sms'):
            notification_set = {
                'SysGroup': ['1', '3']  # Notificaciones estándar según documentación
            }
            
            if data.get('notification_emails'):
                emails = data['notification_emails'] if isinstance(data['notification_emails'], list) else [data['notification_emails']]
                notification_set['Email'] = emails[0]  # Palletways acepta un email principal
            
            if data.get('notification_sms'):
                notification_set['SMSNumber'] = str(data['notification_sms'])
            
            consignment['NotificationSet'] = notification_set
        
        return manifest
    
    def _build_address(self, partner, address_type):
        """Construir datos de dirección según especificación oficial"""
        if not partner:
            raise UserError(f"Dirección {address_type} requerida")
        
        # Validaciones obligatorias según documentación oficial
        if not partner.zip:
            raise UserError(f"Código postal requerido para dirección {address_type}")
        
        if not partner.country_id:
            raise UserError(f"País requerido para dirección {address_type}")
        
        if not partner.city:
            raise UserError(f"Ciudad requerida para dirección {address_type}")
        
        address = {
            'Type': address_type,
            'ContactName': str(partner.name or '')[:50],
            'Telephone': str(partner.phone or partner.mobile or '')[:20],
            'CompanyName': str(partner.commercial_company_name or partner.name or '')[:50],
            'Town': str(partner.city or '')[:30],
            'County': str(partner.state_id.name if partner.state_id else '')[:30],
            'PostCode': str(partner.zip or '')[:10],
            'Country': partner.country_id.code or 'ES',
        }
        
        # Manejar líneas de dirección (máximo 5 según documentación oficial)
        lines = []
        if partner.street:
            lines.append(str(partner.street)[:50])
        if partner.street2:
            lines.append(str(partner.street2)[:50])
        
        # Según documentación, puede ser string único o array
        if len(lines) == 1:
            address['Line'] = lines[0]
        elif len(lines) > 1:
            address['Line'] = lines[:5]  # Máximo 5 líneas según documentación
        
        # Añadir Fax si está disponible
        if hasattr(partner, 'fax') and partner.fax:
            address['Fax'] = str(partner.fax)[:20]
        
        return address
    
    def test_connection(self):
        """Probar conexión con API usando keytest según documentación web"""
        try:
            # CAMBIO: keytest no está documentado en la web, usar availableServices como test
            result = self._make_api_request('GET', 'availableServices/D/GB/BB4%206HH/GB/BB4%205HU')
            
            if isinstance(result, dict):
                if result.get('Status', {}).get('Code') == 'OK':
                    return {
                        'success': True,
                        'message': 'Conexión exitosa con Palletways API',
                        'data': result
                    }
                else:
                    return {
                        'success': False,
                        'message': f"Error: {result.get('Status', {}).get('Description', 'Desconocido')}",
                        'data': result
                    }
            else:
                return {
                    'success': True,
                    'message': 'Conexión exitosa (respuesta no estándar)',
                    'data': result
                }
                
        except Exception as e:
            return {
                'success': False, 
                'message': f'Error de conexión: {str(e)}',
                'data': None
            }
    
    def validate_service_code(self, service_code, service_type='Delivery'):
        """Validar código de servicio según documentación oficial"""
        # Códigos válidos según documentación
        valid_codes = {
            'Premium_Delivery': ['A', 'DY', 'E', 'F', 'H', 'O'],
            'Premium_Collection': ['C', 'AB'],
            'Economy_Delivery': ['B', 'L'],
            'Economy_Collection': ['D'],
            'European_Premium': ['0', '1', '2', '3', '4', '9'],
            'European_Economy': ['5', '6', '7', '8'],
            'Canarias': ['A1', 'A2', 'A3']
        }
        
        # Verificar si el código está en alguna categoría válida
        for category, codes in valid_codes.items():
            if service_code in codes:
                return True
        
        return False

    def _extract_validation_errors(self, validation_errors):
        """Extraer errores de validación según estructura documentada página 8"""
        error_details = []
        
        # Errores de consignación según documentación oficial
        consignment_errors = validation_errors.get('Consignment', [])
        if not isinstance(consignment_errors, list):
            consignment_errors = [consignment_errors] if consignment_errors else []
        
        for cons_error in consignment_errors:
            if isinstance(cons_error, dict):
                index = cons_error.get('Index', 'N/A')
                import_id = cons_error.get('ImportID', 'Sin ID')
                errors = cons_error.get('Error', [])
                
                if not isinstance(errors, list):
                    errors = [errors] if errors else []
                
                for error in errors:
                    if isinstance(error, dict):
                        error_code = error.get('Code', 'ERROR_UNKNOWN')
                        error_desc = error.get('Description', 'Error sin descripción')
                        error_details.append(f"Consignación {index} [{import_id}]: {error_code} - {error_desc}")
        
        # Errores de cuenta
        account_errors = validation_errors.get('Account', [])
        if not isinstance(account_errors, list):
            account_errors = [account_errors] if account_errors else []
        
        for acc_error in account_errors:
            if isinstance(acc_error, dict):
                errors = acc_error.get('Error', [])
                if not isinstance(errors, list):
                    errors = [errors] if errors else []
                
                for error in errors:
                    if isinstance(error, dict):
                        error_code = error.get('Code', 'ERROR_UNKNOWN')
                        error_desc = error.get('Description', 'Error sin descripción')
                        error_details.append(f"Cuenta: {error_code} - {error_desc}")
        
        return "\n• ".join(error_details) if error_details else "Errores de validación sin detalles"

    def get_service_description(self, service_code):
        """Obtener descripción del servicio según documentación web oficial"""
        service_descriptions = {
            # Servicios según documentación web oficial
            'A': 'Next Day Standard',
            'B': 'Economy',
            'C': 'Collection - Premium',
            'D': 'Collection - Economy',
            'DH': 'Premium Timed Delivery PM (Pre-Booked)',
            'E': 'Next Day AM',
            'F': 'Saturday AM',
            'H': 'Timed Delivery (Pre-Booked)',
            'I': 'Remote Contract Collection',
            'J': 'Economy A.M',
            'K': 'Economy Timed',
            'L': '3 Day Service',
            'N': 'Collection 3 Day',
            'O': 'Premium 48',
            'P': 'Collection 5 Day',
            'V': 'Collection Premium 48hr',
            'X': 'Collection 4 Day',
            'Z': 'Saturday Economy A.M',
            '0': 'Europe Collect Premium',
            '1': 'Europe Saturday Premium',
            '2': 'Europe 2 Day Premium',
            '3': 'Europe 3 Day Premium',
            '4': 'Europe 4+ Day Premium',
            '5': 'Europe 5 Day Economy',
            '6': 'Europe 3 Day Economy',
            '7': 'Europe 4 Day Economy',
            '8': 'Europe Collect Economy',
            '9': 'Europe Timed (Pre-Booked)',
        }
        
        return service_descriptions.get(service_code, f'Servicio {service_code}')

    def create_consignment_test(self, shipment_data):
        """Método temporal para probar sin API Key de creación"""
        _logger.info("MODO TEST: Simulando creación de envío")
        
        # Simular respuesta exitosa
        fake_response = {
            'Status': {
                'Code': 'OK',
                'Description': 'Successful (TEST MODE)'
            },
            'Detail': {
                'ImportDetail': {
                    'ResponseID': f'TEST-{int(datetime.now().timestamp())}',
                    'TrackingID': f'TEST-{shipment_data.get("reference", "000")}',
                    'Information': 'Test consignment created'
                }
            }
        }
        
        return fake_response

    def action_test_connection(self):
        """Acción para probar conexión desde interfaz"""
        result = self.test_connection()
        
        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': result['message'],
                    'type': 'success',
                }
            }
        else:
            raise UserError(result['message'])
