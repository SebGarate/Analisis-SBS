"""
procesar_sbs.py - Cópialo en sbs-analisis/scripts/
Estructura:
  sbs-analisis/
  ├── data/raw/       ← pon los 18 xlsx aquí
  ├── data/processed/ ← se generan los CSVs aquí
  └── scripts/
      └── procesar_sbs.py

Instala: pip install pandas openpyxl
Corre:   python procesar_sbs.py
"""

import pandas as pd
import os
import re

RUTA_RAW       = "data/raw"
RUTA_PROCESSED = "data/processed"

TIPOS = {
    "B-2362": "morosidad",
    "B-2359": "creditos_tipo",
    "B-2336": "creditos_sector"
}

BANCOS_MAP = {
    "Banco de Crédito del Perú"                   : "BCP",
"Interbank (con sucursales en el exterior)"    : "Interbank",
"Banco Interamericano de Finanzas"             : "BanBif",
"Banco Pichincha"                              : "Pichincha",
"Banco Falabella Perú"                         : "Falabella",
"Banco Ripley"                                 : "Ripley",
"Banco GNB"                                    : "GNB",
"Banco Azteca"                                 : "Azteca",
"Banco BCI Perú"                               : "BCI",
"Santander Perú S.A."                          : "Santander",
"Total Banca Múltiple"                         : None,
"TOTAL BANCA MÚLTIPLE"                         : None,
"Total"                                        : None,
"Alfin Banco1/"                                : "Alfin Banco",
"Banco de Comercio"                            : "Comercio",
}

MESES = {
    "en":"01","fe":"02","ma":"03","ab":"04",
    "my":"05","ju":"06","jl":"07","ag":"08",
    "se":"09","oc":"10","no":"11","di":"12"
}

def extraer_periodo(nombre):
    match = re.search(r'([a-z]{2})(\d{4})', nombre.lower())
    if match:
        mes, anio = match.groups()
        return f"{anio}-{MESES.get(mes,'01')}"
    return "desconocido"

def normalizar_banco(nombre):
    if not nombre: return None
    return BANCOS_MAP.get(str(nombre).strip(), str(nombre).strip())

def procesar_morosidad(ruta, periodo):
    df_raw = pd.read_excel(ruta, header=None, sheet_name=0)
    IGNORAR = ["fuente", "actualizado", "en miles", "anexo", "nota", "(*)", "total",
               "la información", "los financiamientos", "mibanco envió", "estructura",
               "incluye sucursales"]
    fila_header = None
    for i, row in df_raw.iterrows():
        valores_str = [str(v) for v in row.values if v is not None and not isinstance(v, float)]
        if any("BBVA" in v or "Concepto" in v for v in valores_str):
            fila_header = i
            break
    if fila_header is None: return pd.DataFrame()
    bancos = [normalizar_banco(v) for v in df_raw.iloc[fila_header, 1:].values]
    registros = []
    for i in range(fila_header + 1, len(df_raw)):
        fila = df_raw.iloc[i]
        concepto = fila.iloc[0]
        if not isinstance(concepto, str): continue
        concepto = concepto.strip()
        if not concepto or concepto in ["None", "nan", ""]: continue
        if any(palabra in concepto.lower() for palabra in IGNORAR): continue
        if len(concepto) > 60: continue
        valores = [fila.iloc[j+1] for j in range(len(bancos)) if j+1 < len(fila)]
        if not any(isinstance(v, (int, float)) for v in valores): continue
        for j, banco in enumerate(bancos):
            if not banco: continue
            try: registros.append({"periodo":periodo,"banco":banco,"tipo_credito":concepto,"morosidad_pct": round(float(fila.iloc[j+1]), 4)
})
            except: continue
    return pd.DataFrame(registros)


def procesar_creditos_sector(ruta, periodo):
    df_raw = pd.read_excel(ruta, header=None, sheet_name=0)
    IGNORAR = ["fuente", "actualizado", "en miles", "anexo", "nota", "(*)", "total",
               "la información", "los financiamientos", "mibanco envió", "estructura",
               "incluye sucursales"]
    fila_header = None
    for i, row in df_raw.iterrows():
        valores_str = [str(v) for v in row.values if v is not None and not isinstance(v, float)]
        if any("BBVA" in v for v in valores_str):
            fila_header = i
            break
    if fila_header is None: return pd.DataFrame()
    bancos = [normalizar_banco(v) for v in df_raw.iloc[fila_header, 1:].values]
    registros = []
    for i in range(fila_header + 1, len(df_raw)):
        fila = df_raw.iloc[i]
        sector = fila.iloc[0]
        if not isinstance(sector, str): continue
        sector = sector.strip()
        if not sector or sector in ["None", "nan", ""]: continue
        if any(palabra in sector.lower() for palabra in IGNORAR): continue
        valores = [fila.iloc[j+1] for j in range(len(bancos)) if j+1 < len(fila)]
        if not any(isinstance(v, (int, float)) for v in valores): continue
        for j, banco in enumerate(bancos):
            if not banco: continue
            try: registros.append({"periodo":periodo,"banco":banco,"sector":sector,"creditos_miles":round(float(fila.iloc[j+1]),2)})
            except: continue
    return pd.DataFrame(registros)


def procesar_creditos_tipo(ruta, periodo):
    df_raw = pd.read_excel(ruta, header=None, sheet_name=0)
    IGNORAR = ["fuente", "actualizado", "en miles", "anexo", "nota", "(*)", "total",
               "la información", "los financiamientos", "mibanco envió", "estructura",
               "incluye sucursales","tipo de cambio"
]
    fila_bancos = None
    for i, row in df_raw.iterrows():
        valores_str = [str(v) for v in row.values if v is not None and not isinstance(v, float)]
        if any("BBVA" in v or "Interbank" in v for v in valores_str):
            fila_bancos = i
            break
    if fila_bancos is None: return pd.DataFrame()
    bancos_raw = list(df_raw.iloc[fila_bancos, 1:].values)
    monedas    = list(df_raw.iloc[fila_bancos + 1, 1:].values)
    cols_total = []
    banco_actual = None
    for j, (b, m) in enumerate(zip(bancos_raw, monedas)):
        if b and str(b).strip() not in ["None", "nan"]: banco_actual = normalizar_banco(str(b).strip())
        if "total" in str(m).lower(): cols_total.append((j + 1, banco_actual))
    registros = []
    for i in range(fila_bancos + 2, len(df_raw)):
        fila = df_raw.iloc[i]
        tipo = fila.iloc[0]
        if not isinstance(tipo, str): continue
        tipo = tipo.strip()
        if not tipo or tipo in ["None", "nan", ""]: continue
        if any(palabra in tipo.lower() for palabra in IGNORAR): continue
        valores = [fila.iloc[col_idx] for col_idx, _ in cols_total if col_idx < len(fila)]
        if not any(isinstance(v, (int, float)) for v in valores): continue
        for col_idx, banco in cols_total:
            if not banco or col_idx >= len(fila): continue
            try: registros.append({"periodo":periodo,"banco":banco,"tipo_credito":tipo,"creditos_miles":round(float(fila.iloc[col_idx]),2)})
            except: continue
    return pd.DataFrame(registros)




def main():
    os.makedirs(RUTA_PROCESSED, exist_ok=True)
    dfs = {"morosidad":[],"creditos_sector":[],"creditos_tipo":[]}
    archivos = sorted([f for f in os.listdir(RUTA_RAW) if f.endswith(".xlsx")])
    print(f"Archivos encontrados: {len(archivos)}")
    for archivo in archivos:
        ruta = os.path.join(RUTA_RAW, archivo)
        periodo = extraer_periodo(archivo)
        tipo = next((t for p,t in TIPOS.items() if archivo.startswith(p)), None)
        if not tipo: continue
        print(f"Procesando {archivo} → {periodo}")
        try:
            if tipo == "morosidad": df = procesar_morosidad(ruta, periodo)
            elif tipo == "creditos_sector": df = procesar_creditos_sector(ruta, periodo)
            elif tipo == "creditos_tipo": df = procesar_creditos_tipo(ruta, periodo)
            dfs[tipo].append(df)
            print(f"  ✔ {len(df)} registros")
        except Exception as e:
            print(f"  ✘ {e}")
    salidas = {
        "morosidad": "morosidad_consolidada.csv",
        "creditos_sector": "creditos_sector_consolidado.csv",
        "creditos_tipo": "creditos_tipo_consolidado.csv"
    }
    for tipo, archivo in salidas.items():
        if dfs[tipo]:
            df_final = pd.concat(dfs[tipo], ignore_index=True).dropna(how="all")
            df_final.to_csv(os.path.join(RUTA_PROCESSED, archivo), index=False)
            print(f"✔ {archivo} → {len(df_final):,} registros")

if __name__ == "__main__":
    main()

