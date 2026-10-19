# Revisión editorial del golden dataset — pendiente de aprobación

Base: `5a9b9b7f4681d64f1b07bf7ea8e92c4e77f937fa`, cierre de B con evidencias LangSmith. Rama: `c-evaluacion-ragas`. No se identificaron AGENTS.md en el repositorio. Estado inicial de Git limpio; no se hicieron commits, push, merge ni PR.

## Corpus de referencia

Se inspeccionó `chroma_db/chroma.sqlite3` con SQLite `mode=ro` y `query_only`. No se abrió PersistentClient ni se escribieron colecciones o embeddings. Hay 17 documentos y 35 chunks, dimensión 768. El manifiesto conserva textos, metadatos, IDs, hashes canónicos, correspondencia padre/chunks y configuración; no contiene secretos, embeddings ni bases binarias. Para reconstruir vectores en otra máquina será necesaria una preparación autorizada por separado; estos snapshots no son una copia del índice.

Frente al JSON limpio (normalizando tags a la representación de Chroma), solo cambia DOC-003: el texto pasa del catálogo general de estados a un trámite finalizado, presentado y pagado o compensado, y cambian sus tags. Sus metadatos no vinculan un CUIT. Todos los demás documentos coinciden, incluido el registro de prueba DOC-002-dup-1. DOC-016 se conserva inactivo, con el mismo estado en la derivada.

El registro histórico `../evidencias/b4_companero/indexacion.json` contiene 18/36 y señala DOC-003 y DOC-00X como diferencias. DOC-00X no existe en ninguna colección local inspeccionada; esa evidencia no acredita que el corpus local actual tenga 18 documentos. No se incorporó el documento ni se dedujo su contenido. La evaluación futura deberá usar exactamente el corpus 17/35 de este manifiesto para ambas variantes; si cambia, revisar referencias antes de ejecutar.

## Revisión semántica propuesta

- S1: lista completa de comprobantes, incluida la condición de los tickets; DOC-007, chunk 0.
- S2: los tres componentes; DOC-004, chunk 0.
- S3: ambos comprobantes y sus rasgos; DOC-012, chunk 0. La pregunta no pide recuperar un archivo privado.
- C1: combina comprobantes (DOC-007/0), fechas de IVA (DOC-001/0–1) y obligaciones sociales (DOC-008/0–1). Ningún chunk contiene las tres materias. La referencia completa abarca cinco chunks: supera el máximo de cuatro seleccionados del avanzado. Se mantiene como limitación a medir, sin recortar hechos para favorecerlo.
- C2: requisitos y datos condicionales del alta (DOC-002/0–1), más composición de la cuota (DOC-004/0). Son materias separadas.
- C3: organismos y obligaciones locales de ambas jurisdicciones (DOC-010/0–1 y DOC-011/0–1). No confunde vencimientos ni aplica Convenio Multilateral al contribuyente exclusivamente local.
- E1: revisión de todos los documentos: ninguno responde requisitos fitosanitarios de exportación ganadera. Los certificados fiscales de DOC-015 no permiten responder.
- E2: no hay precios del estudio. Los requisitos del alta y la cuota tributaria no acreditan honorarios. Ambas listas de fuentes quedan vacías.
- I1: «arrimarles» equivale a entregar y «gravamen al valor agregado» a IVA; conserva exactamente las condiciones de S1.
- I2: se respalda orientación y derivación, no una estrategia ante una intimación concreta. DOC-013/0–2 contempla plazo aunque no se haya leído y reserva la evaluación al profesional. No es escape por ausencia de conocimiento.

No se proponen cambios a las diez preguntas. Las respuestas y hechos son una elaboración editorial desde las fuentes, sin usar las respuestas del pipeline como verdad de referencia ni normativa externa.

## Contaminación y alcance de la validación

C1, E1 e I1 se usaron literalmente en B (`CASES` y resultados históricos). S1 comparte intención con I1; C2 contiene el alta de Monotributo ya ensayada en `factual` y `b1_multi`. No se encontró uso de las otras formulaciones en las consultas registradas, sin garantizar independencia absoluta. El conjunto no es un test independiente ni permite afirmar generalización.

`validacion.json` separa comprobaciones automáticas de revisión semántica. Se verifican cantidad, IDs, distribución, campos, integridad del corpus, padres, índices, posiciones, hashes de IDs, metadatos, citas literales, correspondencia de listas y coherencia de escapes. Para categorías se verifica si los fragmentos de respaldo caben juntos en un chunk; esto no demuestra que el texto implique los hechos ni que no exista otra respuesta semánticamente suficiente. Los fragmentos son chunks íntegros, para conservar contexto de cada hecho. Las conclusiones de este documento requieren aprobación humana, especialmente cobertura, necesidad de combinar y ausencia de respuesta de los escapes.

No se ejecutaron pipelines, modelos generativos ni RAGAS. La preparación finaliza con el dataset para revisión.
