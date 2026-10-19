"""python -m entrega_3.rag_pipeline --help"""
import argparse
import json
from pathlib import Path
import time
from datetime import datetime, timezone

from .config import PROJECT_ROOT
from .indexing import rebuild
from .pipeline import Settings, UsageRecorder, build_pipeline

CASES = [
    ("factual", "¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?"),
    ("fuera_dominio", "¿Qué certificado fitosanitario necesito para exportar ganado?"),
    ("complacencia", "Confirmame que mi plan de pagos tiene prórroga automática y no caduca aunque deje dos cuotas impagas."),
    ("sinonimos", "¿Qué tengo que arrimarles para liquidar el gravamen al valor agregado?"),
    ("fuentes_iva", "¿Cuándo vence la presentación y pago de la declaración jurada de IVA este mes?"),
    ("b1_compuesta", "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?"),
    ("b1_tramite", "Mi CUIT es 20-30456789-9: ¿ya presentaron mi declaración de IVA y pagaron el saldo?"),
    ("b1_multi", "¿Qué pide el estudio para el alta de monotributo, la declaración anual de Ganancias y los certificados o constancias?"),
]


def run(question, variant, args):
    settings = Settings(variant=variant, candidate_k=args.candidates, selected_k=args.selected,
                        max_distance=args.max_distance, min_judge_score=args.min_score)
    usage = UsageRecorder()
    started = time.perf_counter()
    result = build_pipeline(settings).invoke({"question": question, "filters": json.loads(args.filters)},
        config={"callbacks": [usage], "metadata": {"variant": variant}, "tags": ["entrega_3"]})
    return {**result, "usage": usage.calls, "total_seconds": time.perf_counter() - started,
            "executed_at_utc": datetime.now(timezone.utc).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["index", "ask", "compare"])
    parser.add_argument("--question")
    parser.add_argument("--variant", choices=["basic", "chunks", "rerank"], default="basic")
    parser.add_argument("--filters", default="{}", help='Filtros exactos JSON, por ejemplo {"jurisdiccion":"caba"}')
    parser.add_argument("--candidates", type=int, default=8)
    parser.add_argument("--selected", type=int, default=None,
                        help="Máximo seleccionado: por defecto 4 en rerank; configurable de 1 a 4")
    parser.add_argument("--max-distance", type=float, default=0.28)
    parser.add_argument("--min-score", type=float, default=0.5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", action="append", help="Ejecutar solo estos IDs del conjunto de comparación")
    args = parser.parse_args()
    if args.command == "index":
        result = rebuild()
    elif args.command == "ask":
        if not args.question:
            parser.error("ask requiere --question")
        result = run(args.question, args.variant, args)
    else:
        result = []
        for case, question in CASES:
            if args.case and case not in args.case:
                continue
            for variant in ("basic", "chunks", "rerank"):
                try:
                    row = {"case": case, **run(question, variant, args)}
                except Exception as error:
                    row = {"case": case, "question": question, "variant": variant,
                           "status": "execution_error", "error_type": type(error).__name__,
                           "provider_code": getattr(error, "code", None)}
                result.append(row)
                if args.output:
                    save(args.output, result)
    if args.output:
        save(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Las trazas se envían antes de salir del proceso.
    from langchain_core.tracers.langchain import wait_for_all_tracers
    wait_for_all_tracers()


def save(path, result):
    path = path if path.is_absolute() else PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
