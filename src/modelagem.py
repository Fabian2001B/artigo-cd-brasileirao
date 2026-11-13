"""Etapa 4: modelagem com árvores de decisão e comparação com outros modelos.

Saídas: outputs/tables/metricas_modelos.csv, importancia_variaveis.csv,
regras_arvore.txt, matriz_confusao_temporal.csv e as figuras fig3 (árvore)
e fig4 (importância das variáveis).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import (GridSearchCV, RepeatedStratifiedKFold,
                                     StratifiedKFold, cross_validate)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from sklearn.base import clone

from config import (BASE_PROCESSADA, CENARIOS_ROBUSTEZ, COR_CAMPEAO, FIGURAS,
                    PREDITORAS, SEMENTE, TABELAS)
from estilo import BORDA, TINTA, TINTA_2, aplicar_estilo, saida_utf8

NOMES = {
    "mandante": "Mandante", "posicao_adv": "Posição do adversário",
    "forma_recente": "Forma recente", "dif_idade": "Dif. de idade",
    "dif_altura": "Dif. de altura", "rodada": "Rodada",
    "meio_semana": "Meio de semana", "hora": "Horário", "campeao": "É o campeão",
}
GRADE_ARVORE = {"max_depth": [2, 3, 4, 5], "min_samples_leaf": [10, 20, 30, 40]}
BINARIAS = {"mandante", "meio_semana", "campeao"}


def num_br(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def nova_floresta():
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=10,
                                  class_weight="balanced", random_state=SEMENTE)


def desenhar_arvore(arvore, X, y, destino):
    """Desenha a árvore em português, com a taxa real de vitória de cada nó."""
    t = arvore.tree_
    caminho = arvore.decision_path(X).toarray().astype(bool)
    n_total = len(X)
    pos, folhas = {}, [0]

    def layout(no, prof):
        if t.children_left[no] == -1:
            pos[no] = (folhas[0], prof)
            folhas[0] += 1
            return
        layout(t.children_left[no], prof + 1)
        layout(t.children_right[no], prof + 1)
        pos[no] = ((pos[t.children_left[no]][0] + pos[t.children_right[no]][0]) / 2, prof)

    layout(0, 0)
    prof_max = max(p for _, p in pos.values())
    fig, ax = plt.subplots(figsize=(6.4, 1.15 + 1.25 * prof_max))
    ax.axis("off")
    ax.grid(False)
    escala_x = 1.0 / max(folhas[0] - 1, 1)

    def xy(no):
        x, p = pos[no]
        return x * escala_x, -p

    for no in pos:
        x, yy = xy(no)
        mask = caminho[:, no]
        n, taxa = mask.sum(), 100 * y[mask].mean()
        folha = t.children_left[no] == -1
        if folha:
            texto = f"Vitória em {taxa:.0f}%\n{n} jogos ({num_br(100 * n / n_total)}%)"
            # Destaque azul = folha em que o modelo prevê vitória.
            cor = "#dbe8f8" if t.value[no][0].argmax() == 1 else "#f4f3f0"
        else:
            var = PREDITORAS[t.feature[no]]
            if var in BINARIAS:
                cond = f"{NOMES[var]}?"
            else:
                cond = f"{NOMES[var]} ≤ {num_br(t.threshold[no])}?"
            texto = f"{cond}\n{n} jogos, vitória em {taxa:.0f}%"
            cor = "white"
        ax.text(x, yy, texto, ha="center", va="center", fontsize=7.5, color=TINTA,
                bbox=dict(boxstyle="round,pad=0.45", fc=cor, ec=BORDA, lw=0.8))
        if not folha:
            var = PREDITORAS[t.feature[no]]
            esq, dir_ = ("não", "sim") if var in BINARIAS else ("sim", "não")
            for filho, rot in [(t.children_left[no], esq), (t.children_right[no], dir_)]:
                fx, fy = xy(filho)
                ax.annotate("", xy=(fx, fy + 0.28), xytext=(x, yy - 0.28),
                            arrowprops=dict(arrowstyle="-", color=BORDA, lw=0.8))
                ax.text((x + fx) / 2, (yy + fy) / 2, rot, ha="center", va="center",
                        fontsize=7, color=TINTA_2,
                        bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
    ax.set_xlim(-0.14, 1.14)
    ax.set_ylim(-prof_max - 0.45, 0.45)
    fig.tight_layout()
    fig.savefig(f"{destino}.png", dpi=300)
    fig.savefig(f"{destino}.pdf")
    plt.close(fig)


def avaliar_cv(modelo, X, y, cv):
    r = cross_validate(modelo, X, y, cv=cv,
                       scoring={"acc": "accuracy", "bal": "balanced_accuracy"})
    return r["test_acc"].mean(), r["test_acc"].std(), r["test_bal"].mean()


def ajustar_arvore(X, y, cv):
    busca = GridSearchCV(DecisionTreeClassifier(random_state=SEMENTE, class_weight="balanced"),
                         GRADE_ARVORE, cv=cv, scoring="balanced_accuracy")
    busca.fit(X, y)
    return busca.best_estimator_, busca.best_params_


def main():
    aplicar_estilo()
    df = pd.read_csv(BASE_PROCESSADA, encoding="utf-8")
    X, y = df[PREDITORAS], df["vitoria"]
    y3 = df["resultado"]
    cv_rep = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEMENTE)
    cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    treino = df["temporada"] <= 2023

    arvore, params = ajustar_arvore(X, y, cv5)
    modelos = {
        "Linha de base (classe mais comum)": DummyClassifier(strategy="most_frequent"),
        f"Árvore de decisão (prof. {params['max_depth']}, folha {params['min_samples_leaf']})": arvore,
        "Regressão logística": make_pipeline(StandardScaler(), LogisticRegression(
            class_weight="balanced", max_iter=1000)),
        "Floresta aleatória (300 árvores)": nova_floresta(),
    }

    linhas = []
    for nome, m in modelos.items():
        acc, dp, bal = avaliar_cv(m, X, y, cv_rep)
        # Teste temporal: hiperparâmetros da árvore escolhidos só com o treino.
        if nome.startswith("Árvore"):
            m_t, _ = ajustar_arvore(X[treino], y[treino], cv5)
        else:
            m_t = m.fit(X[treino], y[treino])
        pred = m_t.predict(X[~treino])
        linhas.append({"modelo": nome, "acuracia_cv": acc, "dp_cv": dp,
                       "acuracia_balanceada_cv": bal,
                       "acuracia_temporal": accuracy_score(y[~treino], pred),
                       "acuracia_balanceada_temporal": balanced_accuracy_score(y[~treino], pred)})
        if nome.startswith("Árvore"):
            cm = confusion_matrix(y[~treino], pred, labels=[1, 0])
            pd.DataFrame(cm, index=["real: vitória", "real: não vitória"],
                         columns=["prev.: vitória", "prev.: não vitória"]).to_csv(
                TABELAS / "matriz_confusao_temporal.csv", encoding="utf-8")

    # Árvore com três classes (vitória, empate, derrota).
    arv3 = GridSearchCV(DecisionTreeClassifier(random_state=SEMENTE, class_weight="balanced"),
                        GRADE_ARVORE, cv=cv5, scoring="balanced_accuracy").fit(X, y3).best_estimator_
    acc3, dp3, bal3 = avaliar_cv(arv3, X, y3, cv_rep)
    base3 = avaliar_cv(DummyClassifier(strategy="most_frequent"), X, y3, cv_rep)
    linhas.append({"modelo": "Árvore 3 classes (V/E/D)", "acuracia_cv": acc3, "dp_cv": dp3,
                   "acuracia_balanceada_cv": bal3})
    linhas.append({"modelo": "Linha de base 3 classes", "acuracia_cv": base3[0],
                   "dp_cv": base3[1], "acuracia_balanceada_cv": base3[2]})

    # Sensibilidade: sem a temporada 2020 (jogos sem torcida).
    sem20 = df["temporada"] >= 2021
    acc_s, dp_s, bal_s = avaliar_cv(arvore, X[sem20], y[sem20], cv_rep)
    linhas.append({"modelo": "Árvore sem 2020", "acuracia_cv": acc_s, "dp_cv": dp_s,
                   "acuracia_balanceada_cv": bal_s})

    met = pd.DataFrame(linhas)
    met.to_csv(TABELAS / "metricas_modelos.csv", index=False, encoding="utf-8")

    # Robustez: a posição final do adversário só é conhecida ao fim da
    # temporada. Comparamos com a posição no ano anterior (conhecida antes do
    # jogo) e com modelos sem nenhuma medida do adversário.
    rob = []
    for cenario, cols in CENARIOS_ROBUSTEZ.items():
        Xc = df[cols]
        arv_cv, _ = ajustar_arvore(Xc, y, cv5)
        arv_t, _ = ajustar_arvore(Xc[treino], y[treino], cv5)
        logit = make_pipeline(StandardScaler(), LogisticRegression(
            class_weight="balanced", max_iter=1000))
        for modelo, m_cv, m_t in [("Árvore de decisão", arv_cv, arv_t),
                                  ("Regressão logística", logit,
                                   clone(logit).fit(Xc[treino], y[treino]))]:
            _, _, bal = avaliar_cv(m_cv, Xc, y, cv_rep)
            pred = m_t.predict(Xc[~treino])
            rob.append({"cenario": cenario, "modelo": modelo,
                        "acuracia_balanceada_cv": bal,
                        "acuracia_balanceada_temporal": balanced_accuracy_score(
                            y[~treino], pred)})
    rob = pd.DataFrame(rob)
    rob.to_csv(TABELAS / "metricas_robustez.csv", index=False, encoding="utf-8")

    # Importância das variáveis por permutação, medida no teste temporal
    # (2024-2025) com a floresta treinada em 2020-2023. A importância por
    # redução de impureza favorece variáveis contínuas e não foi usada.
    rf_t = nova_floresta().fit(X[treino], y[treino])
    perm = permutation_importance(rf_t, X[~treino], y[~treino], n_repeats=50,
                                  scoring="balanced_accuracy", random_state=SEMENTE)
    arvore.fit(X, y)
    imp = pd.DataFrame({"variavel": PREDITORAS,
                        "importancia_arvore": arvore.feature_importances_,
                        "permutacao_media": perm.importances_mean,
                        "permutacao_dp": perm.importances_std}
                       ).sort_values("permutacao_media", ascending=False)
    imp.to_csv(TABELAS / "importancia_variaveis.csv", index=False, encoding="utf-8")
    regras = export_text(arvore, feature_names=[NOMES[c] for c in PREDITORAS],
                         show_weights=True)
    (TABELAS / "regras_arvore.txt").write_text(regras, encoding="utf-8")

    # Figura 3: diagrama da árvore com as taxas reais de vitória de cada nó.
    desenhar_arvore(arvore, X, y, FIGURAS / "fig3_arvore")

    # Figura 4: importância por permutação.
    imp_o = imp.sort_values("permutacao_media")
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    pos = np.arange(len(imp_o))
    ax.barh(pos, imp_o["permutacao_media"] * 100, color=COR_CAMPEAO, height=0.6)
    ax.errorbar(imp_o["permutacao_media"] * 100, pos, xerr=imp_o["permutacao_dp"] * 100,
                fmt="none", ecolor=TINTA_2, elinewidth=0.8, capsize=2)
    ax.set_yticks(pos, [NOMES[v] for v in imp_o["variavel"]])
    ax.axvline(0, color=TINTA_2, linewidth=0.8)
    ax.set_xlabel("Queda na acurácia balanceada ao embaralhar a variável (p.p.)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}".replace("-", "−")))
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    fig.savefig(FIGURAS / "fig4_importancia.png", dpi=300)
    fig.savefig(FIGURAS / "fig4_importancia.pdf")
    plt.close(fig)

    print("Parâmetros da árvore:", params)
    print(met.round(3).to_string(index=False))
    print(rob.round(3).to_string(index=False))
    print(imp.round(3).to_string(index=False))
    print(regras)
    print((TABELAS / "matriz_confusao_temporal.csv").read_text(encoding="utf-8"))


if __name__ == "__main__":
    saida_utf8()
    main()
