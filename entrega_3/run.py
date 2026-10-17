"""Entrada ejecutable desde cualquier directorio, sin depender del cwd."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entrega_3.rag_pipeline.__main__ import main

if __name__ == "__main__":
    main()
