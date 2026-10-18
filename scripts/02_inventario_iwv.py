#Quantidade de observações disponíveis.
#Primeiro e último horário.
#Resolução temporal predominante.
#Percentual de registros ausentes.
#Duplicações e interrupções.
#Estatísticas diárias do IWV.
#Indicadores de qualidade dos dados meteorológicos.


from pathlib import Path
import pandas as pd

PROJETO = Path(__file__).resolve().parents[1]
BASE = PROJETO / "dados/brutos_windows/IWV_export"

# ============================================================
# 01. CONFIGURAÇÃO DOS DIRETÓRIOS DE SAÍDA
# ============================================================

SAIDA = PROJETO / "processados" / "inventario"

SAIDA_CSV = SAIDA / "csv"
SAIDA_TXT = SAIDA / "txt"

# Criação automática das pastas
SAIDA_CSV.mkdir(parents=True, exist_ok=True)
SAIDA_TXT.mkdir(parents=True, exist_ok=True)


COLUNAS = [
    "estacao", "fonte_met", "data", "segJul",
    "Pres", "Temp", "UR", "DTROP",
    "DZH", "DZW", "TM", "IWV"
]

def classificar_periodo(data):
    ano, mes = data.year, data.month

    if mes == 12:
        return "chuvosa", f"{ano}/{ano+1}"

    if 1 <= mes <= 5:
        return "chuvosa", f"{ano-1}/{ano}"

    if 6 <= mes <= 7:
        return "transicao", str(ano)

    return "seca", str(ano)


# ============================================================
# 02. FUNÇÃO PARA EXPORTAÇÃO CSV E TXT
# ============================================================

def salvar_csv_txt(df, nome):

    # 2.1. Salvar CSV
    caminho_csv = SAIDA_CSV / f"{nome}.csv"

    df.to_csv(
        caminho_csv,
        index=False,
        float_format="%.4f",
        na_rep="NaN"
    )

    # 2.2. Salvar TXT tabulado
    caminho_txt = SAIDA_TXT / f"{nome}.txt"

    df.to_csv(
        caminho_txt,
        sep="\t",
        index=False,
        float_format="%.4f",
        na_rep="NaN"
    )

    print(f"CSV salvo: {caminho_csv.name}")
    print(f"TXT salvo: {caminho_txt.name}")


# ============================================================
# IDENTIFICAÇÃO DAS LACUNAS TEMPORAIS
# ============================================================

def detectar_lacunas_dia(dia, validos):
    """
    Identifica intervalos consecutivos sem observações.

    Considera uma resolução temporal esperada de 15 s.

    Cada intervalo utiliza:
      inicio: primeiro horário ausente
      fim_exclusivo: primeiro horário após a lacuna

    Não modifica ou interpola os dados.
    """

    grade = pd.date_range(
        dia,
        periods=5760,
        freq="15s"
    )

    presentes = pd.DatetimeIndex(
        validos["datetime"].dropna().unique()
    )

    faltantes = grade.difference(presentes)

    if faltantes.empty:
        return []

    serie = pd.Series(faltantes)

    # Inicia um novo bloco quando há separação
    # superior a 15 segundos entre horários ausentes
    grupos = (
        serie.diff()
        .ne(pd.Timedelta(seconds=15))
        .cumsum()
    )

    lacunas = []

    for _, bloco in serie.groupby(grupos):

        inicio = bloco.iloc[0]
        ultimo = bloco.iloc[-1]

        lacunas.append({
            "inicio": inicio,
            "fim_exclusivo": ultimo + pd.Timedelta(seconds=15),
            "tipo": "lacuna_no_arquivo"
        })

    return lacunas


def inventariar(arquivo):
    nome = arquivo.name
    dia = pd.to_datetime(nome[4:11], format="%Y%j")

    df = pd.read_csv(
        arquivo,
        sep=r"\s+",
        comment="%",
        header=None,
        names=COLUNAS,
        dtype={"data": "string"}
    )

    df["datetime"] = pd.to_datetime(
        df["data"],
        format="%Y%m%d%H%M%S",
        errors="coerce"
    )

    # Grade diária nominal de 15 segundos
    grade = pd.date_range(dia, periods=5760, freq="15s")

    # Somente horários válidos, sem duplicação
    validos = (
        df.loc[df["datetime"].isin(grade)]
        .drop_duplicates(subset="datetime")
    )

    # Identifica lacunas dentro do arquivo diário
    lacunas_dia = detectar_lacunas_dia(dia, validos)

    iwv = pd.to_numeric(validos["IWV"], errors="coerce")
    ur = pd.to_numeric(validos["UR"], errors="coerce")

    resumo_dia = {
        "dia": dia,
        "arquivo": str(arquivo),
        "n_registros": len(df),
        "n_horarios_validos": len(validos),
        "n_faltantes": 5760 - len(validos),
        "n_duplicados": df["datetime"].dropna().duplicated().sum(),
        "n_fora_grade": (~df["datetime"].isin(grade)).sum(),
        "n_iwv_validos": iwv.count(),
        "soma_iwv": iwv.sum(),
        "iwv_media": iwv.mean(),
        "iwv_std": iwv.std(),
        "iwv_min": iwv.min(),
        "iwv_max": iwv.max(),
        "n_ur_acima100": (ur > 100).sum(),
        "n_ur_110": (ur == 110).sum(),
        "n_lacunas": len(lacunas_dia),

"maior_lacuna_min": max(
    (
        (l["fim_exclusivo"] - l["inicio"]).total_seconds() / 60
        for l in lacunas_dia
    ),
    default=0
),
    }

    return resumo_dia, lacunas_dia


# Prioriza IWV_export quando o nome existe nas duas pastas
arquivos = {
    p.name: p
    for p in (BASE / "timeseriesIA").glob("ztd_*iwv")
}
arquivos.update({
    p.name: p
    for p in BASE.glob("ztd_*iwv")
})


# ============================================================
# LEITURA E IDENTIFICAÇÃO DE LACUNAS
# ============================================================

registros = []
lacunas = []

for i, arquivo in enumerate(sorted(arquivos.values()), 1):

    resumo_dia, lacunas_dia = inventariar(arquivo)

    registros.append(resumo_dia)
    lacunas.extend(lacunas_dia)

    if i % 100 == 0:
        print(f"Processados: {i}/{len(arquivos)}")


    if i % 100 == 0:
        print(f"Processados: {i}/{len(arquivos)}")

inventario = pd.DataFrame(registros).sort_values("dia")

# Inclui dias sem arquivo dentro do intervalo observado
calendario = pd.DataFrame({
    "dia": pd.date_range(
        inventario["dia"].min(),
        inventario["dia"].max(),
        freq="D"
    )
})

inventario = calendario.merge(inventario, on="dia", how="left")
inventario["arquivo_encontrado"] = inventario["arquivo"].notna()

inventario[["periodo", "ciclo"]] = pd.DataFrame(
    inventario["dia"].map(classificar_periodo).tolist(),
    index=inventario.index
)

# Valores nulos nos dias sem arquivo representam zero observações
for col in [
    "n_registros", "n_horarios_validos", "n_iwv_validos",
    "n_ur_acima100", "n_ur_110", "soma_iwv"
]:
    inventario[col] = inventario[col].fillna(0)

    # Inclui corretamente os dias sem arquivo,
# que possuem 5760 horários esperados ausentes
inventario["n_faltantes"] = (
    5760 - inventario["n_horarios_validos"]
).astype(int) 


inventario["disponibilidade_pct"] = (
    100 * inventario["n_iwv_validos"] / 5760
)

# Inventário completo


# Resumo por ciclo sazonal
resumo = (
    inventario.groupby(["periodo", "ciclo"], as_index=False)
    .agg(
        inicio=("dia", "min"),
        fim=("dia", "max"),
        dias_calendario=("dia", "size"),
        dias_com_arquivo=("arquivo_encontrado", "sum"),
        n_iwv=("n_iwv_validos", "sum"),
        soma_iwv=("soma_iwv", "sum"),
        ur_acima100=("n_ur_acima100", "sum"),
        ur_110=("n_ur_110", "sum")
    )
)

resumo["iwv_media"] = (
    resumo["soma_iwv"] / resumo["n_iwv"].replace(0, float("nan"))
)

resumo["disponibilidade_pct"] = (
    100 * resumo["n_iwv"] /
    (resumo["dias_calendario"] * 5760)
)

resumo = resumo.sort_values("inicio")


# ============================================================
# LACUNAS CONTÍNUAS E DIAS PARA REPROCESSAMENTO
# ============================================================

# A. Adicionar dias inteiros sem arquivo
dias_sem_arquivo = inventario.loc[
    ~inventario["arquivo_encontrado"], "dia"
]

for dia in dias_sem_arquivo:
    lacunas.append({
        "inicio": dia,
        "fim_exclusivo": dia + pd.Timedelta(days=1),
        "tipo": "dia_sem_arquivo"
    })


# B. Unir lacunas consecutivas, inclusive entre dias
episodios = []

for trecho in sorted(lacunas, key=lambda x: x["inicio"]):

    if (
        episodios
        and trecho["inicio"] <= episodios[-1]["fim_exclusivo"]
    ):
        atual = episodios[-1]

        atual["fim_exclusivo"] = max(
            atual["fim_exclusivo"],
            trecho["fim_exclusivo"]
        )

        atual["tipos"].add(trecho["tipo"])

    else:
        episodios.append({
            "inicio": trecho["inicio"],
            "fim_exclusivo": trecho["fim_exclusivo"],
            "tipos": {trecho["tipo"]}
        })


# C. Construir tabela dos intervalos contínuos
registros_lacunas = []

for episodio in episodios:

    inicio = episodio["inicio"]
    fim = episodio["fim_exclusivo"]
    ultimo_ausente = fim - pd.Timedelta(seconds=15)

    duracao_s = (fim - inicio).total_seconds()

    registros_lacunas.append({
        "inicio": inicio,
        "ultimo_horario_ausente": ultimo_ausente,
        "fim_exclusivo": fim,
        "duracao_min": duracao_s / 60,
        "n_amostras_ausentes": int(duracao_s / 15),
        "ano_inicio": inicio.year,
        "doy_inicio": inicio.dayofyear,
        "ano_fim": ultimo_ausente.year,
        "doy_fim": ultimo_ausente.dayofyear,
        "periodo_inicio": classificar_periodo(inicio)[0],
        "tipo": "+".join(sorted(episodio["tipos"]))
    })

lacunas_df = pd.DataFrame(registros_lacunas)


# D. Listar dias que precisam ser investigados
selecao = (
    (inventario["n_faltantes"] > 0)
    |
    (
        inventario["n_iwv_validos"]
        < inventario["n_horarios_validos"]
    )
)

dias_reprocessar = inventario.loc[selecao].copy()

dias_reprocessar["ano"] = dias_reprocessar["dia"].dt.year
dias_reprocessar["doy"] = dias_reprocessar["dia"].dt.dayofyear

dias_reprocessar["arquivo_esperado"] = (
    dias_reprocessar["dia"].dt.strftime("ztd_%Y%jiwv")
)


def identificar_motivo(linha):

    if not linha["arquivo_encontrado"]:
        return "arquivo_ausente"

    motivos = []

    if linha["n_faltantes"] > 0:
        motivos.append("lacuna_temporal")

    if linha["n_iwv_validos"] < linha["n_horarios_validos"]:
        motivos.append("iwv_nao_numerico")

    return "+".join(motivos)


dias_reprocessar["motivo"] = dias_reprocessar.apply(
    identificar_motivo,
    axis=1
)

# Dias com mais dados ausentes aparecem primeiro
dias_reprocessar = dias_reprocessar.sort_values(
    ["n_faltantes", "dia"],
    ascending=[False, True]
)


# Seleção das colunas para o relatório de reprocessamento
dias_reprocessar = dias_reprocessar[
    [
        "dia",
        "ano",
        "doy",
        "arquivo_esperado",
        "arquivo_encontrado",
        "motivo",
        "n_faltantes",
        "n_horarios_validos",
        "n_iwv_validos",
        "disponibilidade_pct",
        "periodo",
        "ciclo",
        "arquivo"
    ]
].copy()


# ============================================================
# RELATÓRIO DE SEMANAS PARA INVESTIGAÇÃO NA FLORESTA
# ============================================================

# Copia os dias que apresentam algum problema
df_semanas = dias_reprocessar.copy()

# Calcula a semana ISO e o ano ISO
iso = df_semanas["dia"].dt.isocalendar()

df_semanas["ano_iso"] = iso.year.astype(int)
df_semanas["semana_iso"] = iso.week.astype(int)

# Segunda-feira de cada semana
df_semanas["inicio_semana"] = (
    df_semanas["dia"]
    - pd.to_timedelta(
        df_semanas["dia"].dt.dayofweek,
        unit="D"
    )
)

# Diferencia lacunas de IWV de horários ausentes
df_semanas["n_iwv_nao_numerico"] = (
    df_semanas["n_horarios_validos"]
    - df_semanas["n_iwv_validos"]
).clip(lower=0)

# Agrupa os dias problemáticos por semana
relatorio_semanal = (
    df_semanas.groupby(
        ["ano_iso", "semana_iso", "inicio_semana"],
        as_index=False
    )
    .agg(
        primeiro_dia_falha=("dia", "min"),
        ultimo_dia_falha=("dia", "max"),
        dias_afetados=("dia", "nunique"),
        amostras_ausentes=("n_faltantes", "sum"),
        iwv_nao_numerico=("n_iwv_nao_numerico", "sum"),
        dias_sem_arquivo=(
            "arquivo_encontrado",
            lambda x: int((~x).sum())
        )
    )
)


# ============================================================
# CONVENÇÕES SEMANAIS DA FLORESTA
# ============================================================

# Semana baseada em %W, utilizada no modo automático
# do script proceATTOweek.ksh
relatorio_semanal["semana_W"] = (
    relatorio_semanal["inicio_semana"]
    .dt.strftime("%W")
    .astype(int)
)

# Número da semana ISO, preservado para comparação
relatorio_semanal["semana_ISO"] = (
    relatorio_semanal["inicio_semana"]
    .dt.isocalendar().week.astype(int)
)

# Comando candidato utilizando %W.
# Ainda deve ser validado antes da execução.
def gerar_comando_W(linha):
    data = linha["inicio_semana"]
    semana = int(linha["semana_W"])

    return (
        f"./proceATTOweek.ksh "
        f"{data.year} {data.month:02d} "
        f"{data.day:02d} {semana:02d}"
    )


relatorio_semanal["comando_W"] = (
    relatorio_semanal.apply(
        gerar_comando_W,
        axis=1
    )
)


# ============================================================
# DEFINIÇÃO DO FIM DA SEMANA
# ============================================================

# A semana começa na segunda-feira e termina no domingo
relatorio_semanal["fim_semana"] = (
    relatorio_semanal["inicio_semana"]
    + pd.Timedelta(days=6)
)


# Requer conferência especial na virada do ano
relatorio_semanal["revisar_virada_ano"] = (
    (relatorio_semanal["semana_W"] == 0)
    | (relatorio_semanal["semana_W"] >= 52)
    | (
        relatorio_semanal["inicio_semana"].dt.year
        != relatorio_semanal["fim_semana"].dt.year
    )
)


relatorio_semanal["horas_ausentes"] = (
    relatorio_semanal["amostras_ausentes"] * 15 / 3600
)

# Comandos candidatos: NÃO executar automaticamente
def comando_floresta(linha):
    data = linha["inicio_semana"]
    semana = int(linha["semana_iso"])

    return (
        f"./proceATTOweek.ksh "
        f"{data.year} {data.month:02d} "
        f"{data.day:02d} {semana:02d}"
    )


relatorio_semanal["comando_sugerido"] = (
    relatorio_semanal.apply(comando_floresta, axis=1)
)

# Sinalizar semanas na virada do ano ISO
relatorio_semanal["revisar_ano_semana"] = (
    relatorio_semanal["inicio_semana"].dt.year
    != relatorio_semanal["ano_iso"]
)

# Ordenar cronologicamente
relatorio_semanal = relatorio_semanal.sort_values(
    "inicio_semana"
)


# ============================================================
# 07. EXPORTAÇÃO DOS RESULTADOS
# ============================================================

print("\nSalvando inventários em CSV e TXT...")

# 7.1. Inventário diário completo
salvar_csv_txt(
    inventario,
    "inventario_completo"
)

# 7.2. Inventários separados por estação
for periodo in ["chuvosa", "transicao", "seca"]:

    dados_periodo = inventario[
        inventario["periodo"] == periodo
    ].copy()

    salvar_csv_txt(
        dados_periodo,
        f"inventario_{periodo}"
    )

# 7.3. Resumo por ciclo sazonal
salvar_csv_txt(
    resumo,
    "resumo_sazonal"
)

# Relatório dos intervalos sem observações
salvar_csv_txt(
    lacunas_df,
    "lacunas_iwv"
)

# Lista de dias para investigação na FLORESTA
salvar_csv_txt(
    dias_reprocessar,
    "dias_para_reprocessar"
)

# Semanas com lacunas para investigação na FLORESTA
salvar_csv_txt(
    relatorio_semanal,
    "semanas_para_reprocessar"
)
# ============================================================
# 08. RELATÓRIO FINAL
# ============================================================

print("\nInventário finalizado!")
print(f"Arquivos analisados: {len(arquivos)}")

print("\nResumo sazonal:")
print(
    resumo[
        [
            "periodo",
            "ciclo",
            "dias_com_arquivo",
            "disponibilidade_pct",
            "iwv_media"
        ]
    ].to_string(index=False)
)
