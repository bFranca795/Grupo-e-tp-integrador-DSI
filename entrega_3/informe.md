# TP Integrador — Entrega 3: LCEL y RAG avanzado

**Estado de la entrega:** B.1–B.3 están implementados y validados en los casos
documentados. Esto no constituye una mejora general ni una evaluación RAGAS.
**B.4 queda pendiente de ejecución y verificación con las credenciales del
compañero**: todavía no hay una captura ni enlace de traza real verificada.

Para completar B.4 en otra máquina, seguir [CONTINUAR_B4.md](CONTINUAR_B4.md). La ejecución y verificación de la traza son tareas pendientes; configurar variables por sí solo no las completa.

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
