# TP Integrador — Entrega 2

Del Prompt Saturado a la Base de Conocimiento Vectorial.

Este informe continúa el proyecto de la Entrega 1 (asistente de un estudio contable). El informe de la Entrega 1 queda en `informe.md`.

> **Encuadre.** Los documentos de `base_conocimiento.json` son documentos **simulados** de un estudio contable, escritos para este trabajo práctico. No son normativa fiscal real ni constituyen asesoramiento tributario.

---

## A.1 — Autopsia del contexto estático

| Problema | Aplicado a su dominio |
|---|---|
| Desangre de tokens | La base tiene 16 documentos que suman 3.488 tokens (medidos con el tokenizador de `gpt-4o`, promedio de 218 por documento). Una consulta típica mide 26 tokens, así que pasar la base entera en cada mensaje es enviar unas 134 veces más texto que la pregunta, y para "¿cuándo vence el monotributo?" solo hace falta `DOC-004`: los otros 15 documentos son 3.269 tokens (94%) pagados de más. Con un supuesto de 1.000 consultas diarias son 3.488.000 tokens por día, y como el costo crece lineal con la base, un estudio con 200 documentos pagaría unos 43,6 millones de tokens por día. |
| Lost in the Middle | En el prompt estático los documentos quedan en el orden del archivo, y `DOC-008` (cargas sociales del empleador) cae en la posición 8 de 16, al centro exacto. Con 16 documentos el efecto es mínimo, pero con la base real de un estudio la regla que el cliente pregunta queda enterrada entre cientos de párrafos ajenos, en la zona donde el modelo presta menos atención, y puede pasarla por alto aunque esté en el prompt. |
| Inconsistencia de estado concurrente | `DOC-004` (cuota mensual de Monotributo, que vence alrededor del día 20) pasa a `activo: false` cuando el estudio lo reemplaza. Un System Prompt armado antes de ese cambio sigue informando el vencimiento y el monto viejos durante toda la conversación, y lo mismo pasa entre `DOC-009` (planes de pago vigentes) y `DOC-016` (régimen cerrado): el prompt estático entrega los dos y el modelo no sabe cuál rige. |

Un `SELECT ... WHERE descripcion LIKE '%...%'` busca coincidencias de texto, no significado: la consulta "¿Qué papeles les tengo que mandar para anotarme en el monotributo?" no aparece literal en ningún documento, y `LIKE '%monotributo%'` devuelve `DOC-002`, `DOC-004` y `DOC-015` sin criterio para ordenarlos ni para saber que el correcto es el de documentación requerida para el alta. La búsqueda vectorial permite recuperar documentos por similitud semántica y no solamente por coincidencia literal.

---

## A.2 — Similitud coseno a mano

El dominio se reduce a dos ejes: **X = carga de vencimiento** (cuándo hay que pagar o presentar) e **Y = carga de documentación y trámite** (qué papeles se necesitan y en qué estado está). Son los dos ejes sobre los que ya está construida la base — `vencimientos` cae sobre X, `documentacion` y `comprobantes` sobre Y, `tramites` mezcla los dos — y las dos preguntas que el estudio recibe todos los días.

| Vector | Documento de la base | `[X, Y]` |
|---|---|---|
| DOC 1 | `DOC-001` — Vencimientos de IVA | `[0.9, 0.2]` |
| DOC 2 | `DOC-002` — Alta de Monotributo | `[0.2, 0.9]` |
| DOC 3 | `DOC-003` — Estado de la DDJJ de IVA | `[0.5, 0.7]` |
| Consulta | "¿Cuándo vence el IVA?" | `[1.0, 0.1]` |

### Los tres cálculos

`Similitud = (A · B) / (‖A‖ × ‖B‖)`, con `‖B‖ = √(1.0² + 0.1²) = √1.01 ≈ 1.004988` en los tres.

**DOC 1 — Vencimiento IVA**, `A = [0.9, 0.2]`:

```
A · B = 0.9 × 1.0 + 0.2 × 0.1 = 0.92
‖A‖   = √(0.81 + 0.04) = √0.85 ≈ 0.921954
cos   = 0.92 / (0.921954 × 1.004988) ≈ 0.993
```

**DOC 3 — Estado de un trámite**, `A = [0.5, 0.7]`:

```
A · B = 0.5 × 1.0 + 0.7 × 0.1 = 0.57
‖A‖   = √(0.25 + 0.49) = √0.74 ≈ 0.860233
cos   = 0.57 / (0.860233 × 1.004988) ≈ 0.659
```

**DOC 2 — Documentación Monotributo**, `A = [0.2, 0.9]`:

```
A · B = 0.2 × 1.0 + 0.9 × 0.1 = 0.29
‖A‖   = √(0.04 + 0.81) = √0.85 ≈ 0.921954
cos   = 0.29 / (0.921954 × 1.004988) ≈ 0.313
```

Ranking: DOC 1 (0.993) > DOC 3 (0.659) > DOC 2 (0.313). La consulta pregunta por un vencimiento y gana el documento de vencimientos.

### Validación con NumPy

`similitud_coseno.py` calcula las tres similitudes dos veces, a mano y con NumPy, y compara los resultados:

```python
import numpy as np

def similitud_coseno(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

Salida de `uv run similitud_coseno.py`:

```text
Documento                             manual     numpy
DOC 1 — Vencimiento IVA             0.992928  0.992928
DOC 2 — Documentacion Monotributo   0.312988  0.312988
DOC 3 — Estado de un tramite        0.659323  0.659323

Manual y NumPy coinciden (np.allclose, atol=1e-12).
```

### El umbral de aceptación

Un resultado se acepta a partir de **0.80 de similitud**, que en ChromaDB equivale a **distancia ≤ 0.20**. El valor cae dentro del hueco de 0.334 que separa al documento correcto (0.993) del mejor distractor (0.659), con margen de los dos lados, y es un umbral inicial que habrá que recalibrar contra los embeddings reales. Si ningún documento lo supera, el sistema no devuelve el más cercano: responde que no dispone de información suficiente.

---

## A.3 — `base_conocimiento.json`

La base de conocimiento es la fuente de verdad del sistema: el índice FAISS y la colección de ChromaDB se reconstruyen enteros desde este archivo.

Contiene **16 documentos**, `DOC-001` a `DOC-016`. Cada registro tiene dos partes, y esa división es la decisión central de la sección:

```json
{
  "id": "DOC-001",
  "descripcion_semantica": "El IVA es un impuesto mensual. El responsable inscripto presenta ...",
  "metadatos": {
    "categoria": "vencimientos",
    "activo": true,
    "jurisdiccion": "nacional",
    "tipo_contribuyente": "responsable_inscripto",
    "tags_regionales": ["iva", "ddjj", "declaracion jurada", "vencimiento", "terminacion de cuit", "calendario fiscal", "arca", "afip"]
  }
}
```

### La Regla del Arquitecto aplicada

`descripcion_semantica` es **lo único que se vectoriza**. Los metadatos no entran al embedding: son filtros que se aplican antes o después de la búsqueda por similitud.

De ahí sale el criterio para repartir la información:

| Va al párrafo | Va a metadatos |
|---|---|
| Explicación, contexto, condiciones, excepciones | Valores discretos sobre los que se filtra |
| Lo que el cliente pregunta con sus palabras | Lo que el sistema ya sabe antes de buscar |
| Lo que se recupera por significado | Lo que la similitud semántica **no** puede distinguir |

La tercera fila es la que más importa. El embedding es bueno para acercar "¿qué papeles llevo para anotarme como pequeño contribuyente?" a un documento que habla de "documentación requerida para el alta de Monotributo". Es malo para distinguir un documento vigente de uno derogado, o IIBB de CABA de IIBB de PBA: en los dos casos los textos son casi idénticos y los vectores quedan pegados. Eso no se arregla con mejores embeddings, se arregla con un filtro exacto.

### Esquema de metadatos

Cinco campos. La consigna pide como mínimo un campo categórico, un booleano de estado y `tags_regionales`; los otros dos están porque resuelven un problema concreto del dominio, no por completitud.

| Campo | Tipo | Valores admitidos | Por qué es metadato y no texto |
|---|---|---|---|
| `categoria` | string | `vencimientos`, `documentacion`, `tramites`, `normativa`, `comprobantes`, `casos_complejos`, `datos_fiscales` | Conjunto cerrado de 7 valores. Es el campo que traduce la intención clasificada por el modelo a un subconjunto de la base. Tiene que ser exacto: la similitud confunde "vencimiento de IVA" con "documentación para liquidar IVA", y son consultas distintas. |
| `activo` | booleano | `true`, `false` | Estado de vigencia. Un documento derogado es semánticamente idéntico al vigente que lo reemplaza. Solo un filtro duro evita que el sistema conteste con un régimen caído. |
| `jurisdiccion` | string | `nacional`, `caba`, `pba` | Dato administrativo, no semántico. `DOC-010` (IIBB CABA) y `DOC-011` (IIBB PBA) describen el mismo tributo con casi las mismas palabras. El vector no los separa; el filtro sí. |
| `tipo_contribuyente` | string | `responsable_inscripto`, `monotributo`, `persona_humana`, `empleador`, `general` | Condición del cliente, conocida antes de buscar porque se deriva del CUIT. Filtrar por ella descarta documentos correctos pero inaplicables, que es el error más caro del dominio: contestarle a un monotributista con el calendario del responsable inscripto. |
| `tags_regionales` | lista de strings | jerga, siglas y nombres de impuesto: `iva`, `iibb`, `arba`, `agip`, `afip`, `arca`, `monotributo`, `cargas sociales`, ... | Vocabulario que el embedding cubre mal: siglas, jerga local y renombres institucionales (AFIP → ARCA). Son términos, no explicación, y por eso van a filtro léxico. |

### Cobertura de los 16 documentos

| ID | `categoria` | `jurisdiccion` | `tipo_contribuyente` | `activo` | Tema |
|---|---|---|---|---|---|
| DOC-001 | vencimientos | nacional | responsable_inscripto | true | Vencimientos de IVA |
| DOC-002 | documentacion | nacional | monotributo | true | Alta de Monotributo |
| DOC-003 | tramites | nacional | responsable_inscripto | true | Estado de la DDJJ de IVA |
| DOC-004 | vencimientos | nacional | monotributo | true | Cuota mensual de Monotributo |
| DOC-005 | documentacion | nacional | persona_humana | true | DDJJ anual de Ganancias |
| DOC-006 | tramites | nacional | general | true | Alta y modificación de datos fiscales |
| DOC-007 | documentacion | nacional | responsable_inscripto | true | Comprobantes para liquidar IVA |
| DOC-008 | normativa | nacional | empleador | true | Cargas sociales |
| DOC-009 | tramites | nacional | general | true | Planes de pago vigentes |
| DOC-010 | normativa | caba | general | true | IIBB CABA (AGIP) |
| DOC-011 | normativa | pba | general | true | IIBB PBA (ARBA) |
| DOC-012 | comprobantes | nacional | general | true | Entrega de comprobantes |
| DOC-013 | casos_complejos | nacional | general | true | Intimaciones y requerimientos |
| DOC-014 | datos_fiscales | nacional | general | true | Actualización de datos fiscales |
| DOC-015 | documentacion | nacional | general | true | Certificados y constancias |
| DOC-016 | tramites | nacional | general | **false** | Régimen de regularización cerrado |

Los 7 valores de `categoria`, las 3 jurisdicciones y los 5 tipos de contribuyente están representados. Los párrafos van de 147 a 176 palabras.

Tres pares están puestos a propósito para que la búsqueda tenga con qué fallar si el filtrado no funciona:

- **DOC-010 / DOC-011** — el mismo impuesto en dos jurisdicciones. Solo los separa `jurisdiccion`.
- **DOC-009 / DOC-016** — el mismo trámite, uno vigente y otro cerrado. Solo los separa `activo`. Es el par que sostiene la purga del ETL y la Killer Query de vigencia.
- **DOC-006 / DOC-014** — ambos hablan de datos fiscales, pero uno es el procedimiento de seguimiento y el otro es la operación de escritura sobre el padrón. Los separa `categoria`.

### Los párrafos contienen el conocimiento, no lo describen

Cada `descripcion_semantica` contiene qué se paga o se presenta, cuándo vence, con qué comprobantes, y cierra con la jerga real con la que el cliente pregunta ("hasta cuándo tengo tiempo de pagar las cargas sociales", "qué papeles necesito para anotarme como pequeño contribuyente"). Esa jerga dentro del párrafo es lo que acerca el vector de la pregunta al vector del documento.

