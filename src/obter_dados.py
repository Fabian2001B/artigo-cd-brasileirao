"""Etapa 1: obtenção dos dados.

Baixa os arquivos exportados pelo TCC (SofaScore + FBref) a partir de um
commit fixo do repositório público. Se os arquivos já existirem em data/raw,
nada é baixado de novo.
"""
import urllib.request

from config import ARQUIVOS_TCC, CLASSIFICACAO, DADOS_BRUTOS, TCC_COMMIT, TCC_REPO
from estilo import saida_utf8


def main():
    DADOS_BRUTOS.mkdir(parents=True, exist_ok=True)
    for nome in ARQUIVOS_TCC:
        destino = DADOS_BRUTOS / nome
        if destino.exists():
            print(f"[ok] {nome} já existe")
            continue
        url = (
            f"https://raw.githubusercontent.com/{TCC_REPO}/{TCC_COMMIT}"
            f"/data/exports/{nome}"
        )
        print(f"[baixando] {url}")
        urllib.request.urlretrieve(url, destino)
    if not CLASSIFICACAO.exists():
        raise FileNotFoundError(
            f"{CLASSIFICACAO} não encontrado; ele faz parte do repositório."
        )
    print("[ok] classificação final 2020-2025 disponível")


if __name__ == "__main__":
    saida_utf8()
    main()
