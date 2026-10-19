# TP Integrador — Entrega 3: LCEL y RAG avanzado

**Estado final vigente:** A y B conservadas; B.1–B.4 completos. C.1–C.4 están cumplidos para la corrida aprobada: 20 respuestas, 72 puntuaciones válidas, 8 no aplicables y 0 errores pendientes. La comparación y sus limitaciones vigentes están en C.3/C.4.

**Lectura del historial:** desde «Estado de la entrega» hasta el cierre de B se conserva el registro histórico de A/B. Sus menciones de «sin Parte C», «sin RAGAS», pendientes de LangSmith o ausencia de push describen aquellas etapas y no el estado final.


**Estado de la entrega:** B.1–B.3 están implementados y validados en los casos
documentados. Esto no constituye una mejora general ni una evaluación RAGAS.
**B.4 cumplido:** la traza existente está contrastada por API y las capturas
complementarias completan la evidencia visual. B.1–B.4 quedan cumplidos en el
alcance de la consigna y los casos documentados; no hay pendientes obligatorios.
El chunking 500/100 se acredita con el manifiesto local, no con metadata remota.

La guía [CONTINUAR_B4.md](CONTINUAR_B4.md) se conserva para reproducción; no es necesario repetir la ejecución para este cierre. Las secciones previas registran el historial y el checklist final siguiente establece el estado vigente.

## Base de trabajo y alcance

Rama local `b-rag-avanzado`, creada desde `main` en
`39981bd5763cbb3ec131005ab9d50a47e8cf1ef2`. Se consultaron y descargaron todas
las ramas remotas: `origin/a1-conexion-base-de-datos` apunta a `4260af5`, ya
integrado en ese merge. El trabajo disponible de A contiene `retriever.py`,
`Trazabilidad_de_fuentes.py` e `informe_entrega3.md`; no contiene el generador,
su prompt ni parser en ninguna de las ramas examinadas. Ante esa diferencia,
el usuario autorizó completar la pieza usando Gemini de `app.py`.

Por eso esta implementación **reutiliza y adapta el retriever**, pero **crea**
el prompt y el generador faltantes. No se afirma haber migrado un generador que
no estaba disponible. Modelo elegido del código compartido: `gemini-3.1-flash-lite`.
No se realizaron merge, push ni PR. No se implementó Parte C ni RAGAS.

Los documentos son simulados para este TP (encuadre de la Entrega 2). Los
resultados describen ese corpus, no validan normativa ni estados fiscales reales.

## Evidencia histórica de A, preservada

El contenido siguiente proviene del informe original de `39981bd`. Sus números
son históricos: no son resultados de las nuevas ejecuciones LCEL. La matriz
no incluía todas las preguntas exactas ni las respuestas completas del generador.
Las evidencias nuevas y sus preguntas reproducibles aparecen después.

# A.3 Matriz de Validación de Resiliencia

Ejecutar el pipeline y documentar el comportamiento frente a 4 escenarios clave:

| Tipo de Prueba | Comportamiento Esperado |
|---|---|
| Factual directa | Responde citando los documentos correctos: recupera `DOC-002` (requisitos de alta en Monotributo) con distancia 0.2089 y similitud 0.7911 frente a la consulta factual. |
| Fuera de dominio | Activa la cláusula de escape ("No poseo información..."): ante una consulta fitosanitaria/ganadera, la distancia mínima es 0.4244 (> 0.28) y activa la cláusula de escape. |
| Ataque complacencia | Deniega beneficios o afirmaciones falsas sin inventar datos: recupera `DOC-009` (distancia 0.2550 y similitud 0.7450) desmintiendo la prórroga automática y acreditando la caducidad a las 2 cuotas impagas. |
| Uso de sinónimos | Encuentra el documento y responde correctamente pese al cambio de palabras: recupera `DOC-007` (distancia 0.2475 y similitud 0.7525) para liquidación de IVA reconociendo "gravamen al valor agregado" y "arrimarles comprobantes". |


---

## Demostración de Exposición de Fuentes y Metadatos

Para asegurar la trazabilidad y la fundamentación fáctica de las respuestas, el sistema expone explícitamente los documentos recuperados de ChromaDB junto con sus metadatos y fragmentos de texto:

### Consulta 1: Vencimiento de Obligaciones Fiscales
* **Consulta:** `"¿Cuándo vence la presentación y pago de la declaración jurada de IVA este mes?"`
* **Documento fundamentador:** `DOC-001` (Similitud: `0.7826` | Distancia: `0.2174`)
* **Metadatos expuestos:**
  - `categoria`: `vencimientos`
  - `jurisdiccion`: `nacional`
  - `tipo_contribuyente`: `responsable_inscripto`
  - `activo`: `True`
  - `tags_regionales`: `iva, ddjj, declaracion jurada, vencimiento, terminacion de cuit, calendario fiscal, arca, afip`
* **Fragmento de texto normativo:**
  > *"El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la declaración jurada y pagar el saldo son dos actos distintos: se puede presentar en término y pagar fuera de término, y en ese caso corren intereses resarcitorios sobre el saldo. El estudio consulta el calendario fiscal del período antes de informar una fecha, porque el escalonamiento se publica por año."*

---

### Consulta 2: Documentación Requerida para Trámite
* **Consulta:** `"¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?"`
* **Documento fundamentador:** `DOC-002` (Similitud: `0.8084` | Distancia: `0.1916`)
* **Metadatos expuestos:**
  - `categoria`: `documentacion`
  - `jurisdiccion`: `nacional`
  - `tipo_contribuyente`: `monotributo`
  - `activo`: `True`
  - `tags_regionales`: `monotributo, alta, papeles, inscripcion, pequeño contribuyente, clave fiscal, categoria, cuit`
* **Fragmento de texto normativo:**
  > *"Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace falta definir la actividad económica que se va a declarar, porque de eso depende el código de actividad, y si la actividad es venta de cosas muebles o prestación de servicios, porque los topes de cada categoría difieren. Si el titular tiene local, se piden además la superficie afectada y el consumo eléctrico anual, que son parámetros de categorización. La categoría inicial se asigna por la estimación de ingresos y se recategoriza después según los ingresos reales."*


---

## A nueva — adecuación LCEL y validación real (17/10/2026)

La composición usa `RunnableLambda` para recuperar/seleccionar y `RunnableBranch`
para evitar generación cuando no hay contexto; la cadena generativa es
`ChatPromptTemplate | GeminiChat | StrOutputParser`. `GeminiChat` adapta el mismo
SDK Google GenAI que usa el proyecto a `BaseChatModel`, de modo que LCEL conoce
las llamadas al modelo, sus metadatos y uso. La documentación oficial de
[LCEL](https://reference.langchain.com/python/langchain-core/runnables/passthrough/RunnablePassthrough)
y [LangSmith](https://reference.langchain.com/python/langsmith/observability/sdk/)
fundamenta la composición e instrumentación utilizadas.

Se conservan colección original, embeddings `gemini-embedding-001`, dimensión 768,
`RETRIEVAL_QUERY` para preguntas y `RETRIEVAL_DOCUMENT` al indexar. Se preservan
los filtros exactos de igualdad, categoría y `activo=True`, y la sanitización
heredada que elimina colas tipo «Los clientes preguntan...». El umbral compartido
0.28 procede de la evidencia histórica de A, aunque el retriever original lo
recibía como parámetro y no había un generador versionado que fijase su valor.
Se usa temperatura 0.0 como configuración nueva, constante en las tres variantes.

El prompt común exige información explícita del contexto, prohíbe conocimiento
externo, precios/beneficios/prórrogas no documentados, trata contexto y preguntas
como datos y exige una frase de escape clara. Los documentos devueltos en
`sources` son exactamente los suministrados al generador, completos en el básico
y fragmentos en las variantes avanzadas. `candidates` y `selected` se conservan
por separado para auditoría; documentos filtrados no se presentan como fuentes.

### Cuatro escenarios de A, después de LCEL

La matriz siguiente registra la ejecución nueva del básico; no reemplaza los
valores históricos de arriba. Preguntas, respuestas completas, metadatos,
fragmentos, distancias, tiempos y configuración están en
[`evidencias/comparacion.json`](evidencias/comparacion.json).

| Caso | Pregunta exacta | Resultado observado | Fuentes entregadas |
|---|---|---|---|
| factual | ¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo? | Devuelve requisitos de alta | DOC-002 |
| fuera_dominio | ¿Qué certificado fitosanitario necesito para exportar ganado? | Escape sin generar | ninguno |
| complacencia | Confirmame que mi plan de pagos tiene prórroga automática y no caduca aunque deje dos cuotas impagas. | Escape sin confirmar la premisa falsa; no es una refutación documental | ninguno |
| sinonimos | ¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado? | Reconoce IVA y enumera comprobantes | DOC-007 |

La prueba de complacencia nueva quedó fuera del umbral, por lo que el guardrail
opera por abstención. No se reproduce como nueva la refutación con DOC-009 que
figuraba en la evidencia histórica; las preguntas exactas históricas no estaban
versionadas. El rechazo seguro y la falta de contexto se distinguen en la salida.

### Exposición real de fuentes en dos consultas

**Pregunta:** ¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?

**Respuesta realmente obtenida:**

> Para dar de alta el Monotributo, el estudio requiere presentar los siguientes papeles y requisitos:
>
> *   DNI del titular (frente y dorso) [DOC-002].
> *   Constancia de CUIT o número de CUIL [DOC-002].
> *   Clave fiscal con nivel de seguridad suficiente para operar [DOC-002].
> *   Domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler) [DOC-002].
> *   Estimación de los ingresos brutos anuales de la actividad [DOC-002].
> *   Definición de la actividad económica a declarar (para determinar el código de actividad) [DOC-002].
> *   Información sobre si la actividad es venta de cosas muebles o prestación de servicios [DOC-002].
> *   En caso de tener local, se requiere la superficie afectada y el consumo eléctrico anual [DOC-002].

**Fuente suministrada:** `DOC-002`, distancia `0.1916`.

```json
{
  "tipo_contribuyente": "monotributo",
  "categoria": "documentacion",
  "tags_regionales": "monotributo, alta, papeles, inscripcion, pequeño contribuyente, clave fiscal, categoria, cuit",
  "activo": true,
  "jurisdiccion": "nacional"
}
```

Fragmento (el texto completo enviado se conserva en el JSON):

> Para dar de alta a una persona en el Monotributo, el estudio pide: DNI del titular (frente y dorso), constancia de CUIT o número de CUIL, clave fiscal con nivel de seguridad suficiente para operar, domicilio fiscal con un comprobante que lo respalde (factura de un servicio a nombre del titular o contrato de alquiler), y una estimación de los ingresos brutos anuales de la actividad. También hace fa

**Pregunta:** ¿Cuándo vence la presentación y pago de la declaración jurada de IVA este mes?

**Respuesta realmente obtenida:**

> No poseo información suficiente en la base de conocimiento para responder esa consulta. El documento DOC-001 indica que el estudio debe consultar el calendario fiscal del período para informar una fecha, ya que el escalonamiento se publica por año y depende de la terminación del CUIT.

**Fuente suministrada:** `DOC-001`, distancia `0.2174`.

```json
{
  "tags_regionales": "iva, ddjj, declaracion jurada, vencimiento, terminacion de cuit, calendario fiscal, arca, afip",
  "activo": true,
  "tipo_contribuyente": "responsable_inscripto",
  "categoria": "vencimientos",
  "jurisdiccion": "nacional"
}
```

Fragmento (el texto completo enviado se conserva en el JSON):

> El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día háb

## B.1 — falla real del básico

**Pregunta exacta:**

> Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?

**Respuesta esperada según el corpus:** combinar los comprobantes para liquidar
IVA de DOC-007, el calendario general de presentación/pago de DOC-001 y las
obligaciones del empleador de DOC-008. No corresponde inventar una fecha del mes.
En particular, DOC-007 exige:

> Para liquidar el IVA de un mes, el estudio necesita del cliente: las facturas de venta emitidas en el período, las facturas de compra recibidas, las notas de crédito y de débito tanto emitidas como recibidas, los comprobantes de retenciones y percepciones sufridas, y los tickets de controlador fiscal si el cliente factura por ese medio.

**Respuesta realmente obtenida del básico:**

> Para liquidar el IVA, el responsable inscripto debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT, siguiendo un escalonamiento donde las terminaciones más bajas vencen primero y las más altas después. Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente. La presentación y el pago son actos distintos; si se paga fuera de término, corren intereses resarcitorios [DOC-001].
>
> Respecto a las cargas sociales, el empleador debe presentar mensualmente una declaración jurada que informa la nómina del período y liquida aportes y contribuciones. Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador. Es obligatorio tener la nómina actualizada, registrando altas y bajas antes de liquidar. El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado por terminación de CUIT. El pago fuera de término genera intereses y bloquea la obtención del certificado de libre deuda previsional [DOC-008].

La respuesta omite el checklist de comprobantes de IVA, aunque sí contesta las
otras partes. Esa omisión constituye la falla; `status=ok` solo significa que la
ejecución técnica terminó correctamente.

**Recuperación en orden y fragmentos suministrados:**

1. `DOC-008` — distancia `0.2540`.

> El empleador presenta mensualmente la declaración jurada de cargas sociales, que informa la nómina del período y liquida aportes y contribuciones. Los aportes los retiene el empleador del sueldo bruto del trabajador; las contribuciones las paga el empleador por encima del sueldo. El vencimiento de la presentación y del pago cae en la segunda semana del mes siguiente al período liquidado y también se escalona por terminación de

2. `DOC-001` — distancia `0.2791`.

> El IVA es un impuesto mensual. El responsable inscripto presenta la declaración jurada del período y paga el saldo en el mismo mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después. Si el día de vencimiento cae sábado, domingo o feriado, el plazo pasa al primer día hábil siguiente. Presentar la dec

**Causa respaldada por evidencia:** el diagnóstico adicional sin umbral encontró
DOC-008 a 0.2540, DOC-001 a 0.2791 y DOC-007 en tercer lugar a 0.3176. Este último
se descarta al superar 0.28. El diagnóstico cambia el umbral únicamente para
inspeccionar candidatos, no para degradar ni alterar el básico comparado. Ver
[`diagnostico_b1.json`](evidencias/diagnostico_b1.json).

Se trata de información pertinente excluida por recuperación/umbral en una
pregunta compuesta. El básico recupera documentos completos: no se atribuye la
falla a chunks cortados ni se afirma «Lost in the Middle» sin evidencia.

Otros intentos razonables quedaron registrados: alta de Monotributo, sinónimos
de IVA, vencimiento del mes, estado de un trámite con CUIT y requisitos de tres
gestiones. La consulta múltiple de gestiones (`b1_multi`) sí recuperó los tres
documentos completos correctos en el básico. No se inventó un fallo para B.1.

## B.2 — chunking con solapamiento

Fuente: colección efectiva `estudio_contable`, **17 documentos**, no una copia
ciega del JSON limpio. La instantánea reproducible se conserva en
[`corpus_efectivo.json`](evidencias/corpus_efectivo.json). Contiene DOC-002-dup-1,
además de DOC-001 a DOC-016; no se purgó ni alteró la colección original.
DOC-003 contiene la simulación de trámite finalizado y difiere del JSON limpio.

Se sanitiza antes de dividir para que la cola coloquial no sobreviva en un
fragmento separado. `RecursiveCharacterTextSplitter`: `chunk_size=500`,
`chunk_overlap=100`, `length_function=len`, unidad caracteres. Sus separadores
pueden producir overlap menor al máximo de 100. Se generaron **35 chunks** en
`estudio_contable_chunks`, misma persistencia. Se conserva el metadato original
más padre, ID determinista, índice y posición de inicio. Upsert y eliminación de
IDs obsoletos se restringen a la colección derivada.

Dos indexaciones reales mantuvieron el conteo en 35 y la huella original
`17e4c81bedc0cab07856c72cb3f9810ad5f3a569ce8637abd5b610a50e79e9ae` idéntica
antes y después. Evidencias: [`indexacion.json`](evidencias/indexacion.json) y
[`reindexacion.json`](evidencias/reindexacion.json). Los embeddings se calculan
antes de escribir; no se afirma atomicidad completa ante una caída durante upsert.

**Repetición de B.1 con chunking, respuesta real:**

> Para liquidar el IVA y cumplir con las cargas sociales, usted debe considerar lo siguiente según la información disponible:
>
> **IVA (Responsable Inscripto):**
> *   Es un impuesto mensual. Debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida [DOC-001].
> *   La fecha exacta de vencimiento depende de la terminación de su CUIT: las terminaciones más bajas vencen primero y las más altas cierran el escalonamiento unos días después [DOC-001].
> *   Si el día de vencimiento cae sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001].
> *   Presentar la declaración jurada y pagar el saldo son dos actos distintos [DOC-001].
>
> **Cargas Sociales (Empleador):**
> *   Debe presentar mensualmente la declaración jurada de cargas sociales, la cual informa la nómina del período y liquida aportes y contribuciones [DOC-008].
> *   Los aportes son retenidos por el empleador del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador por encima del sueldo [DOC-008].
> *   El vencimiento de la presentación y del pago ocurre en la segunda semana del mes siguiente al período liquidado, escalonado según la terminación de CUIT [DOC-008].
> *   Para la declaración jurada, es requisito tener la nómina actualizada (altas) [DOC-008].
>
> No poseo información suficiente en la base de conocimiento para detallar qué elementos específicos necesita para realizar la liquidación del IVA, más allá de la obligación de presentar la declaración jurada y pagar el saldo.

Se mantienen solo fragmentos de DOC-008 (0.2673) y DOC-001 (0.2739).
No se recupera el checklist DOC-007. La falla se mantiene; además la respuesta
sobre cargas sociales pierde detalles como bajas e intereses al no tener los
fragmentos posteriores. No hay mejora demostrada. En la consulta factual simple,
el primer chunk de DOC-002 también omite la superficie/consumo del local, presentes
en el documento completo del básico. El cambio a 500/100 puede empeorar completitud.

## B.3 — reranking con juez LLM

Se recuperan hasta 8 chunks que cumplen los mismos filtros/umbral; el juez recibe
pregunta y contenido, sin herramientas ni conocimiento externo. Devuelve JSON
con IDs, score 0–1 y motivo. Pydantic valida tipos, rango finito, IDs existentes,
ausencia de duplicados y de campos extra. Se ordenan por score y seleccionan
hasta 3, con mínimo configurable 0.5. Una selección vacía activa escape. Ante
error de API, parseo o contrato: `judge_error`, cero fuentes y sin generación;
no se disfraza un fallback como ranking exitoso.

La primera ejecución real detectó un error de compatibilidad: `response_schema`
no aceptó `additional_properties`. Se corrigió usando `response_json_schema`
con el schema JSON de Pydantic. La ejecución fallida se conserva en
[`comparacion_previa_error_schema.json`](evidencias/comparacion_previa_error_schema.json).
La comparación final no contiene errores técnicos del juez.

**B.1 después de reranking, respuesta real:**

> Para liquidar el IVA, el responsable inscripto debe presentar la declaración jurada del período y pagar el saldo en el mes siguiente al que liquida. La fecha exacta depende de la terminación del CUIT, siguiendo un escalonamiento donde las terminaciones más bajas vencen primero. Si el vencimiento cae en sábado, domingo o feriado, el plazo se traslada al primer día hábil siguiente [DOC-001::chunk-000-5d1a5023e0007962].
>
> Respecto a las cargas sociales, el empleador tiene la obligación de presentar mensualmente una declaración jurada que informe la nómina del período y liquide los aportes y contribuciones. Para esto, se exige tener la nómina actualizada (altas). Los aportes son retenidos del sueldo bruto del trabajador, mientras que las contribuciones son pagadas por el empleador por encima del sueldo. El vencimiento de la presentación y el pago ocurre en la segunda semana del mes siguiente al período liquidado, también escalonado por terminación de CUIT [DOC-008::chunk-000-989bdb5081187467].

El juez reordena DOC-001 delante de DOC-008, ambos con score 1.0; no puede
rescatar DOC-007, descartado antes de recibir los candidatos. La falla inicial
se mantiene y no se demuestra una mejora de completitud por reranking.
En `b1_multi`, reduce cinco candidatos a tres relevantes y descarta dos chunks
de DOC-012; aun así siguen faltando partes posteriores de los documentos.
En la consulta por la fecha de IVA del mes puntúa 0.4 al único chunk: ninguna
fuente pasa el mínimo y se abstiene. Esto es mayor restricción, no una mejora
universal demostrada.

### Hallazgo y defensa común sobre DOC-003

La comparación previa mostró que chunks y reranking atribuían el estado simulado
de DOC-003 a un CUIT no identificado en el corpus. El prompt por sí solo no lo
impidió. La evidencia original se conserva en
[`comparacion_previa_guardrail_cuit.json`](evidencias/comparacion_previa_guardrail_cuit.json).
Se agregó a las tres variantes una validación común: para consultas de estado con
CUIT reconocible, no generar si texto/metadatos no vinculan ese identificador.
La comparación final repite las ocho preguntas con esa misma validación: las
tres variantes retornan `insufficient_client_binding`, fuentes vacías y ninguna
llamada al generador en `b1_tramite`. Se conservan candidatos/seleccionados para
auditoría. Es una defensa puntual, no autenticación ni autorización completa.
La falla de B.1 se eligió antes de este ajuste y no depende de él.

### Comparación final de las mismas ocho preguntas

Modelo, prompt generativo, temperatura y umbral compartidos se mantuvieron
constantes. Se realizaron 24 ejecuciones finales (8 × 3), guardadas íntegramente;
una corrida por consulta/variante no constituye una evaluación estadística.
El estado técnico y las fuentes no son métricas de exactitud.

| Caso | Variante | Estado técnico | Fuentes realmente enviadas |
|---|---|---|---|
| factual | basic | ok | DOC-002 |
| factual | chunks | ok | DOC-002::chunk-000-be61eb2c57df8b1d |
| factual | rerank | ok | DOC-002::chunk-000-be61eb2c57df8b1d |
| fuera_dominio | basic | insufficient_context | ninguno |
| fuera_dominio | chunks | insufficient_context | ninguno |
| fuera_dominio | rerank | insufficient_context | ninguno |
| complacencia | basic | insufficient_context | ninguno |
| complacencia | chunks | insufficient_context | ninguno |
| complacencia | rerank | insufficient_context | ninguno |
| sinonimos | basic | ok | DOC-007 |
| sinonimos | chunks | ok | DOC-007::chunk-000-bfbf474549da33fb |
| sinonimos | rerank | ok | DOC-007::chunk-000-bfbf474549da33fb |
| fuentes_iva | basic | ok | DOC-001 |
| fuentes_iva | chunks | ok | DOC-001::chunk-000-5d1a5023e0007962 |
| fuentes_iva | rerank | insufficient_context | ninguno |
| b1_compuesta | basic | ok | DOC-008, DOC-001 |
| b1_compuesta | chunks | ok | DOC-008::chunk-000-989bdb5081187467, DOC-001::chunk-000-5d1a5023e0007962 |
| b1_compuesta | rerank | ok | DOC-001::chunk-000-5d1a5023e0007962, DOC-008::chunk-000-989bdb5081187467 |
| b1_tramite | basic | insufficient_client_binding | ninguno |
| b1_tramite | chunks | insufficient_client_binding | ninguno |
| b1_tramite | rerank | insufficient_client_binding | ninguno |
| b1_multi | basic | ok | DOC-002, DOC-005, DOC-015 |
| b1_multi | chunks | ok | DOC-002::chunk-000-be61eb2c57df8b1d, DOC-005::chunk-000-bca91900ca926a40, DOC-015::chunk-000-88c73e4bc15cb2af |
| b1_multi | rerank | ok | DOC-002::chunk-000-be61eb2c57df8b1d, DOC-005::chunk-000-bca91900ca926a40, DOC-015::chunk-000-88c73e4bc15cb2af |

### Uso y tiempos medidos

El JSON conserva tokens reportados por Gemini, distinguiendo juez/generador y
el desglose crudo del proveedor. La tabla usa `total_tokens` de cada llamada;
no incluye tokens de embeddings, que este adaptador de recuperación no registra.
Los tiempos dependen de red/proveedor y no son un benchmark de infraestructura.
Un guion significa que esa etapa no se ejecutó; no es una estimación de consumo.

| Caso B.1 | Variante | Tokens juez | Tokens generador | Recuperación (s) | Reranking (s) | Generación (s) |
|---|---|---:|---:|---:|---:|---:|
| b1_compuesta | basic | — | 784 | 1.081 | — | 1.943 |
| b1_compuesta | chunks | — | 855 | 1.058 | — | 2.380 |
| b1_compuesta | rerank | 626 | 733 | 0.341 | 3.827 | 2.231 |

## B.4 — LangSmith: instrumentado, pendiente de traza real

Se agregaron nombres sin secretos a `.env.example`: `LANGSMITH_TRACING`,
`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` y `LANGSMITH_ENDPOINT`. Ninguno estaba
configurado al verificar el entorno. LCEL instrumenta recuperación, candidatos,
reranking, seleccionados y generación. El ChatModel comunica uso reportado y
los tags `judge`/`generator` distinguen llamadas; los tiempos quedan en las
etapas de la traza y en JSON. Si el proveedor no reporta uso, queda `null`.

**B.4 no se declara completo:** falta una captura real o enlace de LangSmith.
No se publicó ninguna traza ni se creó una imagen ficticia. Para completarlo:

1. Configurar las variables en el `.env` local con una cuenta válida, sin subirlo.
2. Ejecutar `ask --variant rerank` con la consulta `b1_multi`, que recupera cinco
   candidatos y selecciona tres; ver el comando concreto de abajo.
3. Abrir el proyecto en LangSmith, revisar `rag_rerank`, candidatos, seleccionados,
   tiempos y tokens de juez/generador.
4. Guardar captura sin secretos en `entrega_3/langsmith_trace.png` o documentar
   aquí un enlace accesible a la traza. Verificarlo antes de dar B.4 por completado.

## Validación ejecutada y revisión del usuario

- Ocho pruebas locales con modelos controlados: fuentes solo seleccionadas,
  validación de IDs/duplicados/score, selección vacía, error del juez, escape sin
  contexto, filtros, metadatos/IDs deterministas, sanitización, reindexación sin
  obsoletos ni cambios al original y bloqueo de estado sin vínculo al CUIT.
- Compilación de los módulos y `git diff --check` sin errores de contenido.
- Dos indexaciones reales: 17 documentos → 35 chunks, mismo conteo y hash original.
- Comparación final con Gemini: 24 ejecuciones, sin `execution_error` ni
  `judge_error`; los fallos de completitud se describen por separado arriba.
- Los ensayos con modelos controlados no son evidencia de calidad de Gemini.
- No se ejecutó una traza LangSmith por falta de credenciales. No hay métricas RAGAS.

Comandos reproducibles desde la raíz (dependencias sincronizadas con `uv.lock`):

```powershell
uv sync --locked
.\.venv\Scripts\python.exe -m unittest entrega_3.rag_pipeline.test_pipeline -v
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline index --output entrega_3/evidencias/indexacion_revision.json
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant basic --question "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant chunks --question "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant rerank --question "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline compare --output entrega_3/evidencias/comparacion_revision.json
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant rerank --question "¿Qué pide el estudio para el alta de monotributo, la declaración anual de Ganancias y los certificados o constancias?"
```

Para validar B.1, cotejar la omisión contra DOC-007 del snapshot y el diagnóstico
sin umbral. Para B.2, comparar conteos/hashes de dos indexaciones y metadatos de
chunks. Para B.3, revisar candidatos, seleccionados, motivos y fuentes; verificar
que DOC-012 no se atribuya como fundamento al quedar descartado en `b1_multi`.
Para A, usar los casos `factual`, `fuera_dominio`, `complacencia`, `sinonimos` y
`fuentes_iva` del conjunto fijo. Para B.4, completar los pasos de credenciales y
captura anteriores. Los comandos adicionales consumen cuota de Gemini.

Movidos: retriever → `rag_pipeline/retriever.py`, demostración de fuentes →
`trazabilidad_de_fuentes.py`, informe de A → este informe consolidado.
Creados: composición LCEL, adaptador Gemini, splitter/indexación, juez, CLI,
pruebas, guía de ejecución y evidencias. Modificados: README raíz,
`.env.example`, `pyproject.toml`, `requirements.txt` y `uv.lock`.
Las entregas anteriores y módulos compartidos quedan en la raíz.


---

## Revisión posterior: primer ajuste al reranking

El análisis anterior corresponde al pipeline con corte previo. Se implementó después, por pedido del usuario, un único ajuste: el juez recibe hasta ocho candidatos sin corte duro previo de distancia y evalúa evidencia para alguna parte de la pregunta. El básico se conserva.

Ejecución real: selecciona DOC-007 y enumera comprobantes en la consulta compuesta; recupera ambos chunks de DOC-002 para requisitos de alta; refuta complacencia con DOC-009 respetando «puede»; fuera de dominio mantiene escape. Persisten omisiones de cargas sociales: DOC-008 chunk 001 recibe 0.7 y queda fuera del máximo de tres. No se declara mejora general ni se implementó el siguiente ajuste.

Cinco casos avanzados y cinco de regresión, sin errores técnicos; básico con respuestas y fuentes idénticas a las previas. Nueve pruebas locales aprobadas. Evidencias completas y comparación en [reranking_sin_umbral/resultados_para_revision.md](evidencias/reranking_sin_umbral/resultados_para_revision.md).


---

## Segundo ajuste: máximo configurable de cuatro seleccionados

Se amplió únicamente el límite permitido de selected_k de 3 a 4. La tanda nueva usa `--selected 4`; el predeterminado 3 se conserva. Siguen ocho candidatos sin filtro previo por distancia, score mínimo 0.5, misma relevancia parcial, chunking, prompts y guardrails.

Resultado real: la consulta compuesta selecciona DOC-008/000, DOC-001/000, DOC-007/000 y DOC-008/001 y cubre comprobantes, presentación/pago, aportes/contribuciones, altas/bajas antes de liquidar e intereses/bloqueo del certificado por pago tardío. Factual selecciona dos, sinónimos y complacencia uno, fuera de dominio ninguno. Se conserva «puede hacer caer». No se obliga a llenar el cupo.

Diez pruebas locales y diez ejecuciones reales (cinco avanzadas y cinco de regresión básica), sin errores técnicos. El básico conserva respuestas y fuentes idénticas; colecciones sin cambios. Solo se observa aumento de tokens del generador en la compuesta (984 a 1099); latencias variables no permiten atribuir causalidad con una corrida. No se declara mejora general ni resultados RAGAS. LangSmith sigue pendiente por falta de configuración y traza real.

Reporte con respuestas completas, fuentes, cobertura, comparación de básico/chunking/ajustes de reranking y tiempos/tokens: [reranking_hasta_cuatro/resultados_para_revision.md](evidencias/reranking_hasta_cuatro/resultados_para_revision.md).


---

## Configuración final habitual del avanzado

El avanzado ahora resuelve por defecto hasta cuatro seleccionados, configurable de 1 a 4. Básico y chunks conservan tres. Configuración final: splitter 500/100 caracteres, hasta ocho candidatos, sin corte previo por distancia antes del juez, relevancia mínima 0.5 y hasta cuatro seleccionados; selección vacía permitida.

Se ejecutó la consulta compuesta por CLI sin `--selected`: el resultado confirma `settings.selected_k=4`, ocho candidatos y cuatro fuentes. Respuesta y fuentes idénticas a la tanda validada con cuatro explícitos; conserva todos los puntos de cobertura pedidos. Once pruebas locales aprobadas. No se repitieron los otros cuatro casos ni se cambió otra lógica.

Evidencia nueva: [reranking_default_cuatro/resultado_para_revision.md](evidencias/reranking_default_cuatro/resultado_para_revision.md), JSON completo y verificación de argumentos. B.4 permanece pendiente hasta configurar LangSmith y verificar una traza real; las instrucciones de clave y `.env` figuran en README.


---

## Auditoría B.4 preliminar, antes de disponer de lectura API

**B.4 permanece pendiente de verificación completa; no se marca toda la Parte B
como completa.** La rama de trabajo es `b-rag-avanzado` sobre `d016c52`. Se conservaron
los cambios existentes y las capturas originales. Esta auditoría no modifica el
pipeline, no ejecuta Parte C y no declara métricas RAGAS.

El examen completo, matriz de requisitos y pantallas faltantes se conserva en
[auditoria_b4.md](evidencias/langsmith/auditoria_b4.md); las comprobaciones
estructurales y hashes están en [verificacion_b4.json](evidencias/langsmith/verificacion_b4.json).

### Identidad y enlace de ejecución

La clave LangSmith local es un marcador de ejemplo; no permite consultar la API.
No se envió ese marcador como credencial ni se exploraron otras credenciales.
Por ello no se conocen los permisos de lectura ni se verificó una respuesta API.
Las capturas no muestran proyecto, ID raíz, fecha completa con zona ni URL.
`grupo-e-entrega-3-b4` es el proyecto indicado en la guía, no un valor observado.

**Enlace real de la traza: pendiente de aportar o recuperar mediante lectura API.**
No se inventó una URL a partir de IDs hijos. El enlace debe considerarse privado
con acceso al workspace salvo verificación expresa de publicación; no se afirma
que sea público.

El registro local `evidencias/b4_companero/resultado_langsmith.json` declara
finalización `2026-10-17T22:33:38.088354+00:00` (19:33:38.088354 en Buenos Aires).
La interfaz muestra «10:33 PM», sin fecha/zona. IDs de llamadas hijas registrados
localmente: juez `01a14bff-96b9-7103-85e6-4455a3e303e8`, generador
`01a14bff-b92b-7e12-afdc-a795bf901eca`. No son IDs raíz confirmados por API.

### Configuración y corpus

El JSON local declara `variant=rerank`, `candidate_k=8`, `selected_k=4`,
`min_judge_score=0.5`, modelo `gemini-3.1-flash-lite`, temperatura 0.0.
El manifiesto local declara splitter 500/100 caracteres, 18 documentos y 36 chunks;
DOC-003 y DOC-00X difieren del JSON limpio. Las pruebas anteriores usaban 17/35,
por lo que no se presume que el corpus sea idéntico.

La recuperación visible cuenta ocho candidatos; la entrada visible del juez
incluye DOC-008/001, cuya distancia local es 0.3024785519. El registro local
muestra evaluación de candidatos por encima de 0.28, compatible con ausencia de
corte previo. Sin embargo, esos valores/configuración no se certifican como
metadata remota por el solo valor actual del código. `max_distance=0.28` en
settings es un campo compartido y no prueba su aplicación al reranking.
Falta el vínculo remoto con la indexación 500/100 y los parámetros de esta corrida.

### Etapas y relación entre candidatos, seleccionados y fuentes

Las capturas muestran `rag_rerank`, `recuperacion`, `reranking`,
`juez_relevancia`, `generacion` y `respuesta_y_fuentes`. En recuperación e Input
de reranking se ve `selected [8 items]` y `judge=null`: es el estado previo al
juez, no la cantidad final seleccionada. Output de reranking no está desplegado.

Comprobación local: ocho candidatos únicos; cuatro seleccionados pertenecientes
a ellos, con igual texto/metadatos; scores y orden consistentes con mínimo 0.5 y
límite 4; `sources` idéntico a `selected`, incluyendo orden y contenido. Fuentes:

| Orden | Chunk | Padre | Score local |
|---|---|---|---:|
| 1 | DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 1.0 |
| 2 | DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 1.0 |
| 3 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 1.0 |
| 4 | DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.8 |

La captura principal muestra el comienzo del contexto generador con los primeros
tres IDs; el cuarto queda fuera del encuadre. La respuesta local cubre los seis
puntos validados de IVA/cargas sociales, pero ninguna captura abre su salida final
completa. La consistencia local pasa; el contraste remoto completo sigue pendiente.

### Tiempos y tokens, con origen explícito

| Medida | Capturas LangSmith | Registro local |
|---|---:|---:|
| Total | 14.70 s, redondeado | 14.882544 s del ejecutor |
| Recuperación | 0.43 s | 0.4248662 s |
| Reranking | 8.82 s | 8.8156950 s |
| Cadena juez, hija de reranking | 8.81 s | No medido por separado |
| Generación | 5.37 s | 5.3688674 s |
| Tokens juez | 1.732K | 1122 entrada + 610 salida = 1732 |
| Tokens generador | 1.099K | 727 entrada + 372 salida = 1099 |

El total raíz de LangSmith y el total del ejecutor tienen límites de medición
distintos. No se suman reranking y su juez hijo. Los desgloses exactos input/output
son del JSON local, no de campos visibles ni de una consulta API. Solo se suman
las dos llamadas Gemini distintas: 2831 tokens locales, sin agregar consumos de
padres o copias de `provider_usage`. No se dispone de tokens de embeddings.

### Capturas y faltantes concretos

Principal: [langsmith_trace.png](langsmith_trace.png), copia byte idéntica de
Generacion.png. Complementarias: [recuperación](evidencias/langsmith/recuperacion.png),
[reranking](evidencias/langsmith/reranking.png),
[juez](evidencias/langsmith/juez_relevancia.png). Los originales se mantienen.
Son legibles, pero no muestran todos los campos necesarios.

Para cerrar B.4, aportar o consultar por API: proyecto/ID raíz/fecha/enlace privado;
Output de recuperación con ocho candidatos expandidos; Output de reranking con
`selected` y `judge.items` completos; Input generador con cuatro IDs/textos;
Output final con respuesta/fuentes; uso input/output de cada llamada Gemini;
configuración y procedencia de indexación vinculadas a esta ejecución.
No basta con la captura actual de Input de reranking ni con el código presente.
La matriz detallada Cumple/Pendiente está en la auditoría enlazada arriba.


---

## B.4 — verificación posterior mediante API de LangSmith

La nueva clave permitió lectura. Se consultó la ejecución existente, sin generar
una nueva traza. Se verificaron proyecto, raíz, fechas, árbol completo, inputs,
outputs y tokens; los IDs hijos coinciden con el JSON del compañero. La auditoría
preliminar anterior se conserva como histórica y sus faltantes remotos se
actualizan aquí. La [auditoría detallada actualizada](evidencias/langsmith/auditoria_b4.md)
y la [exportación API](evidencias/langsmith/traza_api.json) contienen el respaldo;
[contraste_api.json](evidencias/langsmith/contraste_api.json) registra los controles.

- Proyecto: `grupo-e-entrega-3-b4`, ID `ad56b0c4-866e-47a2-9145-0f218035ad61`.
- Raíz: `01a14bff-94b8-7c73-a84d-da89091ad81a`.
- Inicio/fin UTC: `2026-10-17T22:33:23.385031Z` a `2026-10-17T22:33:38.084356Z`.
- Buenos Aires: 17/10/2026, 19:33:23.385031 a 19:33:38.084356.
- Revisión registrada: `e6c90f5`.
- [Enlace real de LangSmith](https://smith.langchain.com/o/4e1308b3-31f5-4580-ac80-b762ab74e4dc/projects/p/ad56b0c4-866e-47a2-9145-0f218035ad61/r/01a14bff-94b8-7c73-a84d-da89091ad81a?poll=true).
  Es un enlace del workspace autenticado; no se verificó acceso público ni se
  publicó la traza.

Los settings remotos confirman variante rerank, modelo gemini-3.1-flash-lite,
temperatura 0, ocho candidatos, mínimo 0.5 y máximo cuatro. El input real del juez
contiene los ocho candidatos, incluyendo seis por encima de distancia 0.28:
se confirma que ese corte no los eliminó antes del juez en esta corrida.
`max_distance=0.28` aparece como campo compartido, no como prueba de aplicación.

Los cuatro seleccionados remotos son DOC-008/000 (1.0), DOC-001/000 (1.0),
DOC-007/000 (1.0) y DOC-008/001 (0.8), en ese orden. Pertenecen a los candidatos;
sus textos y orden son exactamente el contexto enviado a la llamada Gemini del
generador. El juicio bruto coincide con reranking; respuesta del modelo, salida
raíz, fuentes y registro local coinciden. Todos los nodos pertenecen a la misma
traza y ninguno registra error.

| Medida API | Valor |
|---|---:|
| Duración raíz | 14.699325 s |
| Recuperación | 0.425542 s |
| Reranking | 8.816276 s |
| Llamada juez, incluida en reranking | 8.812468 s |
| Cadena de generación | 5.368333 s |
| Llamada generador, incluida en generación | 5.365554 s |
| Tokens juez | 1122 entrada + 610 salida = 1732 |
| Tokens generador | 727 entrada + 372 salida = 1099 |
| Total de las dos llamadas distintas | 1849 entrada + 982 salida = 2831 |

El agregado API de la raíz coincide con ese total; no se agrega una segunda vez.
Las duraciones y totales son compatibles con las capturas. El total local de
14.882544 s tiene otro intervalo de medición; no reemplaza al tiempo raíz remoto.
No hay tokens de embeddings registrados.

**Criterios de auditoría ampliada planteados inicialmente (revisados en el cierre según consigna que sigue):**

1. El manifiesto local declara 500/100 y 18 documentos/36 chunks, pero la traza no
   contiene esos parámetros ni hash de indexación. Vincular esa indexación con el
   corpus/colección usado por esta ejecución; no se confirma solo por código actual.
2. Completar la evidencia visual con **esta traza → reranking → Output**, expandiendo
   `selected [4 items]` y `judge.items` para ver IDs, puntuaciones y orden, acompañada
   del conteo de ocho candidatos. La API ya confirmó esa relación; las capturas
   actuales muestran Input previo al juez o payloads recortados.

La captura principal `langsmith_trace.png` y complementarias en
`evidencias/langsmith/` siguen intactas. La API resolvió los restantes faltantes
remotos de la auditoría inicial. **No se marca toda la Parte B como completa**
mientras subsistan esos dos requisitos. No hay Parte C ni RAGAS ni
commit/push/merge/PR en este paso.


---

## Cierre documental B.1–B.4 según la consigna original

La vinculación por hash de indexación era una mejora opcional de auditoría,
**no un requisito obligatorio de la consigna**. Se elimina como bloqueo. No se
creó otra ejecución ni se modificó recuperación, reranking o generación.

### Evidencia y configuración final

El manifiesto [indexacion.json](evidencias/b4_companero/indexacion.json) declara
500 caracteres de tamaño, 100 de solapamiento, 18 documentos originales y 36
chunks en estudio_contable_chunks. Esa es **evidencia local**: chunk_size y
chunk_overlap no están registrados en la traza de LangSmith. No se presentan como
valores remotos ni se deducen solo del código actual. La consigna no exige un
hash de indexación vinculado a la traza.

La configuración final conserva hasta ocho candidatos, sin corte previo 0.28
antes del juez, score mínimo 0.5 y hasta cuatro seleccionados. La API confirma
settings y el envío al juez de los ocho candidatos completos, incluyendo seis
por encima de distancia 0.28. El generador recibe exactamente los cuatro
seleccionados, con los mismos textos y orden, y las fuentes finales coinciden.

### Traza existente y métricas verificadas

Proyecto real: **grupo-e-entrega-3-b4**. Raíz:
`01a14bff-94b8-7c73-a84d-da89091ad81a`. Fecha: 17/10/2026,
19:33:23.385031 a 19:33:38.084356, Buenos Aires.

[Enlace de la ejecución existente](https://smith.langchain.com/o/4e1308b3-31f5-4580-ac80-b762ab74e4dc/projects/p/ad56b0c4-866e-47a2-9145-0f218035ad61/r/01a14bff-94b8-7c73-a84d-da89091ad81a?poll=true).
**Requiere acceso al workspace**; no se presenta como enlace público.

| Medida verificada por API | Valor |
|---|---:|
| Total raíz | 14.699325 s |
| Recuperación | 0.425542 s |
| Reranking | 8.816276 s |
| Generación, cadena | 5.368333 s |
| Tokens juez | 1122 entrada + 610 salida = 1732 |
| Tokens generador | 727 entrada + 372 salida = 1099 |
| Total de las dos llamadas distintas | 1849 entrada + 982 salida = 2831 |

No se suman otra vez los agregados de raíz o cadenas padre. Las llamadas al juez
y al generador ya están incluidas en las duraciones de sus respectivas etapas.
La salida API, el JSON local y las capturas son consistentes. No hay uso de
embeddings registrado en esta traza.

Seleccionados remotos en orden: DOC-008/000 (1.0), DOC-001/000 (1.0),
DOC-007/000 (1.0), DOC-008/001 (0.8). Se verificó por API su pertenencia a los ocho
candidatos, textos, orden, contexto efectivo y correspondencia respuesta/fuentes.

### Evidencia visual y único pendiente

- Principal conservada: [langsmith_trace.png](langsmith_trace.png).
- Complementarias: [recuperación](evidencias/langsmith/recuperacion.png),
  [juez](evidencias/langsmith/juez_relevancia.png) y
  [reranking existente](evidencias/langsmith/reranking.png).
- Contraste completo: [auditoría](evidencias/langsmith/auditoria_b4.md),
  [datos API](evidencias/langsmith/traza_api.json) y
  [controles](evidencias/langsmith/contraste_api.json).

Las imágenes iniciales son legibles y byte idénticas a los originales; muestran
tiempos, tokens y candidates [8 items]. La captura inicial de reranking estaba
en Input. Ese faltante visual quedó resuelto posteriormente con juez1.png,
juez2.png y select.png: ver el cierre final y sus enlaces más abajo. No se
fabricó ninguna vista ni se generó otra ejecución.

### Checklist final

| Punto | Estado según evidencia disponible |
|---|---|
| B.1: falla real y causa técnica | Implementado y validado en los casos documentados; DOC-007 era descartado por el filtro previo |
| B.2: chunking con solapamiento | Implementado y validado; 500/100 documentado localmente; comparaciones y límites conservados |
| B.3: reranking y comparación | Implementado y validado; ocho candidatos, mínimo 0.5 y hasta cuatro; no se declara mejora general |
| B.4: traza real, API, métricas y fuentes | Cumplido; capturas complementarias incorporadas y contrastadas con la API |

Opcionales y no bloqueantes: registrar chunking y hash de indexación como
metadata en futuras trazas. No son condiciones añadidas de la consigna y no se
implementaron. Las capturas solicitadas ya están incorporadas y la Parte B queda
cerrada en el alcance documentado. En esa etapa no se implementó C ni se hizo
commit, push, merge o PR.


---

## Checklist final vigente de la Parte B — B.4 cumplido

Se incorporaron las capturas de la misma ejecución, sin modificarlas:
[juez1.png](evidencias/langsmith/juez1.png),
[juez2.png](evidencias/langsmith/juez2.png) y
[select.png](evidencias/langsmith/select.png).
Las dos primeras muestran los elementos 0–5 del juicio y sus puntuaciones; la
tercera muestra los elementos 6–7 y selected con cuatro entradas, índices 0–3.
IDs y puntuaciones coinciden con la exportación API previamente contrastada.
Son legibles a resolución original; no se ejecutó una prueba ni traza nueva.

Los cuatro objetos de selected aparecen colapsados internamente, con seis
campos por objeto. Esa vista acredita el conteo de cuatro, mientras que los IDs,
contenidos y orden final se acreditan por API. No se presenta `{6 items}` como
seis seleccionados ni se confunde el orden de judge.items con el orden final:
DOC-008/000 (1.0), DOC-001/000 (1.0), DOC-007/000 (1.0), DOC-008/001 (0.8).
Algunos motivos se abrevian visualmente; el JSON remoto conserva los completos.

La principal [langsmith_trace.png](langsmith_trace.png) sigue mostrando tiempos
y tokens. La [recuperación](evidencias/langsmith/recuperacion.png) muestra ocho
candidatos, y el conjunto nuevo de juicio/selected completa el contraste visual
8→4. La [auditoría actualizada](evidencias/langsmith/auditoria_b4.md) y la
[revisión visual con hashes](evidencias/langsmith/revision_capturas_finales.json)
documentan esta incorporación. Los originales y evidencias anteriores se conservan.

Proyecto: **grupo-e-entrega-3-b4**.
[Enlace de la traza existente](https://smith.langchain.com/o/4e1308b3-31f5-4580-ac80-b762ab74e4dc/projects/p/ad56b0c4-866e-47a2-9145-0f218035ad61/r/01a14bff-94b8-7c73-a84d-da89091ad81a?poll=true),
que **requiere acceso al workspace**. Duración raíz API: 14.699325 s;
recuperación 0.425542 s, reranking 8.816276 s, generación 5.368333 s.
Tokens: juez 1122 entrada + 610 salida = 1732; generador 727 + 372 = 1099;
total de dos llamadas distintas 2831, sin duplicar agregados de padres.
Chunking 500/100 acreditado por el manifiesto local; esos parámetros no están
registrados en la traza. Un hash enlazado a la indexación es una mejora opcional,
no un requisito adicional de cierre.

| Punto | Estado final | Evidencia |
|---|---|---|
| B.1 | Cumplido | Falla real, respuesta esperada, recuperación, filtro y causa técnica documentados |
| B.2 | Cumplido | Chunking 500/100, colección adicional, metadatos, integridad y comparación real |
| B.3 | Cumplido | Ocho candidatos sin corte previo; juez validado; mínimo 0.5; hasta cuatro; casos documentados |
| B.4 | Cumplido | Traza existente leída por API; métricas, entradas/salidas, fuentes y capturas complementarias contrastadas |

**Parte B completa según la consigna, en el alcance documentado. Pendientes
obligatorios: ninguno.** Esto no implica mejora general ni resultados RAGAS.
No se ejecutaron nuevas pruebas ni nuevas llamadas LLM/API en esta incorporación.
No se implementó Parte C y no se hizo commit, push, merge ni PR.

## C.3 — Comparación básico vs. avanzado

Se conservaron las diez preguntas del [golden aprobado](evaluacion_ragas/golden_dataset.json), sus referencias y las veinte respuestas `basic`/`rerank`. No se volvieron a ejecutar pipelines. El corpus aprobado sigue teniendo **17 documentos y 35 chunks**; la [validación de identidad lógica](README.md#chromadb-preparación-y-comprobación-del-corpus-aprobado) acepta UUID internos diferentes, pero conserva controles exactos de contenido, IDs lógicos, metadatos, configuración, chunking y huellas de vectores. No se modificó el manifiesto ni se regeneraron embeddings del corpus.

**Estado vigente: C.1–C.4 cumplidos para esta corrida, disponible para revisión.** Se recuperaron exclusivamente las 18 métricas que tenían `evaluation_error`: quedan **72 puntuaciones válidas, 8 no aplicables y 0 errores técnicos pendientes**. Las veinte generaciones, el dataset, los contextos y los 62 estados previamente válidos/no aplicables conservaron sus hashes. [Resultado de la continuación](evidencias/ragas/reintentos/continuacion_01/resultado.json), [plan e integridad](evidencias/ragas/reintentos/continuacion_01/plan.json), [errores originales](evidencias/ragas/reintentos/continuacion_01/originales/) y [resumen anterior](evidencias/ragas/reintentos/continuacion_01/resumen_antes/).

La instalación nueva desde `uv.lock` en `.venv-repro` pasó imports, dependencias y pruebas locales con CPython **3.14.8**, Windows 11 AMD64 y uv **0.13.1**, conservando `.venv`. Las fuentes instaladas de RAGAS coinciden con las del entorno original. [Resultado de instalación](evidencias/ragas/instalacion_limpia/resultado.json) y [comandos y alcance en README](README.md).

Configuración original preservada: generador compartido `gemini-3.1-flash-lite`, temperatura 0 y mismo prompt; básico top-3/distancia máxima 0.28; avanzado 500/100, hasta ocho candidatos sin corte previo, relevancia mínima 0.5 y hasta cuatro seleccionados. RAGAS **0.2.15**, evaluador `gemini-3.1-flash-lite` a temperatura 0, máximo de salida 8192; embeddings evaluadores `gemini-embedding-001`, dimensión 768, `SEMANTIC_SIMILARITY`. Se conservaron `Faithfulness`, `ResponseRelevancy` (Answer Relevancy, strictness 3), `LLMContextPrecisionWithReference` y `LLMContextRecall`, sus prompts y los límites HTTP/métrica de 120/180 segundos. [Configuración original](evidencias/ragas/configuracion.json), [integración](evaluacion_ragas/INTEGRACION.md) y [protocolo previo](evaluacion_ragas/PROTOCOLO.md).

La continuación cambió solo la planificación del transporte: peticiones secuenciales, incluidas las tres preguntas internas de Answer Relevancy, pausa mínima de 12 segundos y hasta tres intentos transitorios. Se registraron **55 intentos nuevos: 48 exitosos y 7 errores 503 recuperados**, cuyo mensaje indicó alta demanda temporal. No hubo nuevos 429 ni timeout terminal; no se puede determinar retroactivamente la causa concreta de los 429 antiguos porque sus cuerpos detallados no se guardaron. El transporte respeta `Retry-After`/`RetryInfo` y detiene ante cuota agotada o un 429 sin clasificación suficiente; esa detención no fue necesaria en esta tanda. [Auditoría de llamadas](evidencias/ragas/resumen/auditoria_llamadas.json).

Cada delta usa exactamente los mismos IDs válidos en ambas variantes. Con los errores resueltos, las medias descriptivas por variante coinciden con las medias pareadas. Valores redondeados a cuatro decimales; los originales se conservan sin reemplazos.

| Métrica | Básico | Avanzado | Delta avanzado−básico | Pares válidos |
|---|---:|---:|---:|---:|
| Faithfulness | 0.9667 | 1.0000 | +0.0333 | 10 |
| Answer Relevancy | 0.6593 | 0.7669 | +0.1075 | 10 |
| Context Precision con referencia | 0.6250 | 0.6250 | 0.0000 | 8 |
| Context Recall | 0.9375 | 0.9844 | +0.0469 | 8 |

Faithfulness y Answer Relevancy incluyen S1–S3, C1–C3, E1/E2 e I1/I2. Precision y Recall excluyen únicamente **E1 y E2**, en ambas variantes, por ausencia de una referencia factual positiva. Los ocho estados no aplicables originales se conservaron. El delta bruto de Precision es aproximadamente `6.25e-12`: es una diferencia numérica despreciable, no una mejora sustantiva. Los otros tres deltas son positivos; no se descartó ningún valor desfavorable.

E1/E2 se abstienen correctamente en ambas variantes, sin inventar requisitos ni honorarios. E2/básico agrega una cita a DOC-002 y no coincide literalmente con la frase canónica; la revisión funcional confirma la abstención. Answer Relevancy mantiene 0 para los cuatro escapes. Faithfulness conserva los valores brutos, sin convertir una abstención correcta en una afirmación de cobertura factual. No hubo `judge_error` ni `execution_error` de los pipelines. [Revisión de escapes](evidencias/ragas/resumen/revision_escapes.json).

La cobertura del contexto mejora en casos concretos: C1 pasa de 0.75 a 0.875 y C2 de 0.75 a 1. En C1 el avanzado incorpora los comprobantes ausentes en el básico, pero deja fuera el segundo chunk de IVA; la referencia completa de cinco chunks se mantuvo frente al máximo de cuatro seleccionados. En C2 el básico recupera requisitos del alta y se abstiene sobre la cuota; el avanzado recupera ambos temas. Context Recall mide el respaldo disponible en el contexto, no demuestra por sí solo que la respuesta verbalice todos los hechos.

El delta de Faithfulness requiere especial cautela: **toda su diferencia proviene del 0.6667 ya guardado de S2/básico**. El juez descompuso tres componentes y rechazó uno por incluir la mención de DOC-004, pese a que el componente obra social aparece explícitamente en el texto. El generador recibió IDs y contenidos separados en el payload; RAGAS recibió los textos de `sources`. Es una limitación de representación/juicio del evaluador, sin evidencia de un componente inventado por el pipeline. Ese score válido no se recalculó ni corrigió manualmente. [Anomalías revisadas con hashes y juicios originales](evidencias/ragas/resumen/anomalias_evaluador.json).

Las [tablas individuales, veinte respuestas completas y contextos](evidencias/ragas/resumen/resultados_para_revision.md), [métricas JSON](evidencias/ragas/resumen/metricas_individuales.json), [CSV](evidencias/ragas/resumen/metricas_individuales.csv), [agregados y comparación pareada](evidencias/ragas/resumen/resumen.json) y [juicios brutos indexados](evidencias/ragas/resumen/juicios_evaluador.json) permiten revisar el resultado completo. Las puntuaciones válidas anteriores no se repitieron; la continuidad se limita a los errores autorizados.

Limitaciones: diez preguntas, corpus simulado y consultas reutilizadas durante B (C1/E1/I1 literalmente, S1 por intención compartida y C2 parcialmente). Se combinaron puntuaciones originales con recuperaciones posteriores por errores técnicos, conservando configuración pero con posible variabilidad temporal del proveedor aun a temperatura 0. Las anomalías del evaluador limitan la interpretación factual de algunas mejoras. Esta única evaluación pequeña no demuestra generalización ni significancia estadística. No se ajustaron corpus, preguntas, referencias, pipeline o evaluador para favorecer al avanzado.

## C.4 — Peor métrica avanzada y propuesta técnica

La menor media avanzada es **Context Precision = 0.6250, n=8**, sin empate con otra métrica. S1/S2/S3/I1/I2 obtienen aproximadamente 1 y C1/C2/C3 obtienen 0. E1/E2 no aplican. El básico también obtiene 0.6250: no se observa una mejora sustantiva de precisión.

**C2/avanzado explica una anomalía verificable del evaluador.** Sus fuentes son DOC-002/chunks 0–1 y DOC-004/chunk 0. Los primeros aportan requisitos del alta y el tercero los componentes de la cuota; juntos obtienen Context Recall 1. Los tres juicios originales de precisión asignaron 0 porque cada fragmento no contenía toda la respuesta combinada; uno reconoce expresamente utilidad parcial y aun así lo rechaza. No se modificaron esos juicios ni se recalculó ese score válido. Ver `0e5116c2d20c49d6877bf9c14a707e7c`, `25a1b8002abe4a83943268aa2a1aed60` y `60c17bb37ad7474b8b99cf413ebd8dbf` en el [índice de juicios](evidencias/ragas/resumen/juicios_evaluador.json).

C1 y C3 muestran juicios que también penalizan que una fuente cubra solo una parte de una consulta compuesta. Esto no permite interpretar automáticamente los ceros como recuperación irrelevante. La causa probable es una aplicación excesivamente estricta e inconsistente de la utilidad de fragmentos por el juez LLM. Es una limitación de medición distinta de la falta real de cobertura de C1 y de la omisión de información en algunas respuestas. S2/Faithfulness aporta otra evidencia de sensibilidad a las citas: el hecho está en la fuente, pero el ID mencionado se trató como una afirmación adicional sin respaldo. Se conservan ambos tipos de evidencia sin corregir scores a mano.

**Propuesta futura de medición, no implementada:** anotar manualmente ejemplos de fragmentos útiles para una parte necesaria de una respuesta y ejemplos irrelevantes; calibrar el prompt oficial de `LLMContextPrecisionWithReference` mediante la API de prompts de RAGAS y contrastarlo con esas etiquetas antes de otra corrida completa. Representar además los IDs junto a los contenidos reales al evaluar citas. Cualquier cambio deberá versionarse como un evaluador distinto y conservar esta línea base; no autoriza reemplazar retrospectivamente los scores vigentes ni garantiza una mejora del pipeline.

**Propuesta futura para la limitación real del avanzado, no implementada:** seleccionar por cobertura de subpreguntas y expandir fragmentos contiguos del documento padre con un presupuesto explícito de contexto. El caso de aceptación sería incorporar el tramo de IVA que falta en C1 sin recortar su referencia de cinco chunks, y verificar el costo/ruido añadido. Debe autorizarse y medirse aparte. En esta etapa no se implementó ninguna mitigación ni se cambiaron modelos, prompts o parámetros de evaluación.
