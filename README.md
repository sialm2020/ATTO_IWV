# ATTO PWV Analysis

## Auditoria da série GNSS-PWV da ATTO/Campina e suporte ao reprocessamento na FLORESTA

Este repositório reúne ferramentas e **relatórios de disponibilidade temporal** dos dados de vapor d'água integrado (**IWV**, derivado de GNSS) da estação **CAFE, ATTO/Campina (Amazônia Central)**. Nesta etapa, o foco é **identificar lacunas, documentar evidências de falhas no processamento e subsidiar a priorização do reprocessamento na máquina FLORESTA**.

> **Estado em 19/10/2026:** auditoria e testes diagnósticos realizados; os dados de março de 2026 aqui discutidos **não foram recuperados**. Nenhuma saída oficial foi substituída pelos testes descritos abaixo.

## Resultado principal: relatórios para reprocessamento

Os resultados desta etapa estão em **[`relatorios/floresta/txt/`](relatorios/floresta/txt/)**:

| Arquivo | Finalidade |
|---|---|
| [`dias_para_reprocessar.txt`](relatorios/floresta/txt/dias_para_reprocessar.txt) | Lista de dias indicados pela auditoria para revisão e possível reprocessamento. |
| [`semanas_para_reprocessar.txt`](relatorios/floresta/txt/semanas_para_reprocessar.txt) | Agrupamento semanal para planejar a recuperação e investigar os logs correspondentes. |
| [`lacunas_iwv.txt`](relatorios/floresta/txt/lacunas_iwv.txt) | Identificação das descontinuidades da série temporal IWV. |
| [`inventario_completo.txt`](relatorios/floresta/txt/inventario_completo.txt) | Inventário geral de cobertura e disponibilidade. |
| [`inventario_chuvosa.txt`](relatorios/floresta/txt/inventario_chuvosa.txt) | Inventário referente ao período chuvoso (dezembro–maio). |
| [`inventario_transicao.txt`](relatorios/floresta/txt/inventario_transicao.txt) | Inventário referente ao período de transição (junho–julho). |
| [`inventario_seca.txt`](relatorios/floresta/txt/inventario_seca.txt) | Inventário referente ao período seco (agosto–novembro). |
| [`resumo_sazonal.txt`](relatorios/floresta/txt/resumo_sazonal.txt) | Síntese sazonal da disponibilidade e das estatísticas de inventário. |

**Como usar:** começar por `lacunas_iwv.txt` e `dias_para_reprocessar.txt`, consultar o agrupamento em `semanas_para_reprocessar.txt` e conferir a cobertura no `inventario_completo.txt`. **Uma lacuna na série de IWV não comprova, por si só, ausência das observações GNSS:** a etapa de RINEX e os logs de PPP precisam ser examinados antes de reprocessar.

## Procedimento de auditoria

- Inventário dos arquivos diários GNSS-IWV reunidos a partir de dois conjuntos locais (2023–2026), com tratamento de nomes sobrepostos: **993 nomes diários distintos** no levantamento realizado.
- Verificação da continuidade da série de **15 segundos** (até **5.760 registros/dia**, para cobertura completa).
- Identificação de dias sem produtos e organização por período sazonal, com relatórios textuais destinados ao planejamento do reprocessamento.
- Inspeção dos diretórios de saída e dos registros históricos de execução na FLORESTA.

A contagem de arquivos distintos **não corresponde** necessariamente ao número de dias completos ou válidos; as métricas de disponibilidade e qualidade devem ser consultadas nos relatórios.

## Verificação inicial: lacunas de março de 2026

Na auditoria foram observadas lacunas de **01 a 18/03/2026**, além de **21/03/2026**, nos arquivos diários considerados. A inspeção dos produtos semanais indicou:

| Semana de processamento | Evidência encontrada |
|---|---|
| `2026_week08` | Produtos diários até 28/02; ausência do produto diário de 01/03 na saída examinada. |
| `2026_week09` | Sem os produtos IWV diários esperados; presente um agregado de várias semanas. |
| `2026_week10` | Sem os produtos IWV diários esperados; presente um agregado de várias semanas. |
| `2026_week11` | Produtos diários identificados para 19, 20 e 22/03; outros dias da semana ausentes na saída examinada. |

O log histórico de execução da **semana 09 (11/03/2026)** registrou arquivos RINEX disponíveis, porém falhas na obtenção de produtos orbitais precisos **WUM SP3**, impedindo a conclusão do processamento PPP esperado. **A versão exata do PRIDE usada nessa execução ainda não foi confirmada.** Portanto, não é possível atribuir todas as lacunas de março a uma mesma causa.

### Testes diagnósticos com o PRIDE PPP-AR atualizado

Em outubro de 2026, com o **PRIDE PPP-AR 3.2.12**, foi utilizado o arquivo RINEX da estação CAFE para **02/03/2026 (DOY 061)**. Os testes foram conduzidos em diretórios separados sob `/work/sapucci/`, sem executar a rotina semanal de publicação.

| Tentativa | Resultado |
|---|---|
| `pdp3 -m S` (produtos WUM) | Órbita SP3 obtida; relógio preciso WUM CLK.gz não passou no `gzip -t` (`unexpected end of file`). |
| `pdp3 -m S -wcc` (produtos WCC) | Preparação das tabelas e da navegação concluída; falha na obtenção de relógios WCC CLK.gz, também com erro de integridade gzip. |
| Diagnóstico WCC FIN | O servidor informou `Content-Length: 1835008`, igual ao tamanho recebido (**1.835.008 bytes**), mas o arquivo continuou inválido no teste gzip. |

**Interpretação:** há forte suspeita de que o CLK WCC FIN disponibilizado nesse endereço já esteja incompleto, mas a confirmação definitiva requer comparação com uma fonte independente confiável. O problema observado no teste atualizado é **distinto** daquele documentado no log histórico: **CLK em outubro versus SP3 na execução de março**.

**Observação operacional:** nos testes, o `pdp3` retornou código de saída **0** mesmo após registrar `PrepareProducts failed` e `processing failed`. Portanto, **não** validar o êxito de um reprocessamento apenas por `$?`: conferir os logs, a presença do ZTD e a consistência dos produtos.

**Resultado:** o teste de 02/03/2026 **não gerou o ZTD esperado**, e não houve recuperação ou substituição de IWV nesta etapa. Os testes foram interrompidos.

## Organização e ambiente

- `relatorios/floresta/txt/`: **resultados principais da auditoria e listas para orientar o reprocessamento**.
- `scripts/`: código Python de inventário, leitura e controle de qualidade, quando presente no repositório.
- `notebooks/`, `figuras/`, `processados/`, `resultados/`: materiais de análises complementares, conforme disponibilizados.
- `dados/`: referência local aos dados científicos; **os arquivos brutos não são versionados**.

Ambiente de análise: **Python 3.11 e Conda**, com ambiente `iwv_disdro`. Quando o arquivo `environment.yml` estiver disponível na raiz:

```bash
conda env create -f environment.yml
conda activate iwv_disdro
```

O reprocessamento PPP na FLORESTA utiliza uma instalação separada do **PRIDE PPP-AR**; instalar o ambiente Python **não** instala nem configura o PRIDE ou fornece acesso aos dados da FLORESTA.

## Escopo e cuidados de reprodutibilidade

Este repositório **documenta e orienta** a auditoria e o reprocessamento: ele não contém os arquivos RINEX, os produtos precisos GNSS, nem substitui os procedimentos operacionais autorizados na FLORESTA. Diretórios absolutos da máquina são informados apenas como contexto técnico; não são dependências portáveis. Não publicar credenciais, configurações com segredos, logs sensíveis ou dados brutos sem autorização.

**Status:** diagnóstico registrado; recuperação pendente de produtos GNSS auxiliares íntegros e de validação dos dias candidatos.
