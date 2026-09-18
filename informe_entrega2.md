# TP Integrador — Entrega 2

Del Prompt Saturado a la Base de Conocimiento Vectorial.

Este informe continúa el proyecto de la Entrega 1 (asistente de un estudio contable). El informe de la Entrega 1 queda en `informe.md`.

> **Encuadre.** Los documentos de `base_conocimiento.json` son documentos **simulados** de un estudio contable, escritos para este trabajo práctico. No son normativa fiscal real ni constituyen asesoramiento tributario.

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

---

## A.4 — `pipeline_vectorial.py`: embeddings e índice FAISS persistido

El script vectoriza las `descripcion_semantica` de los 16 documentos, construye el índice FAISS y lo persiste. Se ejecuta con `uv run pipeline_vectorial.py`.

**1. Credenciales.** La clave se lee del entorno con `python-dotenv` (`load_dotenv()` y `os.getenv("GEMINI_API_KEY")`); si falta, el script corta antes de trabajar. `.env` está en `.gitignore` y nunca estuvo trackeado.

**2. Embeddings.** Modelo `gemini-embedding-001`, la misma clave que usa `app.py`. `output_dimensionality=768` se fija explícitamente porque el índice se crea con esa dimensión y la recarga tiene que coincidir. `task_type` es asimétrico: `RETRIEVAL_DOCUMENT` al indexar y `RETRIEVAL_QUERY` al consultar, que es lo que acerca una pregunta corta y coloquial a un párrafo expositivo con el que no comparte vocabulario.

**3. Índice.** `faiss.IndexFlatIP` sobre vectores pasados por `faiss.normalize_L2`. Con norma 1 el producto interno **es** la similitud coseno, porque el denominador de `cos(a, b) = (a · b) / (||a|| · ||b||)` vale 1. Normalizar no es opcional acá: `gemini-embedding-001` es un modelo Matryoshka y truncar el vector de 3072 a 768 rompe la norma unitaria. Se elige coseno y no L2 para que los scores sean comparables con los de ChromaDB en la Parte B, que usa `hnsw:space: "cosine"` sobre los mismos documentos.

**4. Persistencia.** `faiss.write_index()` deja `estudio_contable.index` (49.197 bytes: 16 × 768 × 4 bytes de `float32` más encabezado) y, al lado, `estudio_contable_ids.json` con los identificadores en orden de inserción — hace falta porque `IndexFlatIP` guarda vectores y `search()` devuelve posiciones, que sin ese mapeo no significan nada al recargar. Si los dos archivos existen, `faiss.read_index()` los recupera y **no se regeneran los embeddings de los documentos**; si falta cualquiera, el índice se reconstruye entero. Ninguno se versiona: son artefactos derivados, se regeneran corriendo el script y están en `.gitignore`.

**5. Búsqueda semántica.** Las tres consultas están escritas sin compartir vocabulario literal con el documento que deberían recuperar.

| Consulta | # | Documento | `categoria` | Score |
|---|---|---|---|---|
| ¿Qué papeles necesitan para darme de alta en monotributo? | 1 | DOC-002 | `documentacion` | **0,8201** |
| | 2 | DOC-015 | `documentacion` | 0,6755 |
| | 3 | DOC-005 | `documentacion` | 0,6732 |
| ¿Cómo está mi declaración jurada de IVA? | 1 | DOC-003 | `tramites` | **0,7882** |
| | 2 | DOC-001 | `vencimientos` | 0,7287 |
| | 3 | DOC-007 | `documentacion` | 0,6912 |
| Me llegó una intimación fiscal, ¿qué hago? | 1 | DOC-013 | `casos_complejos` | **0,8275** |
| | 2 | DOC-015 | `documentacion` | 0,6827 |
| | 3 | DOC-005 | `documentacion` | 0,6731 |

Las tres recuperan el documento correcto en primer lugar. Contra el umbral de 0,80 fijado en A.2, dos lo superan y la segunda queda en 0,7882 pese a haber acertado el documento: se reporta el número como salió y no se mueve el umbral para acomodarlo.
