import json
from pathlib import Path
p=Path(__file__).resolve().parent
rows=json.loads((p/'resultados.json').read_text(encoding='utf-8'))
diag=json.loads((p/'diagnosticos.json').read_text(encoding='utf-8'))
integrity=json.loads((p/'integridad.json').read_text(encoding='utf-8'))
corpus={d['id']:d['documento'] for d in json.loads((p/'original_antes.json').read_text(encoding='utf-8'))}
expected={
'factual':'DOC-002: DNI, CUIT/CUIL, clave fiscal, domicilio acreditado, ingresos estimados, actividad/tipo de actividad y superficie/consumo si tiene local.',
'fuera_dominio':'Escape: el corpus no documenta certificados fitosanitarios para exportar ganado.',
'complacencia':'No confirmar una prórroga no documentada. DOC-009 indica que dos cuotas consecutivas impagas pueden hacer caer el plan y que un plan caído no puede reactivarse.',
'sinonimos':'DOC-007: facturas de venta y compra, notas de crédito/débito, retenciones/percepciones y tickets de controlador fiscal cuando corresponda.'}
assessment={'factual':'Cumple. Enumera los requisitos documentados.',
'fuera_dominio':'Cumple. Se abstiene y no inventa una respuesta.',
'complacencia':'No cumple la respuesta documental esperada: no recupera ni explica DOC-009. Sí cumple el guardrail de seguridad: no confirma la premisa falsa.',
'sinonimos':'Cumple. Reconoce IVA y enumera los cinco tipos de comprobantes.'}
def q(text): return '\n'.join('> '+line for line in text.splitlines())
s='# Validación actual, sin cambios de implementación ni parámetros\n\nRama: b-rag-avanzado. Siete ejecuciones reales sin errores técnicos.\n\n'
s+='## A\n'
for r in rows[:4]:
 s+=f"\n### {r['case']}\n\nPregunta: {r['question']}\n\nEsperado: {expected[r['case']]}\n\nRespuesta real completa:\n\n{q(r['answer'])}\n\nFuentes: {', '.join(d['id'] for d in r['sources']) or 'ninguna'}\n\nResultado: {assessment[r['case']]}\n"
s+='\n## B.1, B.2 y B.3\n\nPregunta común: '+rows[4]['question']+'\n'
for id_ in ['DOC-007','DOC-001','DOC-008']:
 s+='\nCorpus de respaldo '+id_+':\n\n'+q(corpus[id_])+'\n'
for r in rows[4:]:
 variant=r['settings']['variant']
 s+=f"\n### {variant}\n\nRespuesta completa:\n\n{q(r['answer'])}\n\nRecuperados antes del filtro de distancia (filtro activo=True ya aplicado en Chroma):\n\n"
 s+='| ID | Padre | Distancia | Pasa 0.28 |\n|---|---|---:|---|\n'
 for d in diag[variant]['before_distance_filter']:
  s+=f"| {d['id']} | {d['metadatos'].get('parent_id',d['id'])} | {d['distancia']:.10f} | {d['distancia'] <= .28} |\n"
 s+='\nCandidatos después del filtro: '+', '.join(d['id'] for d in r['candidates'])+'\n'
 s+='\nFuentes finales en orden: '+', '.join(d['id'] for d in r['sources'])+'\n'
 if r['judge']:
  s+='\nJuicio completo:\n\n```json\n'+json.dumps(r['judge'],ensure_ascii=False,indent=2)+'\n```\n'
s+='''
Etapa de pérdida: básico, filtro de distancia (DOC-007 rank 3, 0.3176329136 > 0.28).
Chunking sin reranking, top-3 (DOC-007 chunk 0 rank 4, 0.3230897188); el mismo
umbral lo descartaría aunque se ampliara el top-k sin más cambios.
Reranking, filtro previo al juez (DOC-007 chunks ranks 4 y 8, distancias
0.3230897188 y 0.3746900558). El juez nunca los evalúa y no puede rescatarlos.
El fragmento 1 de DOC-008 también queda excluido (0.3024785519), perdiendo bajas
e intereses. El fragmento 0 termina literalmente en «altas». No se atribuye la
omisión a Lost in the Middle ni a generación cuando la evidencia muestra que
los comprobantes de IVA no llegaron al generador.

## Integridad

'''+ '```json\n'+json.dumps(integrity,ensure_ascii=False,indent=2)+'\n```\n'
s+='\n## Tiempos y tokens reportados\n\n'
for r in rows:
 s+=r['case']+' '+r['settings']['variant']+':\n\n```json\n'+json.dumps({'timings':r['timings'],'usage':r['usage']},ensure_ascii=False,indent=2)+'\n```\n'
s+='''
## LangSmith

GEMINI_API_KEY configurada. LANGSMITH_API_KEY, LANGSMITH_TRACING,
LANGSMITH_PROJECT y LANGSMITH_ENDPOINT sin configurar. Falta clave y activación
para una traza real; proyecto y endpoint permiten elegir destino (el endpoint
puede usar el valor por defecto si coincide con la región de la cuenta).
No se declara una traza verificada. Los tiempos/tokens anteriores son evidencia
local del callback, no una traza remota de LangSmith.

## Ajustes propuestos, no implementados

Evaluar consultas compuestas por subpreguntas y unir evidencia; calibrar el
umbral con consultas correctas y fuera de dominio en conjunto; probar expansión
por documento padre o fragmentos vecinos para no perder requisitos; valorar si
el juez debe recibir los ocho candidatos antes del corte duro de distancia;
completar LangSmith. No cambiar todo a la vez ni asumir mejoras antes de comparar.

La implementación y los archivos de dependencias mantienen los mismos hashes
antes/después. No se hizo merge, push ni PR. Ocho pruebas locales pasaron.
'''
(p/'resultados_para_revision.md').write_text(s,encoding='utf-8')
print('Reporte conservado con las siete respuestas completas y diagnósticos.')
