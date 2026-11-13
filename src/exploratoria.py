"""Etapa 3: análise exploratória.

Gera tabelas de taxa de vitória por fator (campeões x vices) e as figuras
fig1 (por faixa de posição do adversário) e fig2 (por condição de jogo).
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import BASE_PROCESSADA, COR_CAMPEAO, COR_VICE, FIGURAS, TABELAS

TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRADE = "#e4e3df"


def estilo():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.edgecolor": GRADE, "axes.labelcolor": TINTA_2,
        "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "figure.dpi": 150,
    })


def barras_agrupadas(ax, rotulos, campeao, vice, n_c, n_v):
    x = np.arange(len(rotulos))
    w = 0.38
    for desloc, vals, ns, cor, nome in [(-w / 2, campeao, n_c, COR_CAMPEAO, "Campeões"),
                                         (w / 2, vice, n_v, COR_VICE, "Vice-campeões")]:
        barras = ax.bar(x + desloc, vals, w - 0.03, color=cor, label=nome)
        for b, v, n in zip(barras, vals, ns):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}%",
                    ha="center", va="bottom", fontsize=7.5, color=TINTA)
    ax.set_xticks(x, rotulos)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Taxa de vitória (%)")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper right", fontsize=8)


def taxa(df, col):
    g = df.groupby([col, "papel"], observed=True)["vitoria"].agg(["mean", "size"]).reset_index()
    g["mean"] = 100 * g["mean"]
    return g


def main():
    estilo()
    df = pd.read_csv(BASE_PROCESSADA, encoding="utf-8")
    FIGURAS.mkdir(parents=True, exist_ok=True)

    # Tabela resumo por campanha.
    camp = (df.groupby(["temporada", "papel", "time"])
              .agg(jogos=("pontos", "size"), pontos=("pontos", "sum"),
                   vitorias=("vitoria", "sum"),
                   pts_casa=("pontos", lambda s: s[df.loc[s.index, "mandante"] == 1].sum()),
                   pts_fora=("pontos", lambda s: s[df.loc[s.index, "mandante"] == 0].sum()))
              .reset_index())
    camp.to_csv(TABELAS / "resumo_campanhas.csv", index=False, encoding="utf-8")

    # Pontos perdidos por faixa de adversário (campeão x vice).
    df["pontos_perdidos"] = 3 - df["pontos"]
    perd = (df.groupby(["faixa_adv", "papel"], observed=True)["pontos_perdidos"]
              .agg(["sum", "mean", "size"]).reset_index())
    perd.to_csv(TABELAS / "pontos_perdidos_por_faixa.csv", index=False, encoding="utf-8")

    # Taxa de vitória por fator binário.
    fatores = {
        "mandante": ("Mandante", "Visitante"),
        "adv_z4": ("Adversário no Z4", "Adversário fora do Z4"),
        "meio_semana": ("Meio de semana", "Fim de semana"),
        "reta_final": ("Reta final (30ª-38ª)", "Rodadas 1-29"),
    }
    linhas = []
    for col, (sim, nao) in fatores.items():
        for val, nome in [(1, sim), (0, nao)]:
            sub = df[df[col] == val]
            for papel in ["Campeão", "Vice"]:
                s = sub[sub["papel"] == papel]
                linhas.append({"fator": col, "condicao": nome, "papel": papel,
                               "jogos": len(s), "taxa_vitoria": 100 * s["vitoria"].mean(),
                               "pts_por_jogo": s["pontos"].mean()})
            linhas.append({"fator": col, "condicao": nome, "papel": "Todos",
                           "jogos": len(sub), "taxa_vitoria": 100 * sub["vitoria"].mean(),
                           "pts_por_jogo": sub["pontos"].mean()})
    tab = pd.DataFrame(linhas)
    tab.to_csv(TABELAS / "taxa_vitoria_por_fator.csv", index=False, encoding="utf-8")

    # Figura 1: taxa de vitória por faixa de posição final do adversário.
    t = taxa(df, "faixa_adv")
    ordem = ["1º-4º", "5º-8º", "9º-12º", "13º-16º", "17º-20º"]
    c = t[t.papel == "Campeão"].set_index("faixa_adv").reindex(ordem)
    v = t[t.papel == "Vice"].set_index("faixa_adv").reindex(ordem)
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    barras_agrupadas(ax, ordem, c["mean"], v["mean"], c["size"], v["size"])
    ax.set_xlabel("Posição final do adversário na tabela")
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig1_vitoria_por_adversario.png", dpi=300)
    fig.savefig(FIGURAS / "fig1_vitoria_por_adversario.pdf")
    plt.close(fig)

    # Figura 2: taxa de vitória por condição de jogo.
    rot, cv, vv, nc, nv = [], [], [], [], []
    for col, (sim, nao) in [("mandante", ("Mandante", "Visitante")),
                            ("meio_semana", ("Meio de\nsemana", "Fim de\nsemana")),
                            ("reta_final", ("Reta\nfinal", "Rodadas\n1-29"))]:
        for val, nome in [(1, sim), (0, nao)]:
            s = df[df[col] == val]
            rot.append(nome)
            cv.append(100 * s[s.papel == "Campeão"]["vitoria"].mean())
            vv.append(100 * s[s.papel == "Vice"]["vitoria"].mean())
            nc.append((s.papel == "Campeão").sum())
            nv.append((s.papel == "Vice").sum())
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    barras_agrupadas(ax, rot, cv, vv, nc, nv)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig2_vitoria_por_condicao.png", dpi=300)
    fig.savefig(FIGURAS / "fig2_vitoria_por_condicao.pdf")
    plt.close(fig)

    print(camp.to_string(index=False))
    print(perd.to_string(index=False))
    print(tab[tab.papel != "Todos"].round(1).to_string(index=False))
    print(tab[tab.papel == "Todos"].round(1).to_string(index=False))
    print("[ok] figuras e tabelas exploratórias")


if __name__ == "__main__":
    main()
