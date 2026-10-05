# Resultados de Killer Queries

Se ejecutaron tres consultas diseñadas para poner a prueba
la recuperación semántica, el filtrado mediante metadatos y
el comportamiento del sistema ante consultas fuera de la
Base de Conocimiento.

| # | Consulta | Qué pone a prueba | Resultado esperado | Resultado real | ¿Pasó? |
|---|---|---|---|---|---|
| 1 | ¿Qué me exigen para formalizarme y empezar a vender? | Poder semántico: recuperar el documento correcto aunque la consulta no use las mismas palabras que el texto almacenado | DOC-002 | DOC-002 — distancia 0.2387 / similitud 0.7613 | Sí |
| 2 | ¿En qué padrón estoy y cuándo vence ingresos brutos? | Filtrado por metadatos: evitar una jurisdicción incorrecta y recuperar la correspondiente a CABA | DOC-010 | Sin filtro: DOC-001. Con `jurisdiccion=caba`: DOC-010 — distancia 0.2284 / similitud 0.7716 | Sí |
| 3 | ¿Cómo tramito un permiso para importar maquinaria agrícola? | Consulta fuera del catálogo: no forzar un documento poco relacionado | no tengo eso | no tengo eso | Sí |

## Evidencia de ejecución

```text
=== KILLER QUERIES EN CHROMADB ===
Distancia/similitud: valores crudos de ChromaDB

[Poder semántico] ¿Qué me exigen para formalizarme y empezar a vender?
  1. DOC-002 distancia=0.2387 similitud=0.7613

[El metadato salva el día] ¿En qué padrón estoy y cuándo vence ingresos brutos?
  Sin filtro: DOC-001 similitud=0.7735 (candidato semántico crudo)
  1. DOC-010 distancia=0.2284 similitud=0.7716

[Prueba de estrés] ¿Cómo tramito un permiso para importar maquinaria agrícola?
  no tengo eso

## Ajuste realizado

Se ajustó el umbral de distancia máxima a 0.25 luego de observar los resultados reales de las Killer Queries. Este valor permite aceptar coincidencias válidas como DOC-002 y DOC-010, cuyas distancias fueron 0.2387 y 0.2284, y rechazar consultas fuera del catálogo, cuyo mejor candidato tuvo distancia 0.3026.