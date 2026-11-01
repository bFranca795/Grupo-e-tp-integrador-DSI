# TP Integrador — Entrega 3: LCEL y RAG avanzado

## Resumen de la entrega

La Entrega 3 evoluciona la base vectorial de la Entrega 2 hacia un
pipeline RAG completo con LangChain LCEL. El sistema reutiliza la
colección `estudio_contable`, incorpora guardrails, trazabilidad de
fuentes, chunking con solapamiento 500/100, reranking mediante LLM y
evaluación cuantitativa con RAGAS.

La comparación final se realizó sobre el mismo corpus y el mismo
Golden Dataset para el pipeline básico y avanzado. Las evidencias
detalladas de ejecución se conservan en la carpeta `evidencias/`.

# A.3 Matriz de Validación de Resiliencia

Ejecutar el pipeline y documentar el comportamiento frente a 4 escenarios clave:

| Tipo de Prueba | Comportamiento Esperado |
|---|---|
| Factual directa | Responde citando los documentos correctos: recupera `DOC-002` (requisitos de alta en Monotributo) con distancia 0.2089 y similitud 0.7911 frente a la consulta factual. |
| Fuera de dominio | Activa la cláusula de escape ("No poseo información..."): ante una consulta fitosanitaria/ganadera, la distancia mínima es 0.4244 (> 0.28) y activa la cláusula de escape. |
| Ataque complacencia | Deniega beneficios o afirmaciones falsas sin inventar datos: recupera `DOC-009` (distancia 0.2550 y similitud 0.7450) desmintiendo la prórroga automática y acreditando la caducidad a las 2 cuotas impagas. |
| Uso de sinónimos | Encuentra el documento y responde correctamente pese al cambio de palabras: recupera `DOC-007` (distancia 0.2475 y similitud 0.7525) para liquidación de IVA reconociendo "gravamen al valor agregado" y "arrimarles comprobantes". |


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

La falla se categoriza como ruido en el contexto. En una pregunta compuesta,
el retriever prioriza documentos parcialmente relacionados y deja fuera del
contexto final a `DOC-007`, aunque contiene información necesaria para completar
la respuesta. El diagnóstico sin umbral mostró que `DOC-007` aparece en tercer
lugar con distancia `0.3176`, por encima del corte de `0.28`, por lo que queda
excluido.

No se trata de un chunk cortado, ya que en el RAG básico se recuperan
documentos completos, ni de Lost in the Middle, porque no hay evidencia de
que la información relevante haya sido recuperada y luego ignorada por el LLM.
El problema ocurre antes: el contexto final queda contaminado o incompleto por
la selección del retriever y el umbral aplicado.

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

La métrica más baja del RAG avanzado fue Context Precision = 0.6250. Sin embargo, el análisis de los casos con score 0 muestra que este resultado no puede atribuirse directamente a que el retriever haya recuperado contexto irrelevante.

En particular, en el caso C2 los chunks recuperados contienen información necesaria para construir la respuesta y el sistema obtiene Context Recall = 1. Aun así, RAGAS asignó Context Precision 0 porque cada fragmento individual no contenía por sí solo toda la respuesta combinada. Se observó un comportamiento similar en C1 y C3. Por lo tanto, la causa probable de la baja métrica es una evaluación excesivamente estricta de la utilidad parcial de los chunks por parte del juez LLM de RAGAS, y no evidencia suficiente de ruido real introducido por el retriever.

Como mejora futura se propone calibrar la evaluación de Context Precision utilizando ejemplos etiquetados manualmente de chunks parcialmente útiles e irrelevantes, y contrastar esos resultados con el juicio automático de RAGAS antes de una nueva evaluación completa. Esta mejora modificaría el proceso de evaluación, no los resultados actuales, que se conservan como línea base.