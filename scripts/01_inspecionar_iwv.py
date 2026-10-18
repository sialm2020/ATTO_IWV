
from pathlib import Path
import pandas as pd

# Diretório do projeto
PROJETO = Path(__file__).resolve().parents[1]
BASE = PROJETO / "dados/brutos_windows/IWV_export"

COLUNAS = [
    "estacao", "fonte_met", "data", "segJul",
    "Pres", "Temp", "UR", "DTROP",
    "DZH", "DZW", "TM", "IWV"
]

ARQUIVOS = [
    BASE / "timeseriesIA/ztd_2023184iwv",
    BASE / "ztd_2025001iwv",
]

def ler_iwv(caminho):
    df = pd.read_csv(
        caminho,
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

    return df.sort_values("datetime").reset_index(drop=True)


for arquivo in ARQUIVOS:
    df = ler_iwv(arquivo)

    dt = df["datetime"].diff().dt.total_seconds()

    print(f"\n{'=' * 55}")
    print(f"Arquivo: {arquivo.name}")
    print(f"Registros: {len(df)}")
    print(f"Início: {df['datetime'].min()}")
    print(f"Fim: {df['datetime'].max()}")
    print(f"Intervalo mediano: {dt.median()} s")
    print(f"Intervalos de 15 s: {(dt == 15).sum()}")
    print(f"Datas duplicadas: {df['datetime'].duplicated().sum()}")
    print(f"Datas inválidas: {df['datetime'].isna().sum()}")
    print(f"UR > 100%: {(df['UR'] > 100).sum()}")

    print("\nEstatísticas do IWV:")
    print(df["IWV"].describe().round(3))
