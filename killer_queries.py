from vector_db import buscar_contable


KILLER_QUERIES = [
    # Resultado esperado: DOC-002.
    (
        "Poder semántico",
        "¿Qué me exigen para formalizarme y empezar a vender?",
        None,
    ),
    # Sin filtro puede aparecer una jurisdiccion incorrecta; con jurisdiccion=caba
    # el resultado esperado es DOC-010.
    (
        "El metadato salva el día",
        "¿En qué padrón estoy y cuándo vence ingresos brutos?",
        {"jurisdiccion": "caba"},
    ),
    # Resultado esperado:"no tengo eso"
    (
        "Prueba de estrés",
        "¿Cómo tramito un permiso para importar maquinaria agrícola?",
        None,
    ),
]


def imprimir_resultados(resultados: dict) -> None:
    ids = resultados.get("ids", [[]])[0]
    distancias = resultados.get("distances", [[]])[0]
    if not ids:
        print("  no tengo eso")
        return
    for posicion, (id_documento, distancia) in enumerate(
        zip(ids, distancias), start=1
    ):
        print(
            f"  {posicion}. {id_documento} "
            f"distancia={distancia:.4f} "
            f"similitud={1 - distancia:.4f}"
        )


def main() -> None:
    print(
        "=== KILLER QUERIES EN CHROMADB ===\n"
        "Distancia/similitud: valores crudos de ChromaDB"
    )
    for nombre, consulta, filtros in KILLER_QUERIES:
        print(f"\n[{nombre}] {consulta}")
        if filtros:
            crudo = buscar_contable(
                consulta,
                solo_activos=True,
                n_resultados=1,
            )
            ids_crudos = crudo.get("ids", [[]])[0]
            distancias_crudas = crudo.get("distances", [[]])[0]
            if ids_crudos:
                print(
                    f"  Sin filtro: {ids_crudos[0]} "
                    f"similitud={1 - distancias_crudas[0]:.4f} "
                    "(candidato semántico crudo)"
                )
        resultados = buscar_contable(
            consulta,
            solo_activos=True,
            n_resultados=1,
            filtros=filtros,
        )
        imprimir_resultados(resultados)


if __name__ == "__main__":
    main()