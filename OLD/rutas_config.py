import os
import platform

if platform.system() == "Windows":
    DATA_DIR = os.path.dirname(__file__)
else:
    DATA_DIR = "/mnt/c/Users/adm_tipy/OneDrive - Generadora Metropolitana/ReportePPA"

DIRECTORIO_DESCARGA_CONTRATOS = os.path.join(DATA_DIR, "descarga_contratos")
os.makedirs(DIRECTORIO_DESCARGA_CONTRATOS, exist_ok=True)

DIRECTORIO_RESULTADOS_CONTRATOS = os.path.join(DATA_DIR, "resultados_contratos")
os.makedirs(DIRECTORIO_RESULTADOS_CONTRATOS, exist_ok=True)

DIRECTORIO_DESCARGA = os.path.join(DATA_DIR, "descargados")
os.makedirs(DIRECTORIO_DESCARGA, exist_ok=True)

DIRECTORIO_RESULTADOS = os.path.join(DATA_DIR, "resultados")
os.makedirs(DIRECTORIO_RESULTADOS, exist_ok=True)

DIRECTORIO_PROCESADOS = os.path.join(DATA_DIR, "procesados")
os.makedirs(DIRECTORIO_PROCESADOS, exist_ok=True)

DIRECTORIO_LOGS = os.path.join(DATA_DIR, "logs")
os.makedirs(DIRECTORIO_LOGS, exist_ok=True)

DIRECTORIO_CACHE = os.path.join(DATA_DIR, "cache")
os.makedirs(DIRECTORIO_CACHE, exist_ok=True)

DIRECTORIO_MAPA = os.path.join(DATA_DIR, "mapa")
os.makedirs(DIRECTORIO_MAPA, exist_ok=True)

DIRECTORIO_sii = os.path.join(DATA_DIR, "bbdd del sii")
os.makedirs(DIRECTORIO_sii, exist_ok=True)

DIRECTORIO_PROCESADOS_CMG = os.path.join(DATA_DIR, "procesados_cmg")
os.makedirs(DIRECTORIO_PROCESADOS_CMG, exist_ok=True)

DIRECTORIO_RESULTADOS_CMG = os.path.join(DATA_DIR, "resultados_cmg")
os.makedirs(DIRECTORIO_RESULTADOS_CMG, exist_ok=True)

DIRECTORIO_PROCESADOS_INY = os.path.join(DATA_DIR, "procesados_iny")
os.makedirs(DIRECTORIO_PROCESADOS_INY, exist_ok=True)

DIRECTORIO_RESULTADOS_INY = os.path.join(DATA_DIR, "resultados_iny")
os.makedirs(DIRECTORIO_RESULTADOS_INY, exist_ok=True)

DIRECTORIO_RESULTADOS_INY_CONCAT = os.path.join(DATA_DIR, "resultados_iny_concat")
os.makedirs(DIRECTORIO_RESULTADOS_INY_CONCAT, exist_ok=True)

DIRECTORIO_RETIROS_PROCESADOS_INY = os.path.join(DATA_DIR, "resultados_ret_para_iny_preproces")
os.makedirs(DIRECTORIO_RETIROS_PROCESADOS_INY, exist_ok=True)