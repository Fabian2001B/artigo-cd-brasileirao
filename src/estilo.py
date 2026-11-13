"""Estilo visual compartilhado pelas figuras do artigo."""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRADE = "#e4e3df"
BORDA = "#8a8984"


def aplicar_estilo():
    """Fonte, cores de texto e grade discretas para todas as figuras."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.edgecolor": GRADE, "axes.labelcolor": TINTA_2,
        "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
        "axes.axisbelow": True,
    })


def saida_utf8():
    """Evita erro de acentuação ao imprimir no terminal do Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
