from .rag_pipeline.retriever import get_retriever


CONSULTAS_DEMO = [
    {
        "titulo": "Consulta 1: Vencimiento de Obligaciones Fiscales",
        "query": "¿Cuándo vence la presentación y pago de la declaración jurada de IVA este mes?",
    },
    {
        "titulo": "Consulta 2: Documentación Requerida para Trámite",
        "query": "¿Qué papeles y requisitos necesito presentar para darme de alta en el Monotributo?",
    },
]


def imprimir_fundamentacion(documentos: list[dict]) -> None:
    if not documentos:
        print("  [AVISO] No se recuperaron documentos para fundamentar la respuesta.")
        return

    for i, doc in enumerate(documentos, start=1):
        print(f"\n  [Documento {i}] ID: {doc['id']}")
        print(f"  * Similitud: {doc['similitud']:.4f} | Distancia: {doc['distancia']:.4f}")
        print("  * Metadatos:")
        for clave, valor in doc.get("metadatos", {}).items():
            print(f"      - {clave}: {valor}")
        print("  * Fragmento de texto normativo utilizado como fundamento:")
        print(f"      \"{doc['documento']}\"")


def main() -> None:
    print("=== DEMOSTRACIÓN DE FUNDAMENTACIÓN Y EXPOSICIÓN DE FUENTES ===")
    retriever = get_retriever()
    print(f"Base ChromaDB conectada ({retriever.coleccion.count()} documentos cargados).\n")

    for caso in CONSULTAS_DEMO:
        print("=" * 80)
        print(f"{caso['titulo']}")
        print(f"Consulta del cliente: \"{caso['query']}\"")
        print("=" * 80)

        # Recuperamos el documento con mayor relevancia semántica
        documentos = retriever.recuperar(caso["query"], n_resultados=1)

        print("\nDocumentos expuestos como fundamento (texto y metadatos):")
        imprimir_fundamentacion(documentos)
        print("\n")


if __name__ == "__main__":
    main()
