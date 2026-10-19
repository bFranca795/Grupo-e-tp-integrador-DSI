# Evaluación real de Parte C

## Comparación pareada

| Métrica | Basic | Rerank | Delta | Pares |
|---|---:|---:|---:|---:|
| faithfulness | 0.966667 | 1.000000 | 0.033333 | 10 |
| answer_relevancy | 0.659328 | 0.766873 | 0.107544 | 10 |
| context_precision | 0.625000 | 0.625000 | 0.000000 | 8 |
| context_recall | 0.937500 | 0.984375 | 0.046875 | 8 |

## Agregados por variante

| Métrica | Variante | Media | n |
|---|---|---:|---:|
| faithfulness | basic | 0.966667 | 10 |
| faithfulness | rerank | 1.000000 | 10 |
| answer_relevancy | basic | 0.659328 | 10 |
| answer_relevancy | rerank | 0.766873 | 10 |
| context_precision | basic | 0.625000 | 8 |
| context_precision | rerank | 0.625000 | 8 |
| context_recall | basic | 0.937500 | 8 |
| context_recall | rerank | 0.984375 | 8 |

## Métricas individuales

| ID | Variante | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|---|
| S1 | basic | 1.000000 (ok) | 0.974338 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| S1 | rerank | 1.000000 (ok) | 0.987831 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| S2 | basic | 0.666667 (ok) | 0.965264 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| S2 | rerank | 1.000000 (ok) | 0.995098 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| S3 | basic | 1.000000 (ok) | 0.998693 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| S3 | rerank | 1.000000 (ok) | 0.998693 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| C1 | basic | 1.000000 (ok) | 0.885480 (ok) | 0.000000 (ok) | 0.750000 (ok) |
| C1 | rerank | 1.000000 (ok) | 0.931874 (ok) | 0.000000 (ok) | 0.875000 (ok) |
| C2 | basic | 1.000000 (ok) | 0.000000 (ok) | 0.000000 (ok) | 0.750000 (ok) |
| C2 | rerank | 1.000000 (ok) | 0.977715 (ok) | 0.000000 (ok) | 1.000000 (ok) |
| C3 | basic | 1.000000 (ok) | 0.981091 (ok) | 0.000000 (ok) | 1.000000 (ok) |
| C3 | rerank | 1.000000 (ok) | 0.985851 (ok) | 0.000000 (ok) | 1.000000 (ok) |
| E1 | basic | 1.000000 (ok) | 0.000000 (ok) | — (not_applicable) | — (not_applicable) |
| E1 | rerank | 1.000000 (ok) | 0.000000 (ok) | — (not_applicable) | — (not_applicable) |
| E2 | basic | 1.000000 (ok) | 0.000000 (ok) | — (not_applicable) | — (not_applicable) |
| E2 | rerank | 1.000000 (ok) | 0.000000 (ok) | — (not_applicable) | — (not_applicable) |
| I1 | basic | 1.000000 (ok) | 0.887711 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| I1 | rerank | 1.000000 (ok) | 0.885993 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| I2 | basic | 1.000000 (ok) | 0.900706 (ok) | 1.000000 (ok) | 1.000000 (ok) |
| I2 | rerank | 1.000000 (ok) | 0.905672 (ok) | 1.000000 (ok) | 1.000000 (ok) |

## Exclusiones pareadas

- faithfulness: ninguna
- answer_relevancy: ninguna
- context_precision: [{"id": "E1", "states": {"basic": {"status": "not_applicable", "reason": "no_positive_factual_reference"}, "rerank": {"status": "not_applicable", "reason": "no_positive_factual_reference"}}}, {"id": "E2", "states": {"basic": {"status": "not_applicable", "reason": "no_positive_factual_reference"}, "rerank": {"status": "not_applicable", "reason": "no_positive_factual_reference"}}}]
- context_recall: [{"id": "E1", "states": {"basic": {"status": "not_applicable", "reason": "no_positive_factual_reference"}, "rerank": {"status": "not_applicable", "reason": "no_positive_factual_reference"}}}, {"id": "E2", "states": {"basic": {"status": "not_applicable", "reason": "no_positive_factual_reference"}, "rerank": {"status": "not_applicable", "reason": "no_positive_factual_reference"}}}]

## Escapes funcionales

- E1 / basic: estado insufficient_context; abstención exacta y sin contenido añadido: True.
- E1 / rerank: estado insufficient_context; abstención exacta y sin contenido añadido: True.
- E2 / basic: estado ok; abstención exacta y sin contenido añadido: True.
- E2 / rerank: estado insufficient_context; abstención exacta y sin contenido añadido: True.

## Veinte respuestas completas y fuentes

### S1 / basic

¿Qué comprobantes tengo que entregar para liquidar el IVA del mes?

Para liquidar el IVA del mes, debe entregar los siguientes comprobantes:

*   Facturas de venta emitidas en el período (DOC-007).
*   Facturas de compra recibidas (DOC-007).
*   Notas de crédito y de débito, tanto emitidas como recibidas (DOC-007).
*   Comprobantes de retenciones y percepciones sufridas (DOC-007).
*   Tickets de controlador fiscal, en caso de que facture por ese medio (DOC-007).

Estado: ok. Fuentes: DOC-007.

> DOC-007: Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega tarde no se puede computar en el período ya presentado y arrastra a una rectificativa. Las facturas de compra solo generan crédito fiscal si están a nombre del CUIT del cliente y corresponden a la actividad gravada. Los comprobantes tipo B y C emitidos a consumidor final no discriminan IVA y por eso no generan crédito fiscal computable.

### S1 / rerank

¿Qué comprobantes tengo que entregar para liquidar el IVA del mes?

Para liquidar el IVA del mes, debe entregar los siguientes comprobantes:

*   Facturas de venta emitidas en el período [DOC-007::chunk-000-bfbf474549da33fb].
*   Facturas de compra recibidas [DOC-007::chunk-000-bfbf474549da33fb].
*   Notas de crédito y de débito, tanto emitidas como recibidas [DOC-007::chunk-000-bfbf474549da33fb].
*   Comprobantes de retenciones y percepciones sufridas [DOC-007::chunk-000-bfbf474549da33fb].
*   Tickets de controlador fiscal, en caso de que el cliente facture por ese medio [DOC-007::chunk-000-bfbf474549da33fb].

Estado: ok. Fuentes: DOC-007::chunk-000-bfbf474549da33fb, DOC-007::chunk-001-dfd8e869b69c0e65.

> DOC-007::chunk-000-bfbf474549da33fb: Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega

> DOC-007::chunk-001-dfd8e869b69c0e65: sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega tarde no se puede computar en el período ya presentado y arrastra a una rectificativa. Las facturas de compra solo generan crédito fiscal si están a nombre del CUIT del cliente y corresponden a la actividad gravada. Los comprobantes tipo B y C emitidos a consumidor final no discriminan IVA y por eso no generan crédito fiscal computable.

### S2 / basic

¿Qué componentes integra la cuota mensual del Monotributo?

La cuota mensual del Monotributo integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social (DOC-004).

Estado: ok. Fuentes: DOC-004.

> DOC-004: El monotributista paga una cuota mensual única que integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social. La cuota vence todos los meses alrededor del día 20 y, si ese día no es hábil, el plazo corre al día hábil siguiente. El monto depende de la categoría vigente del contribuyente, y las categorías se actualizan periódicamente, por lo que el importe del mes puede diferir del mes anterior aunque la categoría no haya cambiado. Pagar fuera de término genera intereses y, acumulando deuda, puede derivar en la baja automática del régimen. Dos veces al año corresponde la recategorización, que revisa ingresos, superficie y energía consumida de los últimos doce meses. La recategorización es un trámite distinto del pago de la cuota y tiene su propia fecha.

### S2 / rerank

¿Qué componentes integra la cuota mensual del Monotributo?

La cuota mensual del Monotributo integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social (DOC-004::chunk-000-e141194203030764).

Estado: ok. Fuentes: DOC-004::chunk-000-e141194203030764.

> DOC-004::chunk-000-e141194203030764: El monotributista paga una cuota mensual única que integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social. La cuota vence todos los meses alrededor del día 20 y, si ese día no es hábil, el plazo corre al día hábil siguiente. El monto depende de la categoría vigente del contribuyente, y las categorías se actualizan periódicamente, por lo que el importe del mes puede diferir del mes anterior aunque la categoría no haya cambiado. Pagar fuera de término

### S3 / basic

¿Qué diferencia hay entre el comprobante de presentación y el comprobante de pago?

La diferencia es la siguiente:

*   El **comprobante de presentación** es el acuse de recibo, el cual contiene número de transacción, fecha y hora (DOC-012).
*   El **comprobante de pago** es el ticket del volante electrónico de pago o el extracto del débito, dependiendo del medio utilizado (DOC-012).

Estado: ok. Fuentes: DOC-012.

> DOC-012: El estudio entrega al cliente el comprobante de cada presentación y de cada pago que gestiona en su nombre. El comprobante de presentación es el acuse de recibo, que lleva número de transacción, fecha y hora. El comprobante de pago es el ticket del volante electrónico de pago o el extracto del débito, según el medio utilizado. Para recuperar el archivo correcto hay que identificar tres datos: el CUIT del contribuyente, el impuesto y el período fiscal. Sin los tres, la búsqueda es ambigua, porque un mismo cliente tiene un comprobante por impuesto y por mes. Los comprobantes son documentación privada del cliente y solo se entregan al titular o a quien el titular autorizó formalmente. El estudio conserva copia de cada comprobante entregado.

### S3 / rerank

¿Qué diferencia hay entre el comprobante de presentación y el comprobante de pago?

La diferencia es la siguiente:

*   El **comprobante de presentación** es el acuse de recibo, el cual contiene el número de transacción, la fecha y la hora (DOC-012::chunk-000-aab8e60566e4bda5).
*   El **comprobante de pago** es el ticket del volante electrónico de pago o el extracto del débito, dependiendo del medio utilizado (DOC-012::chunk-000-aab8e60566e4bda5).

Estado: ok. Fuentes: DOC-012::chunk-000-aab8e60566e4bda5.

> DOC-012::chunk-000-aab8e60566e4bda5: El estudio entrega al cliente el comprobante de cada presentación y de cada pago que gestiona en su nombre. El comprobante de presentación es el acuse de recibo, que lleva número de transacción, fecha y hora. El comprobante de pago es el ticket del volante electrónico de pago o el extracto del débito, según el medio utilizado. Para recuperar el archivo correcto hay que identificar tres datos: el CUIT del contribuyente, el impuesto y el período fiscal. Sin los tres, la búsqueda es ambigua, porque

### C1 / basic

Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

Para liquidar el IVA, el responsable inscripto debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT, siguiendo un escalonamiento donde las terminaciones más bajas vencen primero y las más altas después. Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente. La presentación y el pago son actos distintos; si se paga fuera de término, corren intereses resarcitorios [DOC-001].

Respecto a las cargas sociales, el empleador debe presentar mensualmente una declaración jurada que informa la nómina del período y liquida aportes y contribuciones. Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador. Es obligatorio tener la nómina actualizada, registrando altas y bajas antes de liquidar. El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional [DOC-008].

Estado: ok. Fuentes: DOC-008, DOC-001.

> DOC-008: El empleador presenta mensualmente la declaración jurada de cargas sociales, que informa la nómina del período y liquida aportes y contribuciones. Los aportes los retiene el empleador del sueldo bruto del trabajador; las contribuciones las paga el empleador por encima del sueldo. El vencimiento de la presentación y del pago cae en la segunda semana del mes siguiente al período liquidado y también se escalona por terminación de CUIT. La declaración jurada exige tener la nómina actualizada: altas y bajas de empleados deben registrarse antes de liquidar, porque un alta no registrada convierte la relación en trabajo no registrado. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional que piden muchas licitaciones.

> DOC-001: El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la declaración jurada y pagar el saldo son dos actos distintos: se puede presentar en término y pagar fuera de término, y en ese caso corren intereses resarcitorios sobre el saldo. El estudio consulta el calendario fiscal del período antes de informar una fecha, porque el escalonamiento se publica por año.

### C1 / rerank

Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

Para liquidar el IVA, el estudio necesita que el cliente proporcione: facturas de venta emitidas, facturas de compra recibidas, notas de crédito y débito (emitidas y recibidas), comprobantes de retenciones y percepciones sufridas, y tickets de controlador fiscal si utiliza ese medio [DOC-007].

Respecto a la declaración y pago del IVA:
*   Es un impuesto mensual donde se presenta la declaración jurada y se paga el saldo en el mes siguiente al que se liquida [DOC-001].
*   La fecha exacta depende de la terminación del CUIT, escalonándose de menor a mayor [DOC-001].
*   Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001].
*   La presentación y el pago son actos distintos [DOC-001].

Sobre las cargas sociales:
*   El empleador debe presentar mensualmente una declaración jurada que informa la nómina del período y liquida aportes y contribuciones [DOC-008].
*   Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador [DOC-008].
*   El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT [DOC-008].
*   Es obligatorio tener la nómina actualizada, registrando altas y bajas de empleados antes de liquidar [DOC-008].
*   El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional [DOC-008].

Estado: ok. Fuentes: DOC-008::chunk-000-989bdb5081187467, DOC-001::chunk-000-5d1a5023e0007962, DOC-007::chunk-000-bfbf474549da33fb, DOC-008::chunk-001-92e73e8b1d8ef4e4.

> DOC-008::chunk-000-989bdb5081187467: El empleador presenta mensualmente la declaración jurada de cargas sociales, que informa la nómina del período y liquida aportes y contribuciones. Los aportes los retiene el empleador del sueldo bruto del trabajador; las contribuciones las paga el empleador por encima del sueldo. El vencimiento de la presentación y del pago cae en la segunda semana del mes siguiente al período liquidado y también se escalona por terminación de CUIT. La declaración jurada exige tener la nómina actualizada: altas

> DOC-001::chunk-000-5d1a5023e0007962: El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la declaración jurada y pagar el saldo son dos actos distintos: se puede

> DOC-007::chunk-000-bfbf474549da33fb: Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega

> DOC-008::chunk-001-92e73e8b1d8ef4e4: se escalona por terminación de CUIT. La declaración jurada exige tener la nómina actualizada: altas y bajas de empleados deben registrarse antes de liquidar, porque un alta no registrada convierte la relación en trabajo no registrado. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional que piden muchas licitaciones.

### C2 / basic

¿Qué documentación necesito para darme de alta en Monotributo y qué incluye la cuota que después debo pagar?

Para dar de alta el Monotributo, el estudio requiere la siguiente documentación:

*   DNI del titular (frente y dorso).
*   Constancia de CUIT o número de CUIL.
*   Clave fiscal con nivel de seguridad suficiente para operar.
*   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler).
*   Estimación de los ingresos brutos anuales de la actividad.
*   Definición de la actividad económica a declarar (para determinar el código de actividad y si es venta de cosas muebles o prestación de servicios).
*   En caso de tener local: superficie afectada y consumo eléctrico anual.

Fuente: DOC-002.

No poseo información suficiente en la base de conocimiento para responder qué incluye la cuota que debe pagar.

Estado: ok. Fuentes: DOC-002.

> DOC-002: Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de actividad, y si la actividad es venta de cosas muebles o prestación de servicios, porque los topes de cada categoría difieren. Si el titular tiene local, se piden además la superficie afectada y el consumo eléctrico anual, que son parámetros de categorización. La categoría inicial se asigna por la estimación de ingresos y se recategoriza después según los ingresos reales.

### C2 / rerank

¿Qué documentación necesito para darme de alta en Monotributo y qué incluye la cuota que después debo pagar?

Para dar de alta el Monotributo, el estudio requiere la siguiente documentación:

*   DNI del titular (frente y dorso) [DOC-002].
*   Constancia de CUIT o número de CUIL [DOC-002].
*   Clave fiscal con nivel de seguridad suficiente para operar [DOC-002].
*   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler) [DOC-002].
*   Estimación de los ingresos brutos anuales de la actividad [DOC-002].
*   Definición de la actividad económica a declarar (código de actividad) y si se trata de venta de cosas muebles o prestación de servicios [DOC-002].
*   En caso de tener local, se requiere la superficie afectada y el consumo eléctrico anual [DOC-002].

Respecto a la cuota mensual, esta integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social [DOC-004].

Estado: ok. Fuentes: DOC-002::chunk-000-be61eb2c57df8b1d, DOC-004::chunk-000-e141194203030764, DOC-002::chunk-001-b3408e1e8b2c9830.

> DOC-002::chunk-000-be61eb2c57df8b1d: Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de

> DOC-004::chunk-000-e141194203030764: El monotributista paga una cuota mensual única que integra tres componentes: el impuesto integrado, el aporte jubilatorio y el aporte a la obra social. La cuota vence todos los meses alrededor del día 20 y, si ese día no es hábil, el plazo corre al día hábil siguiente. El monto depende de la categoría vigente del contribuyente, y las categorías se actualizan periódicamente, por lo que el importe del mes puede diferir del mes anterior aunque la categoría no haya cambiado. Pagar fuera de término

> DOC-002::chunk-001-b3408e1e8b2c9830: hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de actividad, y si la actividad es venta de cosas muebles o prestación de servicios, porque los topes de cada categoría difieren. Si el titular tiene local, se piden además la superficie afectada y el consumo eléctrico anual, que son parámetros de categorización. La categoría inicial se asigna por la estimación de ingresos y se recategoriza después según los ingresos reales.

### C3 / basic

¿Qué organismos administran Ingresos Brutos en CABA y Provincia de Buenos Aires, y qué obligaciones tiene un contribuyente local en cada jurisdicción?

Los organismos que administran el impuesto sobre los Ingresos Brutos son:

*   **CABA:** La Administración Gubernamental de Ingresos Públicos (AGIP) [DOC-010].
*   **Provincia de Buenos Aires (PBA):** La Agencia de Recaudación de la Provincia de Buenos Aires (ARBA) [DOC-011].

Las obligaciones de un contribuyente local son:

**En CABA:**
*   Presentar una declaración jurada mensual y un resumen anual [DOC-010].
*   Pagar sobre los ingresos facturados atribuibles a la jurisdicción, aplicando la alícuota correspondiente según la actividad declarada [DOC-010].
*   Cumplir con el vencimiento mensual, el cual cae en la segunda quincena y se escalona por terminación de CUIT [DOC-010].
*   Soportar retenciones y percepciones de los agentes de recaudación de la Ciudad [DOC-010].

**En PBA:**
*   Presentar una declaración jurada mensual [DOC-011].
*   Pagar sobre los ingresos atribuibles a la Provincia, con alícuotas que dependen de la actividad y del monto de ingresos del año anterior [DOC-011].
*   Cumplir con el vencimiento mensual, el cual posee un escalonamiento por terminación de CUIT propio de ARBA [DOC-011].
*   Consultar el padrón de regímenes de retención y percepción de ARBA antes de facturar para determinar la alícuota aplicable [DOC-011].

Cabe aclarar que, según lo documentado, quien tiene actividad en más de una jurisdicción no tributa como contribuyente local, sino por Convenio Multilateral [DOC-010, DOC-011].

Estado: ok. Fuentes: DOC-010, DOC-011.

> DOC-010: Ingresos Brutos en la Ciudad Autónoma de Buenos Aires es un impuesto provincial que administra la Administración Gubernamental de Ingresos Públicos, AGIP. El contribuyente local de CABA presenta una declaración jurada mensual y un resumen anual, y paga sobre los ingresos facturados atribuibles a la jurisdicción. La alícuota varía según la actividad declarada y existen actividades con alícuotas diferenciales y exenciones para determinados rubros. El vencimiento mensual cae en la segunda quincena y se escalona por terminación de CUIT. El contribuyente sufre retenciones y percepciones de los agentes de recaudación de la Ciudad, que se computan como pago a cuenta y suelen generar saldo a favor acumulado. Quien tiene actividad en más de una jurisdicción no tributa como contribuyente local sino por Convenio Multilateral, con coeficiente unificado.

> DOC-011: Ingresos Brutos en la Provincia de Buenos Aires es un impuesto provincial que administra la Agencia de Recaudación de la Provincia de Buenos Aires, ARBA. El contribuyente local de PBA presenta una declaración jurada mensual y paga sobre los ingresos atribuibles a la Provincia, con alícuotas que dependen de la actividad y del monto de ingresos del año anterior. El vencimiento mensual y el escalonamiento por terminación de CUIT son propios de ARBA y no coinciden con los de la Ciudad. ARBA publica padrones de regímenes de retención y percepción que se actualizan mensualmente, y la alícuota aplicable a cada contribuyente se consulta en ese padrón antes de facturar. El saldo a favor por retenciones y percepciones es frecuente y se puede solicitar la reducción de alícuota cuando el saldo acumulado supera cierto umbral. Quien opera en varias jurisdicciones tributa por Convenio Multilateral.

### C3 / rerank

¿Qué organismos administran Ingresos Brutos en CABA y Provincia de Buenos Aires, y qué obligaciones tiene un contribuyente local en cada jurisdicción?

Los organismos que administran el impuesto sobre los Ingresos Brutos son:

*   **CABA:** La Administración Gubernamental de Ingresos Públicos (AGIP) [DOC-010].
*   **Provincia de Buenos Aires:** La Agencia de Recaudación de la Provincia de Buenos Aires (ARBA) [DOC-011].

**Obligaciones del contribuyente local:**

*   **En CABA:** Debe presentar una declaración jurada mensual y un resumen anual, pagando sobre los ingresos facturados atribuibles a la jurisdicción. La alícuota varía según la actividad, existiendo actividades con alícuotas diferenciales y exenciones. El contribuyente sufre retenciones y percepciones de los agentes de recaudación de la Ciudad, que se computan como pago a cuenta. Los vencimientos mensuales caen en la segunda quincena y se escalonan por terminación de CUIT [DOC-010].
*   **En Provincia de Buenos Aires:** Debe presentar una declaración jurada mensual y pagar sobre los ingresos atribuibles a la Provincia. Las alícuotas dependen de la actividad y del monto de ingresos del año anterior. El contribuyente debe consultar el padrón de regímenes de retención y percepción que publica ARBA antes de facturar. Los vencimientos mensuales y su escalonamiento por terminación de CUIT son propios de ARBA [DOC-011].

Cabe aclarar que, según la documentación, quien tiene actividad en más de una jurisdicción no tributa como contribuyente local, sino por Convenio Multilateral [DOC-010, DOC-011].

Estado: ok. Fuentes: DOC-011::chunk-000-7345273c5fa84a67, DOC-010::chunk-000-c0431097960fbec4, DOC-010::chunk-001-01056046b7cf009c, DOC-011::chunk-001-dffc157246d4aead.

> DOC-011::chunk-000-7345273c5fa84a67: Ingresos Brutos en la Provincia de Buenos Aires es un impuesto provincial que administra la Agencia de Recaudación de la Provincia de Buenos Aires, ARBA. El contribuyente local de PBA presenta una declaración jurada mensual y paga sobre los ingresos atribuibles a la Provincia, con alícuotas que dependen de la actividad y del monto de ingresos del año anterior. El vencimiento mensual y el escalonamiento por terminación de CUIT son propios de ARBA y no coinciden con los de la Ciudad. ARBA publica

> DOC-010::chunk-000-c0431097960fbec4: Ingresos Brutos en la Ciudad Autónoma de Buenos Aires es un impuesto provincial que administra la Administración Gubernamental de Ingresos Públicos, AGIP. El contribuyente local de CABA presenta una declaración jurada mensual y un resumen anual, y paga sobre los ingresos facturados atribuibles a la jurisdicción. La alícuota varía según la actividad declarada y existen actividades con alícuotas diferenciales y exenciones para determinados rubros. El vencimiento mensual cae en la segunda quincena

> DOC-010::chunk-001-01056046b7cf009c: y exenciones para determinados rubros. El vencimiento mensual cae en la segunda quincena y se escalona por terminación de CUIT. El contribuyente sufre retenciones y percepciones de los agentes de recaudación de la Ciudad, que se computan como pago a cuenta y suelen generar saldo a favor acumulado. Quien tiene actividad en más de una jurisdicción no tributa como contribuyente local sino por Convenio Multilateral, con coeficiente unificado.

> DOC-011::chunk-001-dffc157246d4aead: por terminación de CUIT son propios de ARBA y no coinciden con los de la Ciudad. ARBA publica padrones de regímenes de retención y percepción que se actualizan mensualmente, y la alícuota aplicable a cada contribuyente se consulta en ese padrón antes de facturar. El saldo a favor por retenciones y percepciones es frecuente y se puede solicitar la reducción de alícuota cuando el saldo acumulado supera cierto umbral. Quien opera en varias jurisdicciones tributa por Convenio Multilateral.

### E1 / basic

¿Qué certificado fitosanitario necesito para exportar ganado?

No poseo información suficiente en la base de conocimiento para responder esa consulta.

Estado: insufficient_context. Fuentes: ninguna.

### E1 / rerank

¿Qué certificado fitosanitario necesito para exportar ganado?

No poseo información suficiente en la base de conocimiento para responder esa consulta.

Estado: insufficient_context. Fuentes: ninguna.

### E2 / basic

¿Cuánto cobra exactamente el estudio por tramitar mi alta en Monotributo?

No poseo información suficiente en la base de conocimiento para responder esa consulta (DOC-002).

Estado: ok. Fuentes: DOC-002.

> DOC-002: Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de actividad, y si la actividad es venta de cosas muebles o prestación de servicios, porque los topes de cada categoría difieren. Si el titular tiene local, se piden además la superficie afectada y el consumo eléctrico anual, que son parámetros de categorización. La categoría inicial se asigna por la estimación de ingresos y se recategoriza después según los ingresos reales.

### E2 / rerank

¿Cuánto cobra exactamente el estudio por tramitar mi alta en Monotributo?

No poseo información suficiente en la base de conocimiento para responder esa consulta.

Estado: insufficient_context. Fuentes: ninguna.

### I1 / basic

¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?

Para liquidar el IVA de un mes, debe presentar al estudio la siguiente documentación:

*   Facturas de venta emitidas en el período.
*   Facturas de compra recibidas.
*   Notas de crédito y de débito (tanto emitidas como recibidas).
*   Comprobantes de retenciones y percepciones sufridas.
*   Tickets de controlador fiscal (si factura por ese medio).

Fuente: DOC-007.

Estado: ok. Fuentes: DOC-007.

> DOC-007: Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega tarde no se puede computar en el período ya presentado y arrastra a una rectificativa. Las facturas de compra solo generan crédito fiscal si están a nombre del CUIT del cliente y corresponden a la actividad gravada. Los comprobantes tipo B y C emitidos a consumidor final no discriminan IVA y por eso no generan crédito fiscal computable.

### I1 / rerank

¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?

Para liquidar el IVA, el estudio necesita que el cliente entregue la siguiente documentación:

*   Facturas de venta emitidas en el período.
*   Facturas de compra recibidas.
*   Notas de crédito y de débito (tanto emitidas como recibidas).
*   Comprobantes de retenciones y percepciones sufridas.
*   Tickets de controlador fiscal (si el cliente factura por ese medio).

Fuente: DOC-007::chunk-000-bfbf474549da33fb

Estado: ok. Fuentes: DOC-007::chunk-000-bfbf474549da33fb.

> DOC-007::chunk-000-bfbf474549da33fb: Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio. Cada comprobante aporta crédito fiscal o débito fiscal según sea compra o venta, y el saldo del período es la diferencia entre ambos. Un comprobante que llega

### I2 / basic

Me cayó una intimación del fisco, ¿qué hago ahora?

Ante una intimación o requerimiento fiscal, debe tener en cuenta lo siguiente:

*   La notificación llega al domicilio fiscal electrónico y el plazo de respuesta corre desde que se considera notificada, independientemente de si fue leída o no (DOC-013).
*   Dejar vencer el plazo agrava la situación, habilitando multas, la determinación de oficio y, en casos de deuda firme, el juicio de ejecución fiscal (DOC-013).
*   Estas consultas requieren leer la notificación concreta, identificar el impuesto, el período y el monto reclamado, revisar si la obligación está incumplida y definir si corresponde presentar un descargo, allanarse o rectificar (DOC-013).
*   Debido a que se clasifican como casos de mayor complejidad, deben derivarse al profesional responsable con el detalle del caso (DOC-013).

El asistente no evalúa la procedencia del reclamo ni sugiere una estrategia de respuesta (DOC-013).

Estado: ok. Fuentes: DOC-013.

> DOC-013: Una intimación o un requerimiento fiscal es una notificación formal en la que el organismo reclama una presentación faltante, un pago adeudado o documentación de respaldo. La notificación llega al domicilio fiscal electrónico y corre un plazo de respuesta desde que se considera notificada, aunque el contribuyente no la haya leído. Dejar vencer el plazo agrava la situación: habilita multas, la determinación de oficio y, en casos de deuda firme, el juicio de ejecución fiscal. Estas consultas no se responden con información general. Requieren leer la notificación concreta, identificar impuesto, período y monto reclamado, revisar si la obligación efectivamente está incumplida y definir si corresponde presentar el descargo, allanarse o rectificar. Por eso se clasifican como casos de mayor complejidad y se derivan al profesional responsable con el detalle del caso. El asistente no evalúa la procedencia del reclamo ni sugiere una estrategia de respuesta.

### I2 / rerank

Me cayó una intimación del fisco, ¿qué hago ahora?

Ante una intimación o requerimiento fiscal, debe tener en cuenta lo siguiente:

*   Se trata de una notificación formal que llega al domicilio fiscal electrónico y sobre la cual corre un plazo de respuesta desde que se considera notificada, independientemente de si fue leída o no [DOC-013::chunk-000-7d57d8f61c472874].
*   Dejar vencer el plazo agrava la situación, habilitando multas, la determinación de oficio y, en casos de deuda firme, el juicio de ejecución fiscal [DOC-013::chunk-000-7d57d8f61c472874].
*   Estas consultas requieren leer la notificación concreta para identificar el impuesto, período y monto reclamado, revisar si la obligación está incumplida y definir si corresponde presentar un descargo, allanarse o rectificar [DOC-013::chunk-001-757e9a1ab5f2b921].
*   Debido a que son casos de mayor complejidad, deben derivarse al profesional responsable con el detalle del caso [DOC-013::chunk-001-757e9a1ab5f2b921].

Estado: ok. Fuentes: DOC-013::chunk-000-7d57d8f61c472874, DOC-013::chunk-001-757e9a1ab5f2b921.

> DOC-013::chunk-000-7d57d8f61c472874: Una intimación o un requerimiento fiscal es una notificación formal en la que el organismo reclama una presentación faltante, un pago adeudado o documentación de respaldo. La notificación llega al domicilio fiscal electrónico y corre un plazo de respuesta desde que se considera notificada, aunque el contribuyente no la haya leído. Dejar vencer el plazo agrava la situación: habilita multas, la determinación de oficio y, en casos de deuda firme, el juicio de ejecución fiscal. Estas consultas no se

> DOC-013::chunk-001-757e9a1ab5f2b921: de oficio y, en casos de deuda firme, el juicio de ejecución fiscal. Estas consultas no se responden con información general. Requieren leer la notificación concreta, identificar impuesto, período y monto reclamado, revisar si la obligación efectivamente está incumplida y definir si corresponde presentar el descargo, allanarse o rectificar. Por eso se clasifican como casos de mayor complejidad y se derivan al profesional responsable con el detalle del caso. El asistente no evalúa la procedencia

