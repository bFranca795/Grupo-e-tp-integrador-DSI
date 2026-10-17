import json,ast
from pathlib import Path
p=Path(__file__).resolve().parent
rows=json.loads((p/'resultados.json').read_text(encoding='utf-8'))
regression=json.loads((p/'basico_regresion.json').read_text(encoding='utf-8'))
prior=json.loads((p.parent/'comparacion.json').read_text(encoding='utf-8'))
old={r['case']:r for r in prior if r.get('settings',{}).get('variant')=='rerank'}
analysis={
'b1_compuesta': 'Ahora incluye todos los tipos de comprobantes de IVA y conserva el esquema general de vencimientos. Siguen faltando las bajas de empleados, el registro antes de liquidar y las consecuencias del pago tardío. El segundo chunk de DOC-008 obtiene 0.7 pero queda cuarto, fuera del máximo de tres: pérdida en selección posterior al juicio. Antes no se suministraba ningún chunk de DOC-007.',
'factual': 'Ahora incluye los dos chunks de DOC-002 y recupera superficie/consumo del local y tipo de actividad, omitidos por la variante anterior con chunks. El básico completo ya incluía esos requisitos. No se observa omisión de requisitos pedidos en este caso.',
'fuera_dominio': 'Los ocho candidatos obtienen 0.0. No hay seleccionados ni llamada al generador. Mantiene escape como antes, ahora sustentado en la evaluación del juez en lugar del corte de distancia.',
'complacencia': 'Selecciona DOC-009 chunk 000 y refuta la afirmación, con la expresión puede hacer caer el plan. Antes devolvía escape sin fuente. No incluye el detalle adicional sobre la imposibilidad de reactivar un plan caído; esa parte está en chunk 001, puntuado 0.2 y excluido por score, no por distancia. No se preguntó cómo reactivar un plan, por lo que no lo contamos como incumplimiento de esta pregunta.',
'sinonimos': 'Conserva el checklist de cinco tipos de comprobantes y DOC-007 como fuente. No se observa mejora de cobertura respecto de la respuesta anterior a esta consulta.'}
text='''# Primer ajuste: reranking sin umbral de distancia previo

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
'''
for row in rows:
    text+='\n## '+row['case']+'\n\n**Pregunta exacta:** '+row['question']+'\n\n**Respuesta completa:**\n\n'
    text+='\n'.join('> '+line for line in row['answer'].splitlines())+'\n'
    verdict={r['id']:r for r in row['judge']['items']}
    selected={r['id'] for r in row['selected']}
    text+='\n**Ocho candidatos, en orden de recuperación, y juicio completo:**\n\n'
    text+='| ID | Padre | Distancia | Score | Motivo textual | Seleccionado |\n|---|---|---:|---:|---|---|\n'
    for candidate in row['candidates']:
        j=verdict.get(candidate['id'])
        text+=f"| {candidate['id']} | {candidate['metadatos']['parent_id']} | {candidate['distancia']:.10f} | {j['score'] if j else 'sin juicio'} | {j['reason'] if j else 'no devuelto'} | {'sí' if candidate['id'] in selected else 'no'} |\n"
    text+='\n**Seleccionados y fuentes en orden:**\n\n'
    for candidate in row['sources']:
        text+='- '+candidate['id']+' — padre '+candidate['metadatos']['parent_id']+'\n'
    if not row['sources']: text+='Ninguno.\n'
    text+='\n**Cobertura y comparación:** '+analysis[row['case']]+'\n'
    text+='\n**Estado anterior:** '+old[row['case']]['status']+'; fuentes: '+(', '.join(r['id'] for r in old[row['case']]['sources']) or 'ninguna')+'.\n'
text+='''
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
'''
(p/'resultados_para_revision.md').write_text(text,encoding='utf-8')
root=p.parents[2]
old_tree=ast.parse((p/'pipeline_antes.txt').read_text(encoding='utf-8'))
new_tree=ast.parse((root/'entrega_3/rag_pipeline/pipeline.py').read_text(encoding='utf-8'))
class RestoreOnlyDistance(ast.NodeTransformer):
    def visit_keyword(self,node):
        if node.arg=='distancia_maxima' and isinstance(node.value,ast.IfExp):
            node.value=node.value.orelse
        return self.generic_visit(node)
assert ast.dump(old_tree)==ast.dump(RestoreOnlyDistance().visit(new_tree))
(p/'preservacion_basico.json').write_text(json.dumps({
    'pipeline_only_logic_change': 'distancia_maxima=None exclusivamente para rerank',
    'other_pipeline_ast_unchanged': True,
    'basic_answers_identical':all(r['answer_identical_to_previous'] for r in regression),
    'basic_sources_identical':all(r['source_ids_identical_to_previous'] for r in regression),
},ensure_ascii=False,indent=2),encoding='utf-8')
report=root/'entrega_3/informe.md'
with report.open('a',encoding='utf-8') as file:
    file.write('\n\n---\n\n## Revisión posterior: primer ajuste al reranking\n\n')
    file.write('El análisis anterior corresponde al pipeline con corte previo. Se implementó después, por pedido del usuario, un único ajuste: el juez recibe hasta ocho candidatos sin corte duro previo de distancia y evalúa evidencia para alguna parte de la pregunta. El básico se conserva.\n\n')
    file.write('Ejecución real: selecciona DOC-007 y enumera comprobantes en la consulta compuesta; recupera ambos chunks de DOC-002 para requisitos de alta; refuta complacencia con DOC-009 respetando «puede»; fuera de dominio mantiene escape. Persisten omisiones de cargas sociales: DOC-008 chunk 001 recibe 0.7 y queda fuera del máximo de tres. No se declara mejora general ni se implementó el siguiente ajuste.\n\n')
    file.write('Cinco casos avanzados y cinco de regresión, sin errores técnicos; básico con respuestas y fuentes idénticas a las previas. Nueve pruebas locales aprobadas. Evidencias completas y comparación en [reranking_sin_umbral/resultados_para_revision.md](evidencias/reranking_sin_umbral/resultados_para_revision.md).\n')
print('Reporte guardado y preservación del básico comprobada por AST y regresión.')
