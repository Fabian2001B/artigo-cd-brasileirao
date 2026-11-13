# O que decide a disputa pelo título?

Fatores associados ao desempenho de campeões e vice-campeões do Campeonato
Brasileiro Série A entre 2020 e 2025.

Artigo final da disciplina de Ciência de Dados, IFMG Campus Sabará.
Integrantes: Luan Kauan, Fabian Bernardes, Nathan Siqueira e Robert Barbosa.

## Objetivo

Identificar, com árvores de decisão, quais fatores de partida (mando de campo,
força do adversário, forma recente, perfil dos titulares e calendário) estão
associados à vitória das equipes que disputaram o título entre 2020 e 2025, e
comparar esses padrões entre campeões e vice-campeões.

## Como reproduzir

Requisitos: Python 3.11 ou superior (testado com 3.13.2).

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python run_all.py
```

O `run_all.py` executa as quatro etapas em sequência e leva menos de um
minuto. Cada etapa também pode ser rodada sozinha, de dentro da pasta `src`
(por exemplo, `python modelagem.py`). As sementes aleatórias são fixas
(`SEMENTE = 42` em `src/config.py`), então os números são sempre os mesmos.

## Etapas do pipeline

| Etapa | Script | O que faz | Saídas |
| --- | --- | --- | --- |
| 1. Obtenção | `src/obter_dados.py` | Baixa os CSVs do TCC a partir de um commit fixo | `data/raw/*.csv` |
| 2. Preparação | `src/preparar.py` | Recorte, limpeza, variáveis derivadas e validações | `data/processed/partidas_disputa_titulo.csv`, `outputs/tables/validacao.txt` |
| 3. Exploração | `src/exploratoria.py` | Taxas de vitória e pontos perdidos por fator | `outputs/tables/*.csv`, `outputs/figures/fig1*`, `fig2*` |
| 4. Modelagem | `src/modelagem.py` | Árvores de decisão, comparação de modelos, importância | `outputs/tables/metricas_modelos.csv`, `fig3*`, `fig4*` |

## Dados

| Arquivo | Origem | Conteúdo |
| --- | --- | --- |
| `data/raw/todos-base_detalhada_geral_publico.csv` | [TCC de Luan Kauan](https://github.com/AlvesLuan/tcc_scraper_sofascore), commit `23af40d` (coleta no SofaScore e no FBref) | 4.898 partidas dos clubes do Clube dos 13, 2015 a 2025 |
| `data/raw/z4-todos-base_detalhada_geral_publico.csv` | mesmo repositório | jogos contra equipes do Z4 |
| `data/external/classificacao_final_2020_2025.csv` | Wikipédia, páginas "20XX Campeonato Brasileiro Série A" (consultadas em 12/11/2026) | posição e pontos finais dos 20 clubes por temporada |
| `data/processed/partidas_disputa_titulo.csv` | gerado por `preparar.py` | 456 partidas (12 campanhas x 38 rodadas), base usada na análise |

Os arquivos brutos já estão no repositório. Se forem apagados, `obter_dados.py`
baixa novamente a mesma versão. Os dados são públicos e usados apenas para
fins acadêmicos.

### Dicionário da base processada (principais colunas)

| Coluna | Descrição |
| --- | --- |
| `papel` | Campeão ou Vice na temporada |
| `vitoria` | 1 se a equipe venceu a partida (variável-alvo) |
| `resultado` | Vitória, Empate ou Derrota (alvo da versão com três classes) |
| `mandante` | 1 se a equipe jogou em casa |
| `posicao_adv` | Posição final do adversário na tabela (1 a 20) |
| `adv_z4` | 1 se o adversário terminou entre o 17º e o 20º lugar |
| `forma_recente` | Média de pontos por jogo nas 5 partidas anteriores (1,5 na 1ª rodada) |
| `dif_idade`, `dif_altura` | Idade (anos) e altura (cm) médias dos titulares: equipe menos adversário |
| `rodada`, `reta_final` | Rodada e indicador de rodada 30 ou posterior |
| `meio_semana`, `hora` | Jogo de segunda a sexta e hora de início |
| `confronto_direto` | 1 se o adversário é o outro postulante ao título |

## Estrutura

```
├── data/
│   ├── raw/          # dados originais do TCC
│   ├── external/     # classificação final 2020-2025
│   └── processed/    # base pronta para análise
├── outputs/
│   ├── figures/      # figuras do artigo (PNG e PDF)
│   └── tables/       # tabelas e métricas
├── src/
│   ├── config.py
│   ├── obter_dados.py
│   ├── preparar.py
│   ├── exploratoria.py
│   └── modelagem.py
├── run_all.py
└── requirements.txt
```

## Principais resultados preliminares

- Mando de campo e posição final do adversário são as variáveis que mais
  explicam a vitória; idade, altura e calendário pesam pouco.
- A árvore de decisão (profundidade 2) tem acurácia balanceada de 0,60 na
  validação cruzada e de 0,64 no teste temporal (2024-2025), contra 0,50 da
  linha de base.
- Os vice-campeões perderam 33 pontos a mais que os campeões no período,
  sobretudo contra equipes do 5º ao 8º e do 13º ao 16º lugar.
