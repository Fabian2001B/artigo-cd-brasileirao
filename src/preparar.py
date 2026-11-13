"""Etapa 2: limpeza, transformação e validação dos dados.

Gera data/processed/partidas_disputa_titulo.csv (uma linha por partida de um
campeão ou vice) e outputs/tables/validacao.txt com as checagens feitas.
"""
import numpy as np
import pandas as pd

from config import (
    BASE_PROCESSADA, CAMPANHAS, CLASSIFICACAO, DADOS_BRUTOS, TABELAS,
)

PONTOS = {"Vitória": 3, "Empate": 1, "Derrota": 0}
DIAS_UTEIS = {"Segunda", "Terça", "Quarta", "Quinta", "Sexta"}
NUMERICAS = [
    "idade_media_titular_time", "altura_media_titular_time",
    "idade_media_titular_adv", "altura_media_titular_adv", "publico",
]


def carregar():
    base = pd.read_csv(DADOS_BRUTOS / "todos-base_detalhada_geral_publico.csv",
                       encoding="utf-8-sig")
    z4 = pd.read_csv(DADOS_BRUTOS / "z4-todos-base_detalhada_geral_publico.csv",
                     encoding="utf-8-sig")
    classif = pd.read_csv(CLASSIFICACAO, encoding="utf-8")
    return base, z4, classif


def forma_recente(df):
    """Média de pontos por jogo nas 5 partidas anteriores da mesma campanha."""
    df = df.sort_values("data_dt")
    pts = df["resultado"].map(PONTOS)
    return pts.shift(1).rolling(5, min_periods=1).mean()


def main():
    base, z4, classif = carregar()
    log = []

    # Tipos: colunas numéricas vêm como texto em parte do arquivo.
    for c in NUMERICAS:
        base[c] = pd.to_numeric(base[c], errors="coerce")
    base["data_dt"] = pd.to_datetime(base["data"], format="%d/%m/%Y")

    # Recorte: campanhas de campeões e vices 2020-2025.
    chave = list(zip(base["temporada"], base["time"]))
    base["papel"] = [CAMPANHAS.get(k) for k in chave]
    df = base[base["papel"].notna()].copy()
    log.append(f"Partidas no recorte: {len(df)} (esperado: 12 x 38 = 456)")

    # Forma recente (calculada antes de qualquer filtro adicional).
    df["forma_recente"] = (
        df.groupby(["temporada", "time"], group_keys=False).apply(forma_recente)
    )
    n_sem_forma = int(df["forma_recente"].isna().sum())
    df["forma_recente"] = df["forma_recente"].fillna(1.5)
    log.append(f"Primeira rodada sem histórico (forma = 1,5 ponto/jogo): {n_sem_forma}")

    # Força do adversário: posição final na classificação.
    df = df.merge(
        classif.rename(columns={"clube": "adversario", "posicao": "posicao_adv",
                                "pontos": "pontos_adv"}),
        on=["temporada", "adversario"], how="left",
    )
    log.append(f"Adversários sem posição final: {int(df['posicao_adv'].isna().sum())}")

    # Checagem cruzada com o arquivo Z4 do TCC.
    z4_chaves = set(zip(z4["time"], z4["temporada"], z4["rodada"]))
    df["adv_z4_tcc"] = [int(k in z4_chaves)
                        for k in zip(df["time"], df["temporada"], df["rodada"])]
    df["adv_z4"] = (df["posicao_adv"] >= 17).astype(int)
    diverg = int((df["adv_z4"] != df["adv_z4_tcc"]).sum())
    log.append(f"Jogos contra Z4: {int(df['adv_z4'].sum())}; divergências com o arquivo Z4 do TCC: {diverg}")

    # Validação dos pontos de cada campanha contra a classificação oficial.
    df["pontos"] = df["resultado"].map(PONTOS)
    soma = df.groupby(["temporada", "time"])["pontos"].sum().reset_index()
    oficial = classif.rename(columns={"clube": "time", "pontos": "pontos_oficial"})
    conf = soma.merge(oficial, on=["temporada", "time"])
    erros = conf[conf["pontos"] != conf["pontos_oficial"]]
    log.append(f"Campanhas com pontos diferentes da tabela oficial: {len(erros)} de {len(conf)}")
    log.append(f"Jogos por campanha: min {df.groupby(['temporada','time']).size().min()}, "
               f"max {df.groupby(['temporada','time']).size().max()}")
    log.append(f"Rodadas duplicadas: {int(df.duplicated(['temporada','time','rodada']).sum())}")
    log.append(f"Resultado incoerente com o placar: "
               f"{int(((df.gols_favor > df.gols_sofridos) != (df.resultado == 'Vitória')).sum())}")

    # Valores ausentes.
    for c in NUMERICAS:
        log.append(f"Ausentes em {c}: {int(df[c].isna().sum())}")
    log.append(f"Público ausente ou zero: {int((df['publico'].isna() | (df['publico'] == 0)).sum())}")
    log.append(f"Árbitros com apóstrofo no nome: {int(df['arbitro'].str.contains(chr(39), na=False).sum())}")

    # Confrontos diretos entre campeão e vice (aparecem duas vezes).
    pares = {(t, tm) for (t, tm) in CAMPANHAS}
    df["confronto_direto"] = [int((t, a) in pares) for t, a in zip(df["temporada"], df["adversario"])]
    log.append(f"Linhas de confronto direto campeão x vice: {int(df['confronto_direto'].sum())}")

    # Variáveis derivadas.
    df["vitoria"] = (df["resultado"] == "Vitória").astype(int)
    df["mandante"] = (df["condicao"] == "Mandante").astype(int)
    df["campeao"] = (df["papel"] == "Campeão").astype(int)
    df["dif_idade"] = df["idade_media_titular_time"] - df["idade_media_titular_adv"]
    df["dif_altura"] = df["altura_media_titular_time"] - df["altura_media_titular_adv"]
    df["meio_semana"] = df["dia_semana"].isin(DIAS_UTEIS).astype(int)
    df["reta_final"] = (df["rodada"] >= 30).astype(int)
    df["hora"] = df["horario"].str.slice(0, 2).astype(int)
    df["arbitro"] = df["arbitro"].str.replace("'", "", regex=False)
    df["faixa_adv"] = pd.cut(df["posicao_adv"], [0, 4, 8, 12, 16, 20],
                             labels=["1º-4º", "5º-8º", "9º-12º", "13º-16º", "17º-20º"])

    colunas = [
        "temporada", "rodada", "data", "time", "papel", "adversario", "condicao",
        "resultado", "gols_favor", "gols_sofridos", "pontos", "vitoria",
        "mandante", "campeao", "posicao_adv", "pontos_adv", "faixa_adv", "adv_z4",
        "forma_recente", "dif_idade", "dif_altura", "idade_media_titular_time",
        "altura_media_titular_time", "rodada", "reta_final", "meio_semana",
        "dia_semana", "hora", "publico", "confronto_direto", "arbitro", "estadio",
    ]
    colunas = list(dict.fromkeys(colunas))
    BASE_PROCESSADA.parent.mkdir(parents=True, exist_ok=True)
    df[colunas].sort_values(["temporada", "papel", "rodada"]).to_csv(
        BASE_PROCESSADA, index=False, encoding="utf-8")

    TABELAS.mkdir(parents=True, exist_ok=True)
    (TABELAS / "validacao.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    print(f"[ok] {BASE_PROCESSADA}")


if __name__ == "__main__":
    main()
