# Metadatos

* **Nombre de archivo:** Palletways_API_Cliente_WebServices_2025.pdf
* **Tipo:** PDF
* **Tamaño:** N/A
* **Resolución:** N/A
* **Fecha creación/modificación:** N/A
* **Idioma detectado:** Español

# Resumen

Este documento es una guía técnica completa de la API de Palletways para clientes, que describe los webservices disponibles para integración con el sistema de gestión de envíos de pallets. Incluye requisitos técnicos, endpoints disponibles, códigos de servicios, ejemplos de XML para creación de envíos, y documentación completa de métodos para tracking, etiquetas, POD y gestión de notas. El documento está dirigido a desarrolladores que necesiten integrar sistemas ERP o de gestión con los servicios de Palletways.

# Contenido extraído

## ÍNDICE

**NOTA IMPORTANTE** . . . . . . . . . . 3  
Requisitos . . . . . . . . . . 3  
Ejemplo de parámetros. . . . . . . . . . 3  
Ejemplo general XML y campos obligatorios . . . . . . . 3  
Endpoints y métodos disponibles . . . . . . . 5  
Códigos de servicios Palletways . . . . . . . . 6  
Creación de envío y posibles respuestas . . . . . . . 6  
Solicitud de datos de un envío creado . . . . . . . . 9  
Creación de notas de un envío . . . . . . . . 10  
Solicitud de notas de un envío . . . . . . . . 11  
Solicitud de etiquetas . . . . . . . . . 12  
Solicitud de POD (comprobante de entrega) . . . . . . . 12  
Solicitud de servicios disponibles . . . . . . . 13  
Unidades facturables . . . . . . . . . 14  
Códigos de estado del envío . . . . . . . . 14  
Ejemplo de métodos . . . . . . . . . 14  
Descripción de campos . . . . . . . . 15  

## NOTA IMPORTANTE

El soporte proporcionado por Palletways acerca del proceso de integración es limitado.

**PALLETWAYS NO SE RESPONSABILIZA DEL DESARROLLO**

Para más consultas, solicitar información a: soporte_ti@palletways.com

En el caso de que el sistema no responda ocasionalmente puede deberse a que se está accediendo a la API demasiadas veces en un corto período de tiempo. El sistema aplica una prohibición temporal de IP de 15 minutos a cualquier tercero que acceda a la API más de 100 veces por minuto.

## REQUISITOS

Los requisitos básicos para una integración correcta con el PORTAL de Palletways, son:

- **CUENTA** – para acceder a PORTAL de PALLETWAYS (proporcionada por su Depot)
- **API KEY** – proporcionada por el Gerente del Depot (solicitada a soporte_it@palletways.com)
- **DESARROLLO** informático del software
- **INTRODUCCIÓN** de datos en formato XML o JSON
- **IMPRESIÓN** térmica de etiquetas (proporcionada por su Depot)

## EJEMPLO DE PARÁMETROS

Tomando como ejemplo la siguiente llamada en XML, vamos a explicar brevemente los parámetros.

`https://api.palletways.com/conStatusByTrackingId/60012340167?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D`

- `https://api.palletways.com` – Endpoint de Palletways
- `conStatusByTrackingId` – Método utilizado para solicitar los datos
- `60012340167` – Número de trackingID solicitado
- `apikey` – ApiKEY utilizada para la autentificación

## EJEMPLO GENERAL XML Y CAMPOS OBLIGATORIOS

Este es un ejemplo general en formato XML. **Todos los campos en rojo son obligatorios**.

```xml
<Manifest>
<Date>2025-03-19</Date> (opcionales – se generan solos)
<Time>13:15:00</Time> (opcionales – se generan solos)
<Confirm>yes</Confirm> (confirmación del envío – para pruebas se recomienda el valor no)
<Depot>
<Account>
<Code>Código cliente.</Code>
<Consignment>
<Type>3</Type> Tipo de servicio: C – Recogida / D – Entrega / 3 – Terceros (siempre incluir dirección de entrega y de recogida)
<ImportID>Referencia lotes.</ImportID>
<Number>Número de envío.</Number>
<Reference>Referencia cliente.</Reference>
<Lifts>2</Lifts> (número de pallets físicos)
<Weight>200</Weight> (peso total del envío)
<Handball>yes</Handball> (despaletización requerida)
<TailLift>no</TailLift> (trampilla elevadora)
<Classification>B2B</Classification> (B2B – Business to Business / B2R – Business to Residential)
<BookInRequest>yes</BookInRequest> (Cita previa)
<BookInContactName>Jose</BookInContactName> (obligatorio si BookInRequest es yes)
<BookInContactPhone>Jose</BookInContactPhone> (obligatorio si BookInRequest es yes)
<BookInContactNote>Llamar antes.</BookInContactNote> (obligatorio si BookInRequest es yes)
<BookInInstructions>Instrucciones de cita para el envio.</BookInInstructions> (obligatorio si BookInRequest es yes)
<ManifestNote>Instrucciones especiales,</ManifestNote>
<CollectionDate>2025-03-19</CollectionDate> (fecha de recogida)
<DeliveryDate>2025-03-24</DeliveryDate> (fecha de entrega)
<DeliveryTime>13:00</DeliveryTime> (hora de entrega para los envíos TIMED PRE-BOOKED – máximo de 08:00 a.m. hasta las 18:00)
<CollectionContactName> Jose </CollectionContactName> (obligatorio si el valor de Type es C o 3)
<CollectionContactNumber> 918772178</CollectionContactNumber> (obligatorio si el valor de Type es C o 3)
<CollectionReference>Referencia cliente.</CollectionReference> (obligatorio si el valor de Type es C o 3)
<DeliveryAddressContactName> Jose </DeliveryAddressContactName>
<DeliveryAddressContactNumber>918772178</DeliveryAddressContactNumber>
<Service>
<Type>Delivery</Type> (tipo de servicio)
<Code>B</Code> (código de servicio)
<Surcharge>N</Surcharge> (codigo sub-servicio)
</Service>
<Address> (datos de la entrega)
<Type> Delivery </Type> (tipo de servicio)
<ContactName> Jose </ContactName>
<Telephone>918772178</Telephone>
<Fax>0034918772178</Fax>
<CompanyName>Palletways Iberia</CompanyName>
<Line>Avenida Buenos Aires S/N</Line>
<Line>Poligono Industrial Camporroso</Line>
<Town>Alcala de Madrid</Town>
<County>Madrid</County>
<PostCode>28006</PostCode>
<Country>ES</Country>
</Address>
<Address> (datos de la recogida)
<Type>Collection</Type> (datos de la recogida)
<ContactName> Jose </ContactName>
<Telephone>918772178</Telephone>
<Fax>0034918772178</Fax>
<CompanyName>Palletways Iberia</CompanyName>
<Line>Avenida Buenos Aires S/N</Line>
<Line>Poligono Industrial Camporroso</Line>
<Town>Alcala de Madrid</Town>
<County>Madrid</County>
<PostCode>28006</PostCode>
<Country>ES</Country>
</Address>
<BillUnit> (unidades facturables)
<Type>QP</Type> (tipo de unidad facturable)
<Amount>1</Amount> (cantidad de unidades facturables)
</BillUnit>
<NotificationSet> (notificaciones del cliente)
<SysGroup>1</SysGroup> (notificación especifica)
<SysGroup>3</SysGroup> (notificación especifica)
<SMSNumber>+40618772178</SMSNumber>
<Email>soporte_ti@palletways.com</Email>
</NotificationSet>
<Product>
<LineNo>1</LineNo>
<Description>Camisetas</Description>
<Quantity>6000</Quantity>
<Code>HX120</Code> (lote)
</Product>
</Consignment>
</Account>
</Depot>
</Manifest>
```

## ENDPOINTS Y MÉTODOS DISPONIBLES

### ENDPOINTS

| ENDPOINT | URL |
|----------|-----|
| API | https://portal.palletways.com/api/ |
| API2 | https://api.palletways.com/ |

### Tabla de métodos disponibles

| METHOD NAME | DESCRIPTION | ENDPOINT | USAGE |
|-------------|-------------|----------|-------|
| addPCBUnit | Add billing unit to customer consignment | API2 | Customer |
| adviseBillingUnits | Get suggested billing units for given criteria | Both | Both |
| allNetworkServices | get list of all live services for all networks | Both | Both |
| availableBUnits | Get a list of available billing units from client's network to given network hub code (e.g. "DEHUB") | Both | Both |
| AvailableHazardousPackaging | Get list of available hazardous packaging | API2 | Both |
| availableServices | Get available services for given con type and postcodes | Both | Both |
| availableServicesLocality | Get available services for given con type, postcodes, and localities | Both | Both |
| availableSubstances | Get list of available hazardous substances | API2 | Both |
| consEntered | Get list of cons entered by customer or all depot customers for optionally given date | Both | Both |
| conStatusByConNo | Get basic information for given consignment consignment number | Both | Both |
| conStatusByCustRef | Get basic information for given consignment customer reference number | API | Both |
| conStatusById | Get basic information for given consignment Response ID | Both | Both |
| conStatusByTrackingId | Get basic information for given consignment tracking ID | Both | Both |
| createConsignment | Submit consignment | API2 | Both |
| createSystemNote | Add a note to the given consignment | API2 | Both |
| customer_invoice_detail | Get customer invoice details for given invoice number | API | Customer |
| customer_invoice_pdf | Get PDF of customer invoice for given invoice number | API | Customer |
| customer_invoices | Get list of customer invoices | API | Customer |
| deletePCConsignment | Delete an unconfirmed customer consignment | API2 | Customer |
| delPCBUnit | Remove billing unit from customer consignment | API2 | Customer |
| depotno | Get information about the given depot number (legacy/deprecated - use lookupDepotNumber) | Both | Both |
| dynStatusByTrackingId | Get basic consignment status information for given tracking ID | API | Both |
| getBarcode | Create barcode image of given number | Both | Both |
| getConByBarcode | Get con for given barcode (if barcode produced by customer) | API | Both |
| getConsignment | Get consignment details for given tracking ID | API2 | Both |
| getCustomsDocument | Get the customs document for the given filename | API2 | Both |
| getdepotfrompostcode | Get details of depot that covers given country/postcode | Both | Both |
| getDynConStatus | Get consignment details for given tracking ID | API | Both |
| getDynConStatusByConNo | Get consignment details for given consignment number (most recent as not unique) | Both | Both |
| getinvoicelines | Get invoice lines from given customer invoice number | Both | Customer |
| getLabelsByBarcode | Produce/reprint label for given barcode | API | Both |
| getLabelsByConNo | Get labels for given consignment number | Both | Customer |
| getLabelsById | Get thermal labels for given consignment Response ID, if customer is enabled to produce them | Both | Both |
| getLabelsByTID | Get labels for given tracking ID | Both | Both |
| getNotes | Get consignment notes for given criteria | API2 | Both |
| getPodByTrackingId | Get latest POD image for given tracking ID | Both | Both |
| getSystemIds | Get system/server IDs for depots | API | Both |
| getTrackingNotes | Get consignment notes for given tracking id | Both | Both |
| getTrackingNotesByConNo | Get consignment notes for given con number | Both | Customer |
| keytest | Test key is valid (returns member depot details and username) | Both | Both |
| lookupDepotId | Get details for given depot ID/syscardep | Both | Both |
| lookupDepotNo | Get information about the given depot number | Both | Both |
| lookupGeocode | Get latitude/longitude for given postcode/country | API | Both |
| lookupNetworkId | Get network details for given Network ID | API | Both |
| lookupServiceCode | Get service details for given service/surcharge/network(optional) | Both | Both |
| manifestConsignment | Confirm the given consignment Response ID to the depot | API2 | Customer |
| outstandingCons | Get list of outstanding/unconfirmed customer cons | API | Customer |
| palletconnect | Get pipe-separated list of barcodes for given customer consignment Response ID | API | Both |
| pc_confirm | Confirm the con that corresponds to the given Response ID | API | Customer |
| pc_gazeteer | Get Palletways routing/coverage information with pipekeys | API | Both |
| pc_modify | Modify customer consignment for given Response ID | API | Customer |
| pc_psief | Submit & confirm a delivery consignment | API | Customer |
| pc_psief_3rd | Submit a 3rd Party consignment | API | Customer |
| pc_psief_col | Submit a collection consignment | API | Customer |
| pc_psief_test | Submit a delivery consignment (requires later confirmation) | API | Customer |
| pc_psief_validator | Perform basic validation of delivery consignment | API | Customer |
| podimages | Get POD images for given tracking ID | API | Both |
| podpack | Get POD Pack for given customer invoice number | Both | Customer |
| putXmlSystemNote | Create a consignment note from supplied XML data | API | Both |
| requestPalletPickup | Request a pallet pickup | API | Customer |
| version | Get version number of API | API | Both |

## CÓDIGOS DE SERVICIOS PALLETWAYS

| SERVICIO | SERVICE GROUP CODE | SURCHARGE CODE | SERVICE GROUP NAME | SURCHARGE NAME | SHORT CODE |
|----------|-------------------|----------------|-------------------|----------------|------------|
| **RECOGIDAS** | | | | | |
| | A3 | A3 | PREMIUM | ISLAS CANARIAS | - |
| | A | AB | PREMIUM | 48H | P48COL |
| | A | C | PREMIUM | 24H | COND |
| | B | D | ECONOMY | 48H | COEC |
| **ENTREGAS** | | | | | |
| | A | A | PREMIUM | 24H | ND |
| | A | A1 | PREMIUM | ISLAS 7D | - |
| | A | A2 | PREMIUM | ISLAS 9D | - |
| | A | DY | PREMIUM | 14H | ND14H |
| | A | E | PREMIUM | 12H | NDAM |
| | A | F | PREMIUM | SABADO | SAT |
| | A | H | PREMIUM | TIMED (PRE-BOOKED) | TIMED |
| | A | O | PREMIUM | 48H | P48COL |
| | B | B | ECONOMY | 48H | ECON |
| | B | L | ECONOMY | 72H | E3D |
| **INTERNACIONALES** | | | | | |
| | E | 0 | PREMIUM | COLLECT | EUCOL |
| | E | 1 | PREMIUM | SATURDAY | EUSAT |
| | E | 2 | PREMIUM | 2 DAY | EU2D |
| | E | 3 | PREMIUM | 3 DAY | EU3D |
| | E | 4 | PREMIUM | 4+ DAY | EU4D |
| | E | 9 | PREMIUM | TIMED (PRE-BOOKED) | EUTIME |
| | G | 5 | ECONOMY | 5 DAY | EU5D |
| | G | 6 | ECONOMY | 3 DAY | EU3DEC |
| | G | 7 | ECONOMY | 4 DAY | EU4DEC |
| | G | 8 | ECONOMY | COLLECT | EUCOEC |

## CREACIÓN DE ENVÍO Y POSIBLES RESPUESTAS

Para crear un envío en el sistema Palletways se debe utilizar el siguiente tipo de llamada especificando el método createConsignment.

```
https://api.palletways.com/createConsignment?apikey=API KEY&commit=yes&inputformat=xml&outputformat=xml&data=<MANIFEST>
```

Cuando el sistema reciba los datos del envío estructurados correctamente en formato XML o JSON, los validará y emitirá una respuesta indicando si los datos han sido validados y enviados al sistema.

Esta llamada se puede solicitar a través del método GET o el método POST.

Si el valor del parámetro commit es yes el sistema Palletways almacenara los datos.

(los valores de los parámetros pueden ser "true", "t", "yes", "y", "on" o "1" / "false", "f", "no", "n", "off" o "0")

**PARA PRUEBAS MANTENER EL VALOR DEL PARÁMETRO DE VALIDACIÓN COMMIT EN "NO".**

### Ejemplo de creación de envío

```
https://api.palletways.com/createConsignment?apikey=2CxU7TBmgM%3D&commit=yes&inputformat=xml&outputformat=xml&data=
```

```xml
<Manifest>
<Date>2024-10-31</Date>
<Time>18:25:00</Time>
<Confirm>yes</Confirm>
<Depot>
<Account>
<Code>434481</Code>
<Consignment>
<Type>D</Type>
<Number>31102</Number>
<Reference>Palletways</Reference>
<Lifts>2</Lifts>
<Weight>100</Weight>
<Handball>no</Handball>
<TailLift>no</TailLift>
<Classification>B2B</Classification>
<BookInRequest>false</BookInRequest>
<ManifestNote>Test</ManifestNote>
<CollectionDate>2025-10-31</CollectionDate>
<DeliveryDate>2025-11-04</DeliveryDate>
<Service>
<Type>Delivery</Type>
<Code>A</Code>
<Surcharge>A</Surcharge>
</Service>
<Address>
<Type>Collection</Type>
<ContactName>Cliente</ContactName>
<Telephone>924373315</Telephone>
<CompanyName>CARNES Y VEGETALES, S.L.</CompanyName>
<Line>POL. IND. EL TRADO- C/ SEVILLA S/N</Line>
<Town>MERIDA</Town>
<County>BADAJOZ</County>
<PostCode>06800</PostCode>
<Country>ES</Country>
</Address>
<Address>
<Type>Delivery</Type>
<ContactName>CARNES Y VEGETALES</ContactName>
<Telephone>678345987</Telephone>
<CompanyName>CENTROS COMERCIALES </CompanyName>
<Line>LA ISLA , NAVE 50</Line>
<Town>CARMONA</Town>
<County>SEVILLA</County>
<PostCode>41700</PostCode>
<Country>ES</Country>
</Address>
<BillUnit>
<Type>QP</Type>
<Amount>1</Amount>
</BillUnit>
<BillUnit>
<Type>LP</Type>
<Amount>1</Amount>
</BillUnit>
</Consignment>
</Account>
</Depot>
</Manifest>
```

Las posibles respuestas varían, dependiendo de la validez de los datos proporcionados y el valor del parámetro commit.

### Respuestas del sistema

En el caso de que los datos sean válidos y el valor del parámetro commit es no, el sistema Palletways emitirá la siguiente respuesta:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>OK</Code>
<Description>Successful</Description>
</Status>
<Detail>
<Message>No data has been imported as it was not requested.</Message>
</Detail>
</Response>
```

Si el valor del parámetro commit es yes, recibirá la siguiente respuesta:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>OK</Code>
<Description>Successful</Description>
</Status>
<Detail>
<ImportDetail>
<ImportID></ImportID>
<ResponseID>3972953</ResponseID>
<Information>Consignment type:Delivery.</Information>
</ImportDetail>
</Detail>
</Response>
```

Si la estructura XML o JSON tiene un formato invalido, la respuesta será:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>ERROR_FORMAT_INVALID</Code>
<Description>The supplied data could not be imported in the stated input format.</Description>
</Status>
</Response>
```

Cuando los datos proporcionados son inválidos, un ejemplo de una respuesta podría ser:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>ERROR_VALIDATION</Code>
<Description>Validation errors occurred. No data has been imported.</Description>
</Status>
<ValidationErrors>
<Consignment>
<Index>1</Index>
<ImportID>CustID:123</ImportID>
<Error>
<Code>ERROR_CONSIGNMENT_TYPE_MANDATORY</Code>
<Description>[Consignment] provided does not contain the required [Type] node.</Description>
</Error>
<Error>
<Code>ERROR_BILLUNIT_AMOUNT_VALUE</Code>
<Description>BillUnit [Amount] is not in the required [unsignedinteger] format. Value provided = [-3]</Description>
</Error>
</Consignment>
<Consignment>
<Index>2</Index>
<ImportID>CustID:124</ImportID>
<Error>
<Code>ERROR_CONSIGNMENT_TYPE_MANDATORY</Code>
<Description>[Consignment] provided does not contain the required [Type] node.</Description>
</Error>
</Consignment>
</ValidationErrors>
</Response>
```

## SOLICITUD DE DATOS DE UN ENVÍO CREADO

Para solicitar información sobre un envío previamente creado, se debe utilizar la siguiente llamada con el método getConsignment.

```
https://api.palletways.com/getConsignment/60012340167?apikey=T9CG8Jbni2RVTKhelJfF7Z7kjy%2CxU7TBmgM%3D&outputformat=xml
```

A continuación, podemos observar un ejemplo de una respuesta de la solicitud de un envío.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>OK</Code>
<Description>Successful</Description>
<Count>1</Count>
</Status>
<Detail>
<Data>
<Manifest>
<Date>2024-10-23</Date>
<Time>18:06</Time>
<Depot>
<Number>564</Number>
<Account>
<Name>CONSERVAS, S.A.</Name>
<Code>4300123</Code>
<Consignment>
<Number>2557391-564</Number>
<TrackingID>60012340167</TrackingID>
<Type>3</Type>
<Classification>B2B</Classification>
<CollectionReference>CONSERVAS</CollectionReference>
<Lifts>1</Lifts>
<Weight>110.00</Weight>
<HandBall>no</HandBall>
<TailLift>no</TailLift>
<ADRGoods>no</ADRGoods>
<LimitedQuantityGoods>no</LimitedQuantityGoods>
<Insurance>LOTT</Insurance>
<PaperworkType>PALLETWAYS</PaperworkType>
<CollectionDepot>563</CollectionDepot>
<DeliveryDepot>525</DeliveryDepot>
<DueDate>2025-10-28</DueDate>
<DueTime>20:00</DueTime>
<BookedIn>yes</BookedIn>
<BookInRequest>yes</BookInRequest>
<BookInContactName>JUAN</BookInContactName>
<BookInEmailAddress></BookInEmailAddress>
<BookInReference>Rechazada.</BookInReference>
<Pallet>B00432B6FE</Pallet>
<BillUnit>
<Type>MQP</Type>
<Amount>1</Amount>
</BillUnit>
<Service>
<Type>Delivery</Type>
<Code>A</Code>
<Surcharge>A</Surcharge>
</Service>
<Service>
<Type>Collection</Type>
<Code>A</Code>
<Surcharge>C</Surcharge>
</Service>
<Address>
<Type>Collection</Type>
<ContactName>VALVULAS</ContactName>
<CompanyName>VALVULAS S.L.</CompanyName>
<Line>POL. IND. NEINOL</Line>
<Line>C/ TRIGO 5 NAVE F4</Line>
<Addr1>POL. IND. NEINOL</Addr1>
<Town>GUIPÚZCOA (POBLACIONES)</Town>
<County>GUIPUZCOA</County>
<Country>ES</Country>
<PostCode>20018</PostCode>
<Telephone>943722418</Telephone>
</Address>
<Address>
<Type>Delivery</Type>
<ContactName>JUAN</ContactName>
<CompanyName>CONSERVAS </CompanyName>
<Line>CTRA. DE CALFORRA, KM.11</Line>
<Addr1>CTRA. DE CALFORRA, KM.11</Addr1>
<Town>RIOJA, LA (POBLACIONES)</Town>
<County>LA RIOJA</County>
<Country>ES</Country>
<PostCode>26560</PostCode>
<Telephone>941 401 328</Telephone>
</Address>
<Hub>
<Sequence>1</Sequence>
<Name>Zaragoza</Name>
</Hub>
</Consignment>
</Account>
</Depot>
</Manifest>
</Data>
</Detail>
</Response>
```

Para envíos con paso por múltiples HUBs, en la respuesta se aparecerá un grupo `<Hub>` conteniendo el número de secuencia de paso y el nombre del HUB como, por ejemplo:

```xml
<Hub>
<Sequence>1</Sequence>
<Name>Fradley</Name>
</Hub>
<Hub>
<Sequence>2</Sequence>
<Name>Ruhr</Name>
</Hub>
```

## CREACIÓN DE NOTAS EN UN ENVÍO

Para crear una nota en el envío, se utiliza el método createSystemNote.

```
https://api.palletways.com/createSystemNote?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D&commit=yes&inputformat=xml&outputformat=xml&data=
```

```xml
<notes>
<header>
<create_date>11/09/17</create_date>
<create_time>13:46</create_time>
<orig_filename>misnotas.xml</orig_filename>
<notes_qty>2</notes_qty>
</header>
<note>
<pw_id>60012340167</pw_id>
<barcode>B1244ABCDE</barcode>
<note_create_date>11/09/17</note_create_date>
<note_create_time>13:45</note_create_time>
<customer_name>Nombre cliente 1</customer_name>
<bin_ref>Referencia 1</bin_ref>
<free_text>Texto nota 1</free_text>
<note_group>JIN</note_group>
<note_type>GIN</note_type>
<note_description></note_description>
</note>
<note>
<pw_id>60012340167</pw_id>
<barcode>B1244ABCDE</barcode>
<note_create_date>11/09/17</note_create_date>
<note_create_time>13:46</note_create_time>
<customer_name>Nombre cliente 2</customer_name>
<bin_ref>Referencia 2</bin_ref>
<free_text>Texto nota 2</free_text>
<note_group>JIN</note_group>
<note_type>GIN</note_type>
<note_description></note_description>
</note>
</notes>
```

Igual que en la creación de un envío, la respuesta del sistema Palletways sobre la creación de una nota en el envío, dependerá del valor del parámetro commit, de la validez de los datos y del formato.

## SOLICITUD DE NOTAS DE UN ENVÍO

Para la solicitud de las notas de un envío se utiliza el método getNotes. Se pueden solicitar por trackingID, por número de envío, por rango de fechas y por la última actualización tal y como se muestra en los siguientes ejemplos.

**TrackingID**
```
https://api.palletways.com/getNotes/trackingId/60012340167?apikey=T9CG8Jbni2RVTyH$2CyQelJfF7Z7kjy%2CxU7TBmgM%3D&output=xml
```

**Número de envío**
```
https://api.palletways.com/getNotes/conNo/100-63528?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D&output=xml
```

**Rango de fechas**
```
https://api.palletways.com/getNotes/dateRange/2025-07-20/11:45:00/2025-07-28/16:05:23?apikey=T9CG8Jbni2RVTyH$uyys3D&output=xml
```

**Última actualización**
```
https://api.palletways.com/getNotes/delta/1493826173?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D&output=xml
```

(1493826173 – valor epoch - representa la fecha y el tiempo desde cuando las notas de actualización son requeridas)

Si la solicitud es inválida, el sistema emitirá un mensaje de error. Normalmente, las solicitudes inválidas son causadas por:

- URL incorrecta
- Sintaxis incorrecta en la URL
- Inclusión de un numero de seguimiento en la URL
- APIKEY incorrecta

A continuación, podemos observar un ejemplo corto de la respuesta que el sistema Palletways ofrece al solicitar notas de un envío a través del método getNotes/trackingID.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>OK</Code>
<Description>Successful</Description>
<Count>27</Count>
</Status>
<Detail>
<Data>
<Delta>1730220158</Delta>
<TrackingID>60012340167</TrackingID>
<ConNo>2557791-100</ConNo>
<SysNote>21971</SysNote>
<Barcode></Barcode>
<NoteDate>2024-10-29</NoteDate>
<NoteTime>17:42:38</NoteTime>
<PodDate></PodDate>
<PodTime></PodTime>
<PodSignature></PodSignature>
<BookInDate>2024-10-30</BookInDate>
<BookInTime>20:00:00</BookInTime>
<BookInContact>Juan</BookInContact>
<BookInReference>Redireccionada 60012340268</BookInReference>
<NoteText>Reprogramado por Operaciones.</NoteText>
<StatusCode>0</StatusCode>
<NoteGroup>BIN</NoteGroup>
<NoteType>BIN</NoteType>
<NoteCodeID>32</NoteCodeID>
</Data>
</Detail>
</Response>
```

## SOLICITUD DE ETIQUETAS

Para la solicitud de una etiqueta al sistema Palletways existen varios métodos (consultar métodos disponibles – página 5). Para ofrecer un ejemplo de solicitud de etiqueta utilizaremos el método getLabelsByTID el cual necesita un trackingID para devolver la etiqueta en formato PDF.

También puede configurar su aplicación para enviar el archivo PDF directamente a la impresora y utilizar el valor /degrees para especificar el ángulo de rotación (90,180, 270) de la etiqueta.

```
https://api.palletways.com/getLabelsByTID/60012340167?apikey=T9CG8Jbni2RVTyH$2CyQM7kjy7TBmgM 7KlJfF7Z7kjy%2CxU7TBmgM%3D
```

```
https://api.palletways.com/getLabelsByTID/60012340167/degrees/90?apikey=T9CG8Jbni2RVTyH$2CyQM7KhlJfF7Z7kjy%2CxU7TBmgM%3D
```

En el caso de que la solicitud contenga datos inválidos, error de sintaxis o envío no localizable, el sistema de Palletways emitirá las siguientes respuestas:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>NO_RESULTS_FOUND</Code>
<Count>0</Count>
<Description>No results found.</Description>
</Status>
<Detail>
<Data></Data>
</Detail>
</Response>
```

**ERROR**
There was an error generating this label: consignment data not found. Either the consignment does not exist, or your account is not configured to produce labels. Please contact Palletways Support

## SOLICITUD DE POD (comprobante de entrega)

Para solicitar la imagen del albarán de entrega o POD (Proof Of Delivery), se utiliza el método getPodByTrackingId. Igual que en las etiquetas, el sistema Palletways devolverá el POD en formato PDF y también es posible configurar su aplicación para enviar el archivo directamente a la impresora.

```
https://api.palletways.com/getPodByTrackingId/60012340167?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D
```

Si la solicitud contiene datos inválidos recibirá un mensaje de error similar a los que se muestra a continuación:

- The requested API is not available. (método inválido)
- ERROR: POD not found for this ID. (trackingID inválido)
- API Key not specified. (parámetro inválido)
- The API key provided is not authorised to use the requested API. (API Key inválida)

## SOLICITUD DE SERVICIOS DISPONIBLES

La solicitud de servicios disponibles se efectúa a través del método availableServices especificando los siguientes parámetros a parte de la apikey y el outputformat:

- Tipo de envío – (D, C y 3) – (entrega, recogida y terceros)
- País de origen – (ej. ES) – (código ISO del país)
- CP país origen – (ej. 28007) – (código postal del punto de recogida)
- País de destino – (ej. ES) – (código ISO país de destino)
- CP país destino – (ej. 28009) – (código postal del punto de entrega)

En definitiva, la solicitud debería quedar tal y como se muestra en el ejemplo siguiente:

```
https://api.palletways.com/availableServices/D/ES/28007/ES/28009?apikeyT9CG8Jbni2RVTyH$2CyQ%3D&outputformat=xml
```

Si la solicitud se ha efectuado correctamente, recibirá una respuesta similar a la que se muestra a continuación:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Status>
<Code>OK</Code>
<Description>Successful</Description>
<Count>16</Count>
</Status>
<Detail>
<Data>
<id>26</id>
<ServiceGroupCode>B</ServiceGroupCode>
<ServiceCode>D</ServiceCode>
<ServiceName>ECONOMY COLLECTION 48 HOUR</ServiceName>
<ServiceGroupName>ECONOMY</ServiceGroupName>
<ServiceDaysMin>2</ServiceDaysMin>
<ServiceDaysMax>2</ServiceDaysMax>
<ServiceType>Collection</ServiceType>
<Label_Shed>K</Label_Shed>
</Data>
<Data>
<id>941</id>
<ServiceGroupCode>F</ServiceGroupCode>
<ServiceCode>S</ServiceCode>
<ServiceName>DAMAGE RETURNS</ServiceName>
<ServiceGroupName>FREE SERVICES</ServiceGroupName>
<ServiceDaysMin>3</ServiceDaysMin>
<ServiceDaysMax>3</ServiceDaysMax>
<ServiceType>Collection</ServiceType>
<Label_Shed>K</Label_Shed>
</Data>
</Detail>
</Response>
```

### Tags / Campos disponibles

```xml
<data>
<ServiceGroupCode> Código del servicio principal
<ServiceCode> Código del Subservicio
<ServiceName> Nombre completo del servicio
<ServiceGroupName> Nombre completo del grupo de servicio
<ServiceDaysMin> Número mínimo de días para completar el servicio
<ServiceDaysMax> Número máximo de días para completar el servicio
<ServiceType> Tipo de servicio (delivery – collection)
<Label_Shed> Letra del HUB al que se envía la expedición
</data>
```

## UNIDADES FACTURABLES

Para introducir los códigos de cada tipo de pallet, se utilizan siempre las primeras letras de los nombres de las unidades facturables, por ejemplo, para un Full Pallet el código corto será FP.

| Tipo | Código | Peso Máximo | Altura Máxima |
|------|--------|-------------|---------------|
| MINI QUARTER PALLET | MQP | 150 kg | 0.8m |
| QUARTER PALLET | QP | 300 kg | 1.1m |
| SUPER EURO LIGHT PALLET | SELP | 600 kg | 1.2m |
| HALF PALLET | HP | 300 kg | 1.4m |
| EXTRA LIGHT PALLET | ELP | 450 kg | 1.5m |
| LIGHT PALLET | LP | 750 kg | 1.7m |
| FULL PALLET | FP | 1200 kg | 2.2m |

## CÓDIGOS DE ESTADO DEL ENVÍO

Para conocer el estado del envío, se puede solicitar a través del número de tracking ID o a través del número de envío. (getDynConStatus / getDynStatusByConNo)

```
https://portal.palletways.com/api/getdynconstatus/60034359578?apikey=uKawbBApYhapbuqHvjtH1X460SI%3D&output=xml
```

```
https://api.palletways.com/getdynconstatusbyconno/211817?apikey=uKawbBApYhapbmeLLVXVvPfYX460SI%3D&output=xml
```

| Código | Descripción | Código | Descripción |
|--------|-------------|--------|-------------|
| 15 | REJECTED - Petición de recogida rechazada | 525 | AT INTERNATIONAL HUB - En HUB internacional |
| 25 | TO REQUEST - Petición de recogida a ser solicitada | 530 | DEPART INTERNATIONAL HUB - Salió del HUB internacional |
| 30 | AWAITING ACCEPT - Petición de recogida esperando aceptación | 550 | DEPARTED HUB - Salió del HUB |
| 50 | REQUESTED - Petición de recogida aceptada | 675 | STOCK HELD - Bloqueado en destino |
| 100 | NOT BARCODED - Sin código de barras | 700 | AT DELIVERY DEPOT - En Depot de entrega |
| 300 | IN COLLECTION DEPOT - En Depot de recogida | 800 | OUT FOR DELIVERY - En reparto |
| 350 | TRUNKED TO HUB - De camino al HUB | 900 | JOB COMPLETE - Trabajo finalizado |
| 500 | AT THE HUB - En HUB |

## EJEMPLO DE MÉTODOS

**TODOS LOS MÉTODOS DISPONIBLES SE ENCUENTRAN REFLEJADOS EN LA PÁGINA 5**

**podimages** – descarga múltiple de PODs de un mismo envío
```
https://portal.palletways.com/api/rpodimages/60012340167?apikey=T9CG8Jbni288Jbni2RVTMdJlyasgjbni2RVTM%RVTM%3D
```

**consEntered** – envíos introducidos por el cliente en una determinada fecha
```
https://portal.palletways.com/api/consEntered/2025-04-22?apikey=T9CG8Jbni288Jbnivd2RVTMJlyasgjbni2RVTM%RVTM%3D
```

(si no introduce una fecha determinada automáticamente se asume la fecha de hoy)

**conStatusById** – información sobre un envío previamente introducido especificando el ResponseID
```
https://portal.palletways.com/api/conStatusById/53040783?apikey=T9CG8Jbni288Jbnivd2Ri2RVTM%RVTM%3D&output=xml
```

**conStatusByTrackingId** – obtiene los detalles de un envío proporcionando el trackingID
```
https://portal.palletways.com/api/conStatusById/60012340167?apikey=T9CG8Jbni288J2Ri2fRVTM%RVTM%3D&output=xml
```

**availableServicesLocality** – proporciona los detalles de los servicios de una determinada población
```
https://api.palletways.com/availableServicesLocality/D/ES/28007/ARG4/ES/28009/ARG7?apikeyT9CG8Jbni2RVTH$2CyQ%3D
```

ARG4 – nombre de la población de recogida / ARG7 – nombre de la población de entrega (ver pág. 17)

**adviseBillingUnits** – sugiere las unidades facturables basada en el peso y dimensiones
```
https://portal.palletways.com/api/adviseBillingUnits/ES/28007/ES/28009/ARG5/ARG6/ARG7/ARG8?apikeyT9CG8H$2CyQ%3D
```

ARG5 – peso (kg) / ARG6 -altura (m) / ARG7 – anchura (m) / ARG8 – fondo

## DESCRIPCIÓN DE CAMPOS

| Campo | Descripción |
|-------|-------------|
| `<dc_syscon>` | Tracking ID |
| `<d_shift-asn>` | Fecha de introducción |
| `<i_sysxsn>` | XSN ID – código interno de manifiesto |
| `<c_transaction>` | Tipo de transacción (D entrega / C recogida / 3 terceros) |
| `<i_syscarrier>` | Red Palletways de entrada |
| `<c_account>` | Cuenta cliente |
| `<c_carcon>` | Número de envío |
| `<c_cusref>` | Referencia de Cliente |
| `<dc_weight>` | Peso en Kilos |
| `<c_insure>` | Seguro |
| `<i_pay-syscardep>` | Número de Depot que paga/ordena el servicio |
| `<i_syscardep>` | Número de Depot que recoge |
| `<c_c-round>` | Identificador International del Depot de recogida |
| `<c_service>` | Servicio |
| `<i_c-sysaddress>` | Dirección de recogida |
| `<i_d-sysaddress>` | Dirección de entrega |
| `<l_c-business>` | Albarán de entrega (yes -> albarán Palletways / no-> de cliente) |
| `<i_d-syscardep>` | Depot de entrega |
| `<c_d-round>` | Identificador International del Depot de entrega |
| `<i_d-syscarrier>` | Red Palletways de entrega |
| `<c_d-service>` | Servicio de entrega |
| `<c_d-surcharge>` | Sub-servicio de entrega |
| `<l_d-business>` | No Usado |
| `<d_duedate>` | Fecha de entrega |
| `<i_duetime>` | Hora de entrega |
| `<c_c-surcharge>` | Sub-servicio de recogida |
| `<c_insurance>` | Peso asegurado |
| `<l_handball>` | Entrega manual / Despaletización solicitada (yes/no) |
| `<l_taillift>` | Necesaria trampilla elevadora para entrega (yes/no) |
| `<c_physical>` | Siempre "PL" -> pallet |
| `<l_bin>` | Cita de entrega establecida |
| `<l_printed>` | Nota de entrega impresa |
| `<l_barcodes>` | No Usada |
| `<l_image>` | Hard Copy |
| `<l_binrequest>` | Solicitar cita (detalles del contacto para concertar cita entrega) |
| `<c_binContact>` | Nombre de contacto para solicitud de cita |
| `<c_accname>` | Nombre de cuenta de cliente |
| `<l_DelPaper>` | Confirmado albarán de entrega |
| `<for_i_syscardep>` | Identificador internacional Depot de entrega |
| `<for_DepotNumber>` | Número Depot de entrega |

# Imágenes y diagramas

* **Imagen 1 (página 10):** Etiqueta de envío Palletways con los siguientes elementos visibles:
  - Código "E550" prominente
  - Tipo de servicio "ECON" (Economy 48h)
  - Compañía de destino: "EMPRESA DESTINO"
  - Dirección de destino
  - Código de barras del envío para despegar (3 ETQs)
  - "BOOK IN" con código QR
  - Información del remitente: "FROM: Palletways Iberia S.L."
  - REF y TRACKING: 60000966585
  - Código postal de destino: AZUQUECA DE HENARES GUADALAJARA
  - Peso total: 799.00 kg
  - Enviado: 05.05.2020
  - Depot origen

* **Imagen 2 (página 12):** Diagrama de unidades facturables mostrando diferentes tipos de pallets con sus dimensiones y pesos máximos, desde MINI QUARTER PALLET (MQP) hasta FULL PALLET (FP).

# Pies de página / Notas

- Para pruebas mantener el valor del parámetro de validación COMMIT en "NO"
- Palletways NO SE RESPONSABILIZA DEL DESARROLLO
- El sistema aplica una prohibición temporal de IP de 15 minutos a cualquier tercero que acceda a la API más de 100 veces por minuto
- Contacto para soporte: soporte_ti@palletways.com

# Errores/Incógnitas detectadas

* **Página 4:** Algunos caracteres especiales en URLs podrían estar mal codificados debido a limitaciones del OCR (símbolos % y caracteres de escape)
* **Página 10:** La imagen de la etiqueta contiene texto pequeño que podría no haberse transcrito completamente
* **Varias páginas:** Algunos acentos y caracteres especiales podrían haberse perdido en el proceso de OCR (ñ, í, ó, etc.)
* **Página 13:** El término "ARG4/ARG7" se refiere a argumentos en URLs pero la página 17 mencionada no está disponible en este documento
* **URLs con API keys:** Algunas API keys en los ejemplos podrían tener caracteres mal interpretados por el OCR
* **Códigos de barras:** Los códigos de barras en las imágenes no son legibles por OCR y se han omitido

# Texto completo (sin formato)

PALLETWAYS API CLIENTE WEBSERVICES 2025 ÍNDICE NOTA IMPORTANTE 3 Requisitos 3 Ejemplo de parámetros 3 Ejemplo general XML y campos obligatorios 3 Endpoints y métodos disponibles 5 Códigos de servicios Palletways 6 Creación de envío y posibles respuestas 6 Solicitud de datos de un envío creado 9 Creación de notas de un envío 10 Solicitud de notas de un envío 11 Solicitud de etiquetas 12 Solicitud de POD comprobante de entrega 12 Solicitud de servicios disponibles 13 Unidades facturables 14 Códigos de estado del envío 14 Ejemplo de métodos 14 Descripción de campos 15 NOTA IMPORTANTE El soporte proporcionado por Palletways acerca del proceso de integración es limitado PALLETWAYS NO SE RESPONSABILIZA DEL DESARROLLO Para más consultas solicitar información a soporte_ti@palletways.com En el caso de que el sistema no responda ocasionalmente puede deberse a que se está accediendo a la API demasiadas veces en un corto período de tiempo El sistema aplica una prohibición temporal de IP de 15 minutos a cualquier tercero que acceda a la API más de 100 veces por minuto REQUISITOS Los requisitos básicos para una integración correcta con el PORTAL de Palletways son CUENTA para acceder a PORTAL de PALLETWAYS proporcionada por su Depot API KEY proporcionada por el Gerente del Depot solicitada a soporte_it@palletways.com DESARROLLO informático del software INTRODUCCIÓN de datos en formato XML o JSON IMPRESIÓN térmica de etiquetas proporcionada por su Depot EJEMPLO DE PARÁMETROS Tomando como ejemplo la siguiente llamada en XML vamos a explicar brevemente los parámetros https://api.palletways.com/conStatusByTrackingId/60012340167?apikey=T9CG8Jbni2RVTyH$2CyQM7KhelJfF7Z7kjy%2CxU7TBmgM%3D https://api.palletways.com Endpoint de Palletways conStatusByTrackingId Método utilizado para solicitar los datos 60012340167 Número de trackingID solicitado apikey ApiKEY utilizada para la autentificación EJEMPLO GENERAL XML Y CAMPOS OBLIGATORIOS Este es un ejemplo general en formato XML Todos los campos en rojo son obligatorios Manifest Date Time Confirm Depot Account Code Consignment Type ImportID Number Reference Lifts Weight Handball TailLift Classification BookInRequest BookInContactName BookInContactPhone BookInContactNote BookInInstructions ManifestNote CollectionDate DeliveryDate DeliveryTime CollectionContactName CollectionContactNumber CollectionReference DeliveryAddressContactName DeliveryAddressContactNumber Service Address BillUnit NotificationSet Product Consignment Account Depot Manifest
