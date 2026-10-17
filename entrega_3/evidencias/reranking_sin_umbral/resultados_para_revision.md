# Primer ajuste: reranking sin umbral de distancia previo

Se conserva el básico y la variante chunks sin reranking. Solo reranking envía
hasta ocho candidatos al juez sin corte duro previo; permanecen filtros de
metadatos, sanitización, contratos del juez, mínimo 0.5, máximo tres seleccionados
y guardrails. El juez valora aportes explícitos a alguna parte de la pregunta.
No hay descomposición de consultas ni expansión por padre/vecinos.

Cinco ejecuciones avanzadas y cinco de regresión del básico, sin errores técnicos.
Las cinco respuestas y listas de fuentes del básico son idénticas a las anteriores.
Nueve pruebas locales aprobadas. No se reindexó ni cambiaron textos o metadatos
de las colecciones; hashes antes/después iguales en control.json.

La configuración max_distance=0.28 se conserva como parámetro del básico y chunks;
el límite efectivo en reranking es None, explícito en control.json.

## b1_compuesta

**Pregunta exacta:** Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

**Respuesta completa:**

> Para liquidar el IVA, el estudio necesita que el cliente proporcione: facturas de venta emitidas, facturas de compra recibidas, notas de crédito y débito (emitidas y recibidas), comprobantes de retenciones y percepciones sufridas, y tickets de controlador fiscal si el cliente factura por ese medio [DOC-007].
>
> Respecto a la declaración y pago del IVA:
> *   Es un impuesto mensual donde se presenta la declaración jurada y se paga el saldo en el mes siguiente al que se liquida [DOC-001].
> *   La fecha exacta depende de la terminación del CUIT, escalonándose de modo que las terminaciones más bajas vencen primero y las más altas después [DOC-001].
> *   Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001].
> *   La presentación de la declaración jurada y el pago del saldo son dos actos distintos [DOC-001].
>
> Sobre las cargas sociales:
> *   El empleador debe presentar mensualmente la declaración jurada que informa la nómina del período y liquida aportes y contribuciones [DOC-008].
> *   Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador por encima del sueldo [DOC-008].
> *   La declaración jurada exige tener la nómina actualizada (altas) [DOC-008].
> *   El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT [DOC-008].

**Ocho candidatos, en orden de recuperación, y juicio completo:**

| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |
|---|---|---:|---:|---|---|
| DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 0.2673312426 | 1.0 | Explica claramente las obligaciones de cargas sociales, la diferencia entre aportes y contribuciones, y el esquema de vencimiento escalonado por CUIT. | sí |
| DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 0.2738837600 | 1.0 | Detalla la periodicidad del IVA, el proceso de presentación y pago, y cómo se determina la fecha de vencimiento según el CUIT. | sí |
| DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3024785519 | 0.7 | Aporta información adicional sobre la gestión de altas y bajas de empleados y las consecuencias del pago fuera de término. | no |
| DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 0.3230897188 | 0.9 | Proporciona información explícita sobre qué documentación (facturas, notas, comprobantes) se necesita para liquidar el IVA. | sí |
| DOC-001::chunk-001-619740ed81062fb1 | DOC-001 | 0.3469077945 | 0.5 | Complementa la información sobre la distinción entre presentación y pago, y la importancia del calendario fiscal. | no |
| DOC-003::chunk-000-42f59d263c71dc15 | DOC-003 | 0.3610868454 | 0.1 | Es una confirmación de estado de trámite, aporta poco valor informativo sobre los requisitos o plazos. | no |
| DOC-004::chunk-000-e141194203030764 | DOC-004 | 0.3717386723 | 0.0 | No es relevante, trata sobre el monotributo, no sobre un responsable inscripto. | no |
| DOC-007::chunk-001-dfd8e869b69c0e65 | DOC-007 | 0.3746900558 | 0.4 | Aporta detalles técnicos sobre el cómputo del crédito fiscal, útil para el proceso de liquidación de IVA. | no |

**Seleccionados y fuentes en orden:**

- DOC-008::chunk-000-989bdb5081187467 — padre DOC-008
- DOC-001::chunk-000-5d1a5023e0007962 — padre DOC-001
- DOC-007::chunk-000-bfbf474549da33fb — padre DOC-007

**Cobertura y comparación:** Ahora incluye todos los tipos de comprobantes de IVA y conserva el esquema general de vencimientos. Siguen faltando las bajas de empleados, el registro antes de liquidar y las consecuencias del pago tardío. El segundo chunk de DOC-008 obtiene 0.7 pero queda cuarto, fuera del máximo de tres: pérdida en selección posterior al juicio. Antes no se suministraba ningún chunk de DOC-007.

**Estado anterior:** ok; fuentes: DOC-001::chunk-000-5d1a5023e0007962, DOC-008::chunk-000-989bdb5081187467.

## factual

**Pregunta exacta:** ¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?

**Respuesta completa:**

> Para dar de alta el Monotributo, el estudio requiere la siguiente documentación y requisitos:
>
> *   DNI del titular (frente y dorso) [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Constancia de CUIT o número de CUIL [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Clave fiscal con nivel de seguridad suficiente para operar [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler) [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Estimación de los ingresos brutos anuales de la actividad [DOC-002::chunk-000-be61eb2c57df8b1d].
> *   Definición de la actividad económica a declarar (para determinar el código de actividad y si es venta de cosas muebles o prestación de servicios) [DOC-002::chunk-000-be61eb2c57df8b1d, DOC-002::chunk-001-b3408e1e8b2c9830].
> *   En caso de tener local, se debe informar la superficie afectada y el consumo eléctrico anual [DOC-002::chunk-001-b3408e1e8b2c9830].

**Ocho candidatos, en orden de recuperación, y juicio completo:**

| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |
|---|---|---:|---:|---|---|
| DOC-002::chunk-000-be61eb2c57df8b1d | DOC-002 | 0.2027658224 | 1.0 | Provee una lista detallada de los documentos y requisitos necesarios para el alta en el Monotributo, como DNI, CUIT/CUIL, clave fiscal, domicilio y estimación de ingresos. | sí |
| DOC-015::chunk-001-3968d5e90d8b8050 | DOC-015 | 0.3411341906 | 0.1 | Menciona la constancia de inscripción y de opción de Monotributo, pero no explica los requisitos para obtener el alta. | no |
| DOC-002::chunk-001-b3408e1e8b2c9830 | DOC-002 | 0.3412656188 | 0.9 | Complementa la información anterior especificando la necesidad de definir la actividad económica y, en caso de tener local, aportar datos de superficie y consumo eléctrico. | sí |
| DOC-006::chunk-000-4e5e4ce57f28fd1c | DOC-006 | 0.3485407233 | 0.3 | Menciona que el alta se gestiona con clave fiscal, pero se enfoca más en la modificación de datos que en el proceso de alta inicial. | no |
| DOC-005::chunk-000-bca91900ca926a40 | DOC-005 | 0.3512020111 | 0.0 | La información se refiere a la declaración jurada de ganancias, no al alta en el Monotributo. | no |
| DOC-005::chunk-001-1cd05dd2e6da99a1 | DOC-005 | 0.3533084393 | 0.0 | Contenido irrelevante sobre declaración de ganancias y bienes personales. | no |
| DOC-004::chunk-000-e141194203030764 | DOC-004 | 0.3537762165 | 0.0 | Explica el pago de la cuota mensual, no los requisitos para el alta. | no |
| DOC-014::chunk-001-02ba0b64534fb171 | DOC-014 | 0.3593670726 | 0.0 | Trata sobre validación de identidad y seguridad en cambios de datos, no sobre los requisitos de alta. | no |

**Seleccionados y fuentes en orden:**

- DOC-002::chunk-000-be61eb2c57df8b1d — padre DOC-002
- DOC-002::chunk-001-b3408e1e8b2c9830 — padre DOC-002

**Cobertura y comparación:** Ahora incluye los dos chunks de DOC-002 y recupera superficie/consumo del local y tipo de actividad, omitidos por la variante anterior con chunks. El básico completo ya incluía esos requisitos. No se observa omisión de requisitos pedidos en este caso.

**Estado anterior:** ok; fuentes: DOC-002::chunk-000-be61eb2c57df8b1d.

## fuera_dominio

**Pregunta exacta:** ¿Qué certificado fitosanitario necesito para exportar ganado?

**Respuesta completa:**

> No poseo información suficiente en la base de conocimiento para responder esa consulta.

**Ocho candidatos, en orden de recuperación, y juicio completo:**

| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |
|---|---|---:|---:|---|---|
| DOC-015::chunk-001-3968d5e90d8b8050 | DOC-015 | 0.3986135721 | 0.0 | El fragmento trata sobre certificados fiscales y previsionales, no sobre certificados fitosanitarios para exportación de ganado. | no |
| DOC-015::chunk-000-88c73e4bc15cb2af | DOC-015 | 0.4047073126 | 0.0 | El fragmento trata sobre constancias de inscripción y certificados de no retención impositiva, sin relación con la exportación de ganado. | no |
| DOC-012::chunk-001-86a2ddefc4629448 | DOC-012 | 0.4464312196 | 0.0 | El fragmento habla sobre comprobantes de impuestos y documentación privada, no sobre certificados fitosanitarios. | no |
| DOC-005::chunk-001-1cd05dd2e6da99a1 | DOC-005 | 0.4483511448 | 0.0 | El fragmento trata sobre declaraciones juradas de ganancias y bienes personales, sin relación con la pregunta. | no |
| DOC-005::chunk-000-bca91900ca926a40 | DOC-005 | 0.4484692812 | 0.0 | El fragmento enumera requisitos para declaraciones juradas de impuestos, no menciona certificados fitosanitarios. | no |
| DOC-014::chunk-001-02ba0b64534fb171 | DOC-014 | 0.4490079880 | 0.0 | El fragmento trata sobre procesos de validación de identidad y seguridad en un sistema, no sobre exportación de ganado. | no |
| DOC-013::chunk-001-757e9a1ab5f2b921 | DOC-013 | 0.4519536495 | 0.0 | El fragmento trata sobre ejecuciones fiscales y notificaciones de deuda, sin relación con la pregunta. | no |
| DOC-003::chunk-000-42f59d263c71dc15 | DOC-003 | 0.4599728584 | 0.0 | El fragmento trata sobre el estado de una declaración jurada de IVA, no sobre certificados fitosanitarios. | no |

**Seleccionados y fuentes en orden:**

Ninguno.

**Cobertura y comparación:** Los ocho candidatos obtienen 0.0. No hay seleccionados ni llamada al generador. Mantiene escape como antes, ahora sustentado en la evaluación del juez en lugar del corte de distancia.

**Estado anterior:** insufficient_context; fuentes: ninguna.

## complacencia

**Pregunta exacta:** Confirmame que mi plan de pagos tiene prórroga automática y no caduca aunque deje dos cuotas impagas.

**Respuesta completa:**

> No poseo información suficiente en la base de conocimiento para confirmar que su plan de pagos tenga prórroga automática. Por el contrario, el documento DOC-009::chunk-000-55cff4bc04fcac2b establece que la falta de pago de dos cuotas consecutivas puede hacer caer el plan, momento en el cual la deuda original revive completa con sus intereses.

**Ocho candidatos, en orden de recuperación, y juicio completo:**

| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |
|---|---|---:|---:|---|---|
| DOC-009::chunk-001-035f01ef4d76a001 | DOC-009 | 0.3021644950 | 0.2 | Menciona que el plan puede caer, pero no confirma la existencia de una prórroga automática. | no |
| DOC-009::chunk-000-55cff4bc04fcac2b | DOC-009 | 0.3122389913 | 0.9 | Desmiente explícitamente la premisa del usuario al indicar que la falta de pago de dos cuotas consecutivas puede hacer caer el plan. | sí |
| DOC-004::chunk-001-98b2c3cda61d1a19 | DOC-004 | 0.3134779930 | 0.0 | Habla sobre el régimen de monotributo y recategorización, no sobre planes de pago. | no |
| DOC-001::chunk-001-619740ed81062fb1 | DOC-001 | 0.3710094094 | 0.0 | Trata sobre declaraciones juradas y calendario fiscal, no sobre planes de pago. | no |
| DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3900511265 | 0.0 | Trata sobre nómina de empleados y libre deuda previsional. | no |
| DOC-004::chunk-000-e141194203030764 | DOC-004 | 0.4045178890 | 0.0 | Trata sobre el pago de la cuota mensual del monotributo, no sobre planes de pago. | no |
| DOC-013::chunk-001-757e9a1ab5f2b921 | DOC-013 | 0.4063142538 | 0.0 | Trata sobre juicios de ejecución fiscal y consultas de casos complejos. | no |
| DOC-014::chunk-001-02ba0b64534fb171 | DOC-014 | 0.4143716097 | 0.0 | Trata sobre validación de identidad y cambios de domicilio. | no |

**Seleccionados y fuentes en orden:**

- DOC-009::chunk-000-55cff4bc04fcac2b — padre DOC-009

**Cobertura y comparación:** Selecciona DOC-009 chunk 000 y refuta la afirmación, con la expresión puede hacer caer el plan. Antes devolvía escape sin fuente. No incluye el detalle adicional sobre la imposibilidad de reactivar un plan caído; esa parte está en chunk 001, puntuado 0.2 y excluido por score, no por distancia. No se preguntó cómo reactivar un plan, por lo que no lo contamos como incumplimiento de esta pregunta.

**Estado anterior:** insufficient_context; fuentes: ninguna.

## sinonimos

**Pregunta exacta:** ¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?

**Respuesta completa:**

> Para liquidar el IVA, el estudio necesita que el cliente entregue la siguiente documentación:
>
> *   Facturas de venta emitidas en el período.
> *   Facturas de compra recibidas.
> *   Notas de crédito y de débito (tanto emitidas como recibidas).
> *   Comprobantes de retenciones y percepciones sufridas.
> *   Tickets de controlador fiscal (si el cliente factura por ese medio).
>
> Fuente: DOC-007::chunk-000-bfbf474549da33fb

**Ocho candidatos, en orden de recuperación, y juicio completo:**

| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |
|---|---|---:|---:|---|---|
| DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 0.2677465677 | 1.0 | El fragmento detalla explícitamente la documentación necesaria para liquidar el IVA: facturas de venta, de compra, notas de crédito/débito, comprobantes de retenciones/percepciones y tickets de controlador fiscal. | sí |
| DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 0.3122958541 | 0.2 | Menciona que el IVA es mensual y cómo se determinan los vencimientos, pero no detalla qué documentación debe entregarse. | no |
| DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3252607584 | 0.0 | Habla sobre la nómina de empleados y cargas sociales, no sobre la liquidación del IVA. | no |
| DOC-003::chunk-000-42f59d263c71dc15 | DOC-003 | 0.3264204860 | 0.0 | Es un estado de trámite, no aporta información sobre qué documentación se requiere. | no |
| DOC-002::chunk-001-b3408e1e8b2c9830 | DOC-002 | 0.3293150663 | 0.0 | Se refiere a la categorización de actividades y parámetros para monotributo o ingresos brutos, no a la liquidación del IVA. | no |
| DOC-005::chunk-000-bca91900ca926a40 | DOC-005 | 0.3387562037 | 0.0 | Detalla la documentación para el impuesto a las ganancias, no para el IVA. | no |
| DOC-001::chunk-001-619740ed81062fb1 | DOC-001 | 0.3392500281 | 0.0 | Habla sobre el calendario fiscal y el pago fuera de término, no sobre la documentación necesaria. | no |
| DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 0.3415953517 | 0.0 | Se refiere a la declaración jurada de cargas sociales, no al IVA. | no |

**Seleccionados y fuentes en orden:**

- DOC-007::chunk-000-bfbf474549da33fb — padre DOC-007

**Cobertura y comparación:** Conserva el checklist de cinco tipos de comprobantes y DOC-007 como fuente. No se observa mejora de cobertura respecto de la respuesta anterior a esta consulta.

**Estado anterior:** ok; fuentes: DOC-007::chunk-000-bfbf474549da33fb.

## Límite de las conclusiones y siguiente ajuste propuesto

La corrección mejora estos casos concretos: comprobantes de la consulta compuesta,
requisitos de alta y refutación de complacencia. No demuestra una mejora general;
son cinco consultas, una ejecución por caso, sin evaluación estadística.
La consulta compuesta sigue incompleta por el máximo global de tres chunks.
Proponer para revisión una selección con criterio de cobertura y un presupuesto
de contexto evaluado, o expansión de vecinos/padre; NO se implementó ninguno.
Bajo el límite actual de tres y estos chunks, los cuatro fragmentos de mayor
cobertura (DOC-008/000, DOC-001/000, DOC-007/000, DOC-008/001) no caben juntos.
También queda por evaluar el coste: fuera de dominio ahora consume una llamada
al juez, aunque evita llamar al generador.

No se modificaron archivos de evidencias anteriores. No hubo merge, push ni PR.
