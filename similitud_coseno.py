"""A.2 — Similitud coseno a mano, validada con NumPy.

Correr con: uv run similitud_coseno.py
"""

import math

import numpy as np

# Eje X: carga de vencimiento. Eje Y: carga de documentacion / tramite.
DOCUMENTOS = [
    ("DOC 1 — Vencimiento IVA", (0.9, 0.2)),
    ("DOC 2 — Documentacion Monotributo", (0.2, 0.9)),
    ("DOC 3 — Estado de un tramite", (0.5, 0.7)),
]

CONSULTA = (1.0, 0.1)  # "¿Cuando vence el IVA?"


def similitud_coseno_manual(a, b):
    """Los tres pasos sin NumPy: A . B, ||A||, ||B||, division."""
    punto = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x**2 for x in a))
    norma_b = math.sqrt(sum(y**2 for y in b))
    return punto / (norma_a * norma_b)


def similitud_coseno(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


manuales = [similitud_coseno_manual(v, CONSULTA) for _, v in DOCUMENTOS]
numpys = [similitud_coseno(np.array(v), np.array(CONSULTA)) for _, v in DOCUMENTOS]

print(f"{'Documento':<34} {'manual':>9} {'numpy':>9}")
for (nombre, _), manual, con_numpy in zip(DOCUMENTOS, manuales, numpys):
    print(f"{nombre:<34} {manual:>9.6f} {con_numpy:>9.6f}")

assert np.allclose(manuales, numpys, atol=1e-12)
print("\nManual y NumPy coinciden (np.allclose, atol=1e-12).")
