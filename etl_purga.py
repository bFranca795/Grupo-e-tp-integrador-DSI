"""Normaliza, vectoriza y purga casi-duplicados de la base de conocimiento."""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSION = 768
DISTANCIA_MAXIMA = 0.20

ALIAS_CLAVES = {
    "descripcion": "descripcion_semantica",
    "texto": "descripcion_semantica",
    "metadata": "metadatos",
}


def normalizar_booleano(valor: object, campo: str) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.strip().lower() in {"true", "false"}:
        return valor.strip().lower() == "true"
    raise ValueError(f"{campo} debe ser booleano, recibido: {valor!r}")


def normalizar_documento(documento: dict) -> dict:
    documento = dict(documento)
    normalizaciones = []
    for clave_vieja, clave_nueva in ALIAS_CLAVES.items():
        if clave_vieja in documento and clave_nueva not in documento:
            documento[clave_nueva] = documento.pop(clave_vieja)
            normalizaciones.append(f"clave {clave_vieja} -> {clave_nueva}")

    if not isinstance(documento.get("metadatos"), dict):
        raise ValueError(f"{documento.get('id', '<sin id>')}: falta metadatos")

    metadatos = dict(documento["metadatos"])
    activo_original = metadatos.get("activo")
    metadatos["activo"] = normalizar_booleano(activo_original, "activo")
    if isinstance(activo_original, str):
        normalizaciones.append(f"activo {activo_original!r} -> {metadatos['activo']!r}")
    if isinstance(metadatos.get("tags_regionales"), str):
        metadatos["tags_regionales"] = [
            tag.strip() for tag in metadatos["tags_regionales"].split(",") if tag.strip()
        ]
    documento["metadatos"] = metadatos

    if not documento.get("id") or not documento.get("descripcion_semantica"):
        raise ValueError(f"Documento incompleto: {documento!r}")
    if normalizaciones:
        documento["_normalizaciones"] = normalizaciones
    return documento


def resolver_ids(documentos: list[dict]) -> list[dict]:
    usados: set[str] = set()
    for documento in documentos:
        id_original = documento["id"]
        id_resuelto = id_original
        sufijo = 1
        while id_resuelto in usados:
            id_resuelto = f"{id_original}-dup-{sufijo}"
            sufijo += 1
        documento["id"] = id_resuelto
        usados.add(id_resuelto)
        if id_resuelto != id_original:
            documento["_colision_id"] = id_original
    return documentos


def generar_embeddings(textos: list[str]) -> np.ndarray:
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY no está configurada en las variables de entorno.")

    cliente = genai.Client()
    respuesta = cliente.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=textos,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=DIMENSION,
        ),
    )
    vectores = np.asarray([embedding.values for embedding in respuesta.embeddings], dtype="float32")
    normas = np.linalg.norm(vectores, axis=1, keepdims=True)
    return vectores / normas


def pares_candidatos(documentos: list[dict], vectores: np.ndarray) -> list[dict]:
    similitudes = vectores @ vectores.T
    pares = []
    for izquierda in range(len(documentos)):
        for derecha in range(izquierda + 1, len(documentos)):
            metadatos_izq = documentos[izquierda]["metadatos"]
            metadatos_der = documentos[derecha]["metadatos"]
            if any(
                metadatos_izq[campo] != metadatos_der[campo]
                for campo in ("categoria", "jurisdiccion", "tipo_contribuyente", "activo")
            ):
                continue
            distancia = 1 - float(similitudes[izquierda, derecha])
            if distancia <= DISTANCIA_MAXIMA:
                pares.append(
                    {
                        "id_izquierda": documentos[izquierda]["id"],
                        "id_derecha": documentos[derecha]["id"],
                        "distancia": distancia,
                        "similitud": float(similitudes[izquierda, derecha]),
                    }
                )
    return pares


def purgar(documentos: list[dict], pares: list[dict]) -> tuple[list[dict], list[dict]]:
    eliminados: set[str] = set()
    for par in pares:
        eliminados.add(par["id_derecha"])
        par["eliminado"] = par["id_derecha"]
        par["conservado"] = par["id_izquierda"]
        par["motivo"] = (
            f"distancia coseno {par['distancia']:.4f} <= {DISTANCIA_MAXIMA:.2f}; "
            "mismos metadatos de alcance y estado"
        )
    limpios = [documento for documento in documentos if documento["id"] not in eliminados]
    return limpios, [par for par in pares if par["eliminado"] in eliminados]


def informar_purga(
    documentos_iniciales: list[dict], documentos_finales: list[dict], pares: list[dict]
) -> None:
    colisiones = [
        documento for documento in documentos_iniciales if "_colision_id" in documento
    ]
    print("\n=== IDs resueltos ===")
    if colisiones:
        for documento in colisiones:
            print(f"{documento['_colision_id']} -> {documento['id']}")
    else:
        print("No hubo colisiones.")

    print("\n=== Eliminaciones ===")
    if pares:
        for par in pares:
            print(
                f"Se elimina {par['eliminado']} y se conserva {par['conservado']}: "
                f"similitud {par['similitud']:.4f} "
                f"(distancia {par['distancia']:.4f} <= {DISTANCIA_MAXIMA:.2f}; "
                "mismos metadatos de alcance y estado)."
            )
    else:
        print("No se detectaron casi-duplicados.")

    print("\n=== Inconsistencias estructurales normalizadas ===")
    inconsistencias = [
        documento for documento in documentos_iniciales if "_normalizaciones" in documento
    ]
    if inconsistencias:
        for documento in inconsistencias:
            print(f"{documento['id']}: " + "; ".join(documento["_normalizaciones"]))
    else:
        print("No se detectaron inconsistencias.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, default=Path("base_conocimiento.json"))
    parser.add_argument("--salida", type=Path, default=Path("base_conocimiento_limpia.json"))
    argumentos = parser.parse_args()
    load_dotenv()

    documentos = json.loads(argumentos.entrada.read_text(encoding="utf-8"))
    documentos = resolver_ids([normalizar_documento(documento) for documento in documentos])
    vectores = generar_embeddings([documento["descripcion_semantica"] for documento in documentos])
    pares = pares_candidatos(documentos, vectores)
    documentos_limpios, eliminaciones = purgar(documentos, pares)

    argumentos.salida.write_text(
        json.dumps(
            [
                {
                    clave: valor
                    for clave, valor in documento.items()
                    if clave not in {"_colision_id", "_normalizaciones"}
                }
                for documento in documentos_limpios
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    informar_purga(documentos, documentos_limpios, eliminaciones)

    print(f"Entrada: {len(documentos)} documentos")
    print(f"Salida: {len(documentos_limpios)} documentos")
    for eliminacion in eliminaciones:
        print(
            f"Eliminado {eliminacion['eliminado']} por casi-duplicar a "
            f"{eliminacion['conservado']} (distancia={eliminacion['distancia']:.4f})"
        )
    print(f"Generado: {argumentos.salida}")


if __name__ == "__main__":
    main()