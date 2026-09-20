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

---

## A.5 — Prueba destructiva: volatilidad de la RAM

`faiss.IndexFlatIP` vive en la memoria del proceso que lo crea. Para demostrar que `write_index()`/`read_index()` es lo único que separa "persiste" de "se pierde", se armaron dos escenarios sobre los mismos 16 documentos y se corrió cada uno dos veces **en procesos de Python separados** — un proceso nuevo no puede ver la RAM del anterior, que es exactamente lo que pasa cuando un servidor se reinicia.

### Escenario 1 — sin `write_index()`

Un script temporal (`_tmp_sin_persistencia.py`, descartado después de la prueba) construye el índice en memoria y nunca lo guarda en disco:

```text
=== EJECUCIÓN 1 (proceso nuevo, simula el primer arranque) ===
Generando embeddings (SIN persistencia: no se llama a write_index)...
  -> 16 embeddings generados en 1.64s (llamada real a la API).
Índice en RAM: 16 vectores. NO se guarda en disco.

=== EJECUCIÓN 2 (otro proceso nuevo, simula un restart) ===
Generando embeddings (SIN persistencia: no se llama a write_index)...
  -> 16 embeddings generados en 0.97s (llamada real a la API).
Índice en RAM: 16 vectores. NO se guarda en disco.
```

Antes y después de las dos corridas, `ls *.index` no encuentra ningún archivo. Las dos ejecuciones imprimen "Generando embeddings" y hacen una llamada real a la API de `gemini-embedding-001`: el índice se pierde al terminar el proceso y el segundo "arranque" vuelve a pagar los tokens de los 16 documentos, exactamente igual que el primero.

### Escenario 2 — con `write_index()` / `read_index()`

Mismo experimento sobre `pipeline_vectorial.py`, partiendo de un estado limpio (sin `estudio_contable.index` en disco):

```text
=== EJECUCIÓN 1 (primer arranque, no existe el .index) ===
Generando embeddings...
Índice listo: 16 vectores de dimensión 768.
[... resultados de las 3 consultas de A.4 ...]

$ ls -la estudio_contable.index estudio_contable_ids.json
-rw-r--r-- 1 Martin 197609 49197 estudio_contable.index
-rw-r--r-- 1 Martin 197609   227 estudio_contable_ids.json

=== EJECUCIÓN 2 (simula un restart: el .index ya existe en disco) ===
Cargando índice FAISS desde disco...
Índice listo: 16 vectores de dimensión 768.
[... mismos resultados, sin llamar a la API ...]
```

La primera ejecución imprime "Generando embeddings..." y deja `estudio_contable.index` (49.197 bytes) y `estudio_contable_ids.json` en disco. La segunda ejecución — un proceso nuevo, sin memoria compartida con el anterior — imprime "Cargando índice FAISS desde disco..." en su lugar: entra directo a `faiss.read_index()`, no vuelve a llamar a `generar_embeddings()` y devuelve los mismos scores sin gastar un solo token.

### Reflexión

Si el servidor de producción se reinicia y el índice solo vive en RAM (Escenario 1), se pierde entero y hay que rehacer todos los embeddings antes de poder responder la primera consulta — downtime y costo de tokens en cada deploy o crash. Con `write_index()` en un volumen persistente (Escenario 2) el proceso nuevo recarga en milisegundos; con dos servidores el problema se traslada a la sincronización, ya que cada instancia con su propio disco local reconstruiría el índice por separado (inconsistente y `n` veces más caro), por lo que hace falta un almacenamiento compartido — o directamente una base vectorial con servidor propio, que es el problema que resuelve ChromaDB en la Parte B.

---

# Parte B — ChromaDB, filtrado híbrido y ETL

## B.1 — Migración a ChromaDB

`vector_db.py` carga los mismos 16 documentos de `base_conocimiento.json` en una colección de ChromaDB persistente. Tres decisiones de diseño:

**1. `PersistentClient`, no `Client()`.** `chromadb.PersistentClient(path="chroma_db")` escribe la colección en disco, en la carpeta `chroma_db/` (ignorada por `.gitignore`, igual que `*.index`). Un `Client()` sin ruta vive solo en RAM y se pierde al terminar el proceso — el mismo problema que se demostró a mano en A.5, pero acá lo resuelve la librería en vez de un `write_index()` manual.

**2. Espacio de similitud coseno explícito.** La colección se crea con `metadata={"hnsw:space": "cosine"}` para que sea comparable con los scores de FAISS de A.4, que también usa coseno (`IndexFlatIP` sobre vectores normalizados).

**3. Misma función de embeddings que FAISS.** Por default, ChromaDB vectoriza con un modelo local (`all-MiniLM-L6-v2`) si no se le indica lo contrario. Para que la Parte B sea coherente con la Parte A y los scores no salgan de dos espacios vectoriales distintos, se escribió `GeminiEmbeddingFunction`, una clase que envuelve `gemini-embedding-001` (el mismo modelo de `pipeline_vectorial.py`) y se la pasa a la colección con `embedding_function=GeminiEmbeddingFunction(task_type="RETRIEVAL_DOCUMENT")`.

**Un ajuste que exigió la migración**: ChromaDB solo acepta `str`, `int`, `float` o `bool` como valor de metadato — no listas. `tags_regionales` en `base_conocimiento.json` es una lista (p. ej. `["iva", "ddjj", ...]`), así que `aplanarTagsRegionales()` la convierte a un único string separado por comas (`"iva, ddjj, declaracion jurada, ..."`) antes de insertar. El campo sigue siendo texto libre para filtrar por contención (`$contains`), no se perdió información, solo cambió el tipo de contenedor.

**Ingesta con `upsert`, no `add`.** `coleccion.upsert(ids=ids, documents=documents, metadatas=metadatas)` permite re-ejecutar `vector_db.py` sin duplicar: `add()` fallaría o duplicaría IDs en una segunda corrida, `upsert()` inserta si el ID es nuevo y actualiza si ya existe.

### Evidencia: carga y verificación

```text
$ uv run vector_db.py
Colección 'estudio_contable' lista: 16 documentos.

$ uv run vector_db.py   # segunda corrida, mismos datos
Colección 'estudio_contable' lista: 16 documentos.
```

El conteo se mantiene en 16 en la segunda corrida — evidencia de que `upsert` no duplicó nada.

Verificación de un documento puntual con `coleccion.get(ids=["DOC-001"])`:

```text
{
  'ids': ['DOC-001'],
  'documents': ['El IVA es un impuesto mensual. El responsable inscripto presenta la declaración
                 jurada del período y paga el saldo en el mismo mes siguiente al que liquida. ...'],
  'metadatas': [{
    'categoria': 'vencimientos',
    'activo': True,
    'jurisdiccion': 'nacional',
    'tipo_contribuyente': 'responsable_inscripto',
    'tags_regionales': 'iva, ddjj, declaracion jurada, vencimiento, terminacion de cuit,
                         calendario fiscal, arca, afip'
  }]
}
```

---

## B.2 — Los tres límites de FAISS que ChromaDB resuelve

| Límite de FAISS | Cómo se manifiesta en el dominio | Cómo lo resuelve ChromaDB |
|---|---|---|
| Sin persistencia transaccional / atomicidad | `write_index()` escribe el `.index` entero de una sola vez, sin noción de commit parcial. Si el proceso se cae a mitad de una actualización (por ejemplo regenerando los 16 embeddings después de dar de baja `DOC-016`) y nunca llega a llamar `write_index()`, se pierde todo lo trabajado en esa corrida y hay que rehacerla completa (mismo problema demostrado a mano en A.5). Además `IndexFlatIP` no tiene "update" ni "delete": para cambiar un solo vector hay que reconstruir el índice entero. | ChromaDB persiste sobre un motor propio (SQLite + segmentos HNSW) donde cada `upsert`/`delete` se confirma por documento. Si el proceso se cae a mitad de un `upsert` de 16 documentos, los que ya se comprometieron quedan guardados en disco y la colección no queda corrupta ni a medio escribir. |
| Sin filtrado híbrido nativo | `IndexFlatIP.search()` solo entiende vectores, no sabe qué es `jurisdiccion` o `activo`. Para separar `DOC-010` (IIBB CABA) de `DOC-011` (IIBB PBA) (semánticamente casi idénticos) no queda otra que buscar top-K y filtrar el resultado con un `if` en Python | `coleccion.query(query_texts=[...], where={"jurisdiccion": {"$eq": "caba"}})` aplica el filtro **dentro** del motor, en la misma llamada que la búsqueda semántica: la similitud coseno se calcula únicamente sobre el subconjunto que ya cumple el filtro, nunca sobre los documentos que se van a descartar. |
| CRUD ineficiente / sin concurrencia | Actualizar la cuota mensual de `DOC-004` cuando cambia el monto exige regenerar embeddings de los 16 documentos y volver a llamar `write_index()`, aunque los otros 15 no cambiaron (no hay operación de "tocar un solo documento"). Tampoco hay locking: dos procesos escribiendo el mismo `.index` al mismo tiempo pueden pisarse el archivo. | `coleccion.upsert(ids=["DOC-004"], documents=[...], metadatas=[...])` actualiza un único documento sin tocar los otros 15, con el motor de Chroma manejando el acceso concurrente por dentro. Es literalmente el escenario que se prueba en B.3 (evento de negocio en caliente). |




