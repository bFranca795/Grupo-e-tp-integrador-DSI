import json
from pathlib import Path
p=Path(__file__).resolve().parent
rows=json.loads((p/'resultados.json').read_text(encoding='utf-8'))
previous={r['case']:r for r in json.loads((p.parent/'reranking_sin_umbral/resultados.json').read_text(encoding='utf-8'))}
regression=json.loads((p/'basico_regresion.json').read_text(encoding='utf-8'))
coverage={
'comprobantes_iva':True,'presentacion_y_pago_iva':True,'aportes_y_contribuciones':True,
'altas_y_bajas_antes_de_liquidar':True,'intereses_por_pago_tardio':True,'bloqueo_certificado_por_pago_tardio':True}
text='''# Segundo ajuste: máximo configurable de cuatro chunks

Único cambio en pipeline.py: admitir selected_k hasta 4 en vez de hasta 3.
El predeterminado 3 se conserva para no alterar configuración existente; esta
nueva ejecución usa explícitamente selected_k=4 / --selected 4. No se cambian
los ocho candidatos, ausencia de corte previo de distancia en reranking,
score mínimo 0.5, prompt del juez/generador, filtros, guardrails, ni chunking 500/100.
No se fuerza ningún ID ni se seleccionan documentos por una regla especial.

Diez pruebas locales aprobadas, incluyendo selección de cero, dos y hasta cuatro
por relevancia. Cinco ejecuciones avanzadas y cinco de regresión básica, sin
errores técnicos. Respuestas y fuentes del básico idénticas a las anteriores.
Las dos colecciones conservan los mismos hashes de textos y metadatos.
'''
for row in rows:
    text+='\n## '+row['case']+'\n\n**Pregunta completa:** '+row['question']+'\n\n**Respuesta real completa:**\n\n'
    text+='\n'.join('> '+line for line in row['answer'].splitlines())+'\n'
    judgments={r['id']:r for r in row['judge']['items']}
    text+='\n**Seleccionados y fuentes finales, en orden:**\n\n| Orden | ID | Padre | Score | Motivo |\n|---|---|---|---:|---|\n'
    for i,d in enumerate(row['selected'],1):
        j=judgments[d['id']]
        text+=f"| {i} | {d['id']} | {d['metadatos']['parent_id']} | {j['score']} | {j['reason']} |\n"
    if not row['selected']:text+='\nNinguno: escape sin llamada al generador.\n'
    text+='\n**Tiempos y uso anterior/actual:**\n\n```json\n'+json.dumps({
        'before':{'timings':previous[row['case']]['timings'],'total_seconds':previous[row['case']]['total_seconds'],'usage':previous[row['case']]['usage']},
        'after':{'timings':row['timings'],'total_seconds':row['total_seconds'],'usage':row['usage']},
    },ensure_ascii=False,indent=2)+'\n```\n'
text+='''
## Cobertura de la consulta compuesta

Ahora selecciona DOC-008/000 (1.0), DOC-001/000 (1.0), DOC-007/000 (0.9)
y DOC-008/001 (0.7). Incluye comprobantes de IVA, presentación y pago, aportes y
contribuciones, altas y bajas antes de liquidar, intereses y bloqueo del
certificado por pago tardío. No se observa omisión de los puntos solicitados
para esta comprobación; no se afirma reproducir todo el contenido del corpus.

Factual selecciona dos chunks de DOC-002; fuera de dominio cero; complacencia
uno de DOC-009 y conserva la expresión «puede hacer caer»; sinónimos uno de
DOC-007. No se seleccionan cuatro por obligación. Las otras cuatro respuestas
son idénticas a las del ajuste anterior de reranking.

## Diferenciación de variantes y evidencia histórica

| Variante/etapa | Evidencia | Resultado para consulta compuesta |
|---|---|---|
| Básico: documentos completos, top-3 y distancia 0.28 | Regresión básica nueva y validacion_actual | Omite comprobantes de IVA; conserva más detalle de cargas sociales |
| Chunking sin reranking: 500/100, top-3 y distancia 0.28 | Evidencia histórica validacion_actual; no se reejecutó esta variante en esta tanda | Omite comprobantes y parte de cargas sociales |
| Reranking original: ocho recuperados, corte previo 0.28, máximo tres | Evidencia histórica validacion_actual | DOC-007 se descarta antes del juez |
| Primer ajuste: ocho sin corte previo, máximo tres | reranking_sin_umbral | Recupera comprobantes; DOC-008/001 puntúa 0.7 pero queda cuarto |
| Segundo ajuste: ocho sin corte previo, máximo cuatro | Esta tanda, --selected 4 | Incluye los seis puntos de cobertura pedidos |

Los tokens del juez son iguales a la tanda anterior en estos cinco casos.
En la consulta compuesta el generador pasa de 984 a 1099 tokens totales
(entrada 618 -> 727; salida 366 -> 372). Las otras cuatro llamadas/abstenciones
mantienen sus consumos reportados. No se incluyen tokens de embeddings.
Los tiempos varían en ambas direcciones, incluso en casos con respuesta y
selección idénticas: una sola corrida no permite atribuir latencia exclusivamente
al cambio ni extraer conclusiones de rendimiento general.

## LangSmith y límites

LANGSMITH_API_KEY, LANGSMITH_PROJECT y LANGSMITH_ENDPOINT sin configurar;
LANGSMITH_TRACING no habilitado. Sigue pendiente una captura o enlace de traza
real. Los registros locales de tiempos y tokens no sustituyen esa evidencia.
No se declara mejora general ni se implementa Parte C ni métricas RAGAS.
No se propone otro cambio para resolver estos seis puntos porque ahora están
cubiertos en esta corrida; falta ampliar el conjunto de evaluación antes de
generalizar. No se modificaron evidencias anteriores. No hubo merge, push ni PR.
'''
(p/'resultados_para_revision.md').write_text(text,encoding='utf-8')
(p/'cobertura_y_regresion.json').write_text(json.dumps({
    'composite_coverage_manual_review':coverage,
    'basic_answers_identical':all(r['answer_identical_to_previous'] for r in regression),
    'basic_sources_identical':all(r['source_ids_identical_to_previous'] for r in regression),
    'other_rerank_answers_identical':{r['case']:r['answer']==previous[r['case']]['answer'] for r in rows if r['case']!='b1_compuesta'},
    'local_tests_passed':10,'default_selected_k_unchanged':3,'explicit_selected_k_for_this_run':4,
},ensure_ascii=False,indent=2),encoding='utf-8')
root=p.parents[2]
with (root/'entrega_3/informe.md').open('a',encoding='utf-8') as out:
    out.write('\n\n---\n\n## Segundo ajuste: máximo configurable de cuatro seleccionados\n\n')
    out.write('Se amplió únicamente el límite permitido de selected_k de 3 a 4. La tanda nueva usa `--selected 4`; el predeterminado 3 se conserva. Siguen ocho candidatos sin filtro previo por distancia, score mínimo 0.5, misma relevancia parcial, chunking, prompts y guardrails.\n\n')
    out.write('Resultado real: la consulta compuesta selecciona DOC-008/000, DOC-001/000, DOC-007/000 y DOC-008/001 y cubre comprobantes, presentación/pago, aportes/contribuciones, altas/bajas antes de liquidar e intereses/bloqueo del certificado por pago tardío. Factual selecciona dos, sinónimos y complacencia uno, fuera de dominio ninguno. Se conserva «puede hacer caer». No se obliga a llenar el cupo.\n\n')
    out.write('Diez pruebas locales y diez ejecuciones reales (cinco avanzadas y cinco de regresión básica), sin errores técnicos. El básico conserva respuestas y fuentes idénticas; colecciones sin cambios. Solo se observa aumento de tokens del generador en la compuesta (984 a 1099); latencias variables no permiten atribuir causalidad con una corrida. No se declara mejora general ni resultados RAGAS. LangSmith sigue pendiente por falta de configuración y traza real.\n\n')
    out.write('Reporte con respuestas completas, fuentes, cobertura, comparación de básico/chunking/ajustes de reranking y tiempos/tokens: [reranking_hasta_cuatro/resultados_para_revision.md](evidencias/reranking_hasta_cuatro/resultados_para_revision.md).\n')
print('Reporte e informe actualizados con resultados reales.')
