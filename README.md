# ATTO IWV and Disdrometer Analysis

Projeto de processamento e análise de séries temporais de vapor d'água integrado (IWV) derivado de GNSS e observações do disdrômetro JOSS na região da ATTO, Amazônia Central.

## Objetivos

- Leitura e controle de qualidade dos dados GNSS-IWV.
- Avaliação da variabilidade temporal do IWV.
- Processamento dos dados do disdrômetro JOSS.
- Sincronização das séries temporais.
- Análise das relações entre IWV e características da precipitação.
- Investigação de aplicações para nowcasting.

## Organização

- `scripts/`: scripts de processamento Python.
- `notebooks/`: análises exploratórias.
- `figuras/`: visualizações científicas.
- `dados/`: acesso aos dados originais, não versionados.
- `processados/`: produtos intermediários.
- `resultados/`: estatísticas e resultados finais.

## Ambiente

Python 3.11 e Conda.

Para recriar o ambiente:

```bash
conda env create -f environment.yml
conda activate iwv_disdro
```

Os dados científicos são mantidos fora do controle de versão.
