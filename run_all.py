"""Executa todo o pipeline: obtenção, preparação, exploração e modelagem."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import exploratoria  # noqa: E402
import modelagem  # noqa: E402
import obter_dados  # noqa: E402
import preparar  # noqa: E402

if __name__ == "__main__":
    for etapa in (obter_dados, preparar, exploratoria, modelagem):
        print(f"\n===== {etapa.__name__} =====")
        etapa.main()
