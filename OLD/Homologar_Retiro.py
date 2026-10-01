import os
import json
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import random
from rapidfuzz import process, fuzz
import glob
import csv
from fake_useragent import UserAgent
import datetime
import sys
import unicodedata
import pyarrow
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR) 

import rutas_config

DIRECTORIO_DESCARGA = rutas_config.DIRECTORIO_DESCARGA
csv_RUTS = os.path.join(rutas_config.DIRECTORIO_RESULTADOS, "CompiladoEmpresasConRUT.csv")

DBUTIL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

empresas_encontradas = []

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

search_engines = [
    "https://www.google.com/search?q={query}+RUT+empresa+Chile",
    "https://www.portalchile.org/search?q={query}+RUT+empresa+Chile",
    "https://www.bing.com/search?q={query}+RUT+empresa+Chile",
    "https://search.yahoo.com/search?p={query}+RUT+empresa+Chile",
    "https://duckduckgo.com/?q={query}+RUT+empresa+Chile"
]

CACHE_FILE= os.path.join(rutas_config.DIRECTORIO_CACHE,"cache_ruts_empresas.json")

cache_ruts_empresas = {}

empresas_no_scrape={"OUTLET_GNAVALES","OC1000376037","SE BUIN-Alim VILLASECA","CORPORA_TM_CAFE",\
                    "CLT PARIS BARON","BOULEVARD_CURAUMA","PTOTOCOPILLA","G_CTRL_HE_MELA",\
                    "AGRIGOLA LOMAS PUCALAN","MENORES_ARICA","MENORES_CHAP","LBRCBLANCHILQ","47346_COLINA","|"}

def procesar_reglas_padre_hijo(empresas_faltantes, cache):
    
    configuracion_grupos = [
        {
            "padre_nombre": "CODELCO",
            "padre_rut": "61704000-k",
            "hijos": ["CODELCO","CODELCO A-D.ALMAGRO", "CODELCO A-EL LLANO", "CODELCO A-MAQUI", "CODELCO ANDINA-SALADILLO", "CODELCO CHILE - DIVISION ANDINA", "CODELCO CHILE DIVISION ANDINA", "CODELCO MINEROS", "CODELCO VENTANAS", "DESALADORA_CODELCO", "MIN_CODELCO_SALAR", "MINERA_MINISTRO_HALES_CODELCO", "CHUQUICAMATA", "MIN_RTOMIC", "MINERA_GABY", "EMPRESA NACIONAL DE MINERIA"]
        },
        {
            "padre_nombre": "BHP",
            "padre_rut": "86160300-8",
            "hijos": ["BHP","MINERA_ESCONDIDA", "MINERA_ESCONDIDA_COLOSO1", "MINERA_ESCONDIDA_COLOSO2", "MINERA_SPENCE", "MIN_COLORADO110", "BOMBEO 2", "BOMBEO 3", "BOMBEO 4",  "BOMBEO_AES", "SGO_BOMBEO_CAITAN", "SGO_BOMBEO1_CAITAN", "SGO_BOMBEO2y3_CAITAN", "OGP1", "LAGUNA SECA", "SULFUROS", "PURI", "FARELLONES", "CHIMBORAZO", "OXIDOS"]
        },
        {
            "padre_nombre": "INES DE COLLAHUASI",
            "padre_rut": "89468900-5",
            "hijos": ["INES DE COLLAHUASI","MIN_COLLAHUASI", "COLBUN_COLLAHUASI_CAHUIZA", "Collahuasi Puerto (CLIENTES_TARAP)"]
        },
        {
            "padre_nombre": "ANTOFAGASTA MINERALS",
            "padre_rut": "93920000-2",
            "hijos": ["ANTOFAGASTA MINERALS","MIN. PELAMBRES", "MIN. PELAMBRES-L.VILOS", "MIN. PELAMBRES-L.VILOS JAV", "MIN. PELAMBRES-QUEREO", "MIN. PELAMBRES-QUEREO JAV", "MIN. PELAMBRES-QUILLOTA", "MIN. PELAMBRES-QUILLOTA CON", "MIN. PELAMBRES-QUILLOTA JAV", "MIN. PELAMBRES-VILOS", "MINERA_LOS_PELAMBRES", "MINERA_LOS_PELAMBRES_2", "MINERA_TESORO_CENTINELA", "MINERA ANTUCO SPA",  "MINERA_ANTUCOYA023", "MIN_ZALDIVAR", "MINERA_ESPERANZA", "MINERA_ESPERANZA OXE"]
        },
        {
            "padre_nombre": "ANGLO AMERICAN",
            "padre_rut": "77762940-9",
            "hijos": ["ANGLO AMERICAN","ANGLO AMERICAN SUR SA"]
        },
        {
            "padre_nombre": "TECK RESOURCES",
            "padre_rut": "78127000-8",
            "hijos": ["TECK RESOURCES", "MIN_QBLANCA", "MIN_QBLANCA_II", "MIN_QBL_II_PUQ_CHALL_TIQ", "CIA MINERA TECK CARMEN DE ANDACOLLO", "MIN. C. DE ANDACOLLO"]
        },
        {
            "padre_nombre": "GLENCORE",
            "padre_rut": "78512520-7",
            "hijos": ["GLENCORE","MINERA_LOMAS_BAYAS", "NORANDA"]
        },
        {
            "padre_nombre": "LUNDIN MINING",
            "padre_rut": "76263083-1",
            "hijos": ["LUNDIN MINING","MIN. LA CANDELARIA", "MIN. CASERONES", "MIN. OJOS DEL SALADO"]
        },
        {
            "padre_nombre": "FREEPORT-MCMORAN",
            "padre_rut": "78273180-7",
            "hijos": ["FREEPORT-MCMORAN","MIN_ELABRA"]
        },
        {
            "padre_nombre": "KGHM INTERNACIONAL",
            "padre_rut": "76025837-7",
            "hijos": ["KGHM INTERNACIONAL","SIERRA GORDA_AES", "SIERRA GORDA_COCHRANE", "SCM_SIERRA_GORDA1", "SCM_SIERRA_GORDA2"]
        },
        {
            "padre_nombre": "GRUPO CAP",
            "padre_rut": "91297000-0",
            "hijos": ["GRUPO CAP","CMP PUERTO", "CMP LOS COLORADOS", "CMP CERRO NEGRO NORTE", "CMP ALGARROBO", "CMP MAGNETITA", "CMP PELLETS", "CMP ROMERAL", "CAP_HUACHIPATO"]
        },
        {
            "padre_nombre": "SQM",
            "padre_rut": "93007000-9",
            "hijos": ["SQM", "SQM_SALAR_CARMEN", "SQM_SALAR_URIBE", "PTOTOCOPILLA"]
        },
        {
            "padre_nombre": "CMPC",
            "padre_rut": "90222000-3",
            "hijos": ["CMPC","FORSAC S.A.","AUTOPRODUCTOR CORDILLERA CMPC", "AUTOPRODUCTOR TISSUE CMPC", "C_CTRL_BM_CMPC_LAJA", "C_CTRL_TE_CMPC PACIFICO", "CMPC  TISSUE S.A", "CMPC (MININCO)", "CMPC AGA LAJA", "CMPC CARTULINAS-MAULE", "CMPC CELULOSA", "CMPC CORONEL", "CMPC ERCO", "CMPC INDURA", "CMPC LAJA", "CMPC LOS ANGELES", "CMPC MAD-MININCO", "CMPC MULCHEN", "CMPC PACIFICO", "CMPC PLYWOOD",  "CMPC SANTAFE", "CMPC TISSUE", "CMPC TISSUE S A", "CMPC_TISSUE", "PLANTA CARTULINAS MAULE CMPC", "PLANTA CARTULINAS VALDIVIA CMPC", "PLANTA CHIMOLSA CMPC", "PLANTA TISSUE CMPC", "FORESTAL MININCO SPA"]
        },
        {
            "padre_nombre": "ENGIE",
            "padre_rut": "88006900-4",
            "hijos": ["MUELLE"]
        }
    ]

    mapa_busqueda = {}

    for grupo in configuracion_grupos:
        p_nombre = grupo["padre_nombre"]
        p_rut = grupo["padre_rut"]
        
        for hijo in grupo["hijos"]:
            key_hijo = hijo.strip().upper()
            mapa_busqueda[key_hijo] = {
                "nombre": p_nombre,
                "rut": p_rut
            }

    procesados = 0
    
    for empresa in list(empresas_faltantes):
        empresa_key = empresa.strip().upper()
        
        if empresa_key in mapa_busqueda:
            datos_padre = mapa_busqueda[empresa_key]
            
            info_empresa = {
                "Empresa": empresa,
                "RUTs": [datos_padre["rut"]],
                "nombres_sii": [[datos_padre["nombre"], datos_padre["rut"]]],
                "nombre_mas_probable": datos_padre["nombre"],
                "rut_mas_probable": datos_padre["rut"],
                "origen_dato": "REGLA_PADRE_HIJO"
            }
            
            cache[empresa] = info_empresa
            empresas_faltantes.remove(empresa)
            safe_prent(f" > Match: '{empresa}' es hijo de '{datos_padre['nombre']}'")
            procesados += 1

    if procesados > 0:
        safe_prent(f"Se resolvieron {procesados} empresas mediante agrupación familiar.")
        save_json_cache()
    else:
        safe_prent("No se encontraron coincidencias en las reglas de grupos.")

    return empresas_faltantes

def fix_encoding(nombre):
    replacements = {
        "Â": "",
        "Ã‘": "Ñ",
        "Ã¡": "á", "Ã©": "e", "Ã­": "í", "Ã³": "ó", "Ãº": "ú", 
        "Ã¼": "ü", "Â¿": "¿", "Â¡": "¡"
    }
    for wrong, correct in replacements.items():
        nombre = nombre.replace(wrong, correct)
    fixed = nombre.strip()
    return fixed

def check_encoding_issues_in_cache(cache):
    safe_prent("\nEmpresas en cache con posibles problemas de encoding:")
    problemas = False
    replacements = {
        "Â": "", "Ã‘": "Ñ", "Ã¡": "á", "Ã©": "e", "Ã­": "í", 
        "Ã³": "ó", "Ãº": "ú", "Ã¼": "ü", "Â¿": "¿", "Â¡": "¡"
    }
    for empresa in cache:
        if any(error in empresa for error in replacements.keys()):  
            safe_prent(f" - {empresa}")
            problemas = True
    if not problemas:
        safe_prent("No se detectaron problemas de encoding en las claves del cache.")

def show_new_and_low_similarity(new_entries, cache):
    resultado = []  
    safe_prent("\nÚltimos registros agregados al cache (nuevas empresas):")
    for empresa in new_entries:
         safe_prent(f" - {empresa}")
    
    similarity_list = []
    for empresa in new_entries:
         data = cache.get(empresa, {})
         nombre_mp = data.get("nombre_mas_probable", "")
         score = fuzz.ratio(empresa.upper(), nombre_mp.upper()) if nombre_mp else 0
         similarity_list.append((empresa, nombre_mp, score))
    
    similarity_list = sorted(similarity_list, key=lambda x: x[2])
    resultado.append("\nRegistros con peores porcentajes de similitud entre 'Empresa' y 'nombre_mas_probable':")
    for empresa, nombre_mp, score in similarity_list:
         resultado.append(f" - Empresa: {empresa}, Nombre SII: {nombre_mp}, Similaridad: {score}%")
    return "\n".join(resultado) if resultado else "No hay nuevas empresas con baja similitud."

def load_json_cache():
    global cache_ruts_empresas
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding="utf-8") as file:
            cache_ruts_empresas = json.load(file)
        safe_prent(f"Cache cargada desde '{CACHE_FILE}' con exito.")
    else:
        with open(CACHE_FILE, 'w', encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        safe_prent(f"Archivo de cache '{CACHE_FILE}' no encontrado. Se creó un archivo vacío.")
        cache_ruts_empresas = {}

def save_json_cache(CACHE_FILE):
    with open(CACHE_FILE, 'w', encoding="utf-8") as file:
        json.dump(cache_ruts_empresas, file, ensure_ascii=False, indent=4)
    print(f"Cache guardada en '{CACHE_FILE}' con exito.")

def verify_in_cache(empresa, cache, resultados_empresas, empresas_faltantes):
    if empresa in cache:
        info = cache[empresa]
        if info and isinstance(info, dict):
            if info.get("RUTs") and len(info.get("RUTs")) > 0:
                resultados_empresas.append(info)
                safe_prent(f"El RUT de la empresa '{empresa}' ya está en el cache.")
                empresas_encontradas.append(empresa)
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
                return True
    return False

def normalizar_rut(rut):
    return re.sub(r'\.', '', rut)

def obtener_nombres_sii(ruts_encontrados, df_sii):
    if not {'RUT', 'RAZON SOCIAL'}.issubset(df_sii.columns):
        raise ValueError("El DataFrame debe contener las columnas 'RUT' y 'RAZON SOCIAL'")
    
    ruts_norm = {normalizar_rut(rut) for rut in ruts_encontrados}
    df_sii['RUT_NORMALIZADO'] = df_sii['RUT'].apply(normalizar_rut)
    df_filtrado = df_sii[df_sii['RUT_NORMALIZADO'].isin(ruts_norm)]
    nombres_ruts = list(zip(df_filtrado['RAZON SOCIAL'], df_filtrado['RUT']))
    return nombres_ruts

def fuzzy_nombre_mas_probable(nombre_original, posibles_nombres_ruts):
    if not posibles_nombres_ruts:
        return "", ""
    nombres, ruts = zip(*posibles_nombres_ruts)
    if nombre_original != "COMISION PARA EL MERCADO FINANCIERO":
        candidatos_filtrados = [(n, r) for n, r in zip(nombres, ruts) if n != "COMISION PARA EL MERCADO FINANANCIERO"]
    else:
        candidatos_filtrados = list(posibles_nombres_ruts)
    if not candidatos_filtrados:
        return "", ""
    nombres_filtrados, ruts_filtrados = zip(*candidatos_filtrados)
    mejor_match = process.extractOne(nombre_original, nombres_filtrados)
    if mejor_match:
        nombre_probable = mejor_match[0]
        indice = nombres_filtrados.index(nombre_probable)
        return nombre_probable, ruts_filtrados[indice]
    return "", ""

def check_cache_similarity(empresa, cache):
    best_match = None
    best_score = 0
    for key, data in cache.items():
        nombre_prob = data.get("nombre_mas_probable", "")
        rut_prob = data.get("rut_mas_probable", "")
        if nombre_prob:
            score = fuzz.ratio(empresa.upper(), nombre_prob.upper())
            if score > best_score:
                best_score = score
                best_match = data
    if best_match and best_score >= 90:
        return best_match.get("nombre_mas_probable", ""), best_match.get("rut_mas_probable", ""), best_score
    return "", "", best_score

def fetch_url_with_ua_random(url):
    ua = UserAgent()
    headers = {
         "User-Agent": ua.random, 
         "Accept-Language": "es-ES,es;q=0.9,en;q=0.8", 
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", 
         "Referer": "https://www.google.com/"
    }
    response = requests.get(url, headers=headers, timeout=10)
    return response

def multiple_request_for_url(url, n_intentos, headers):
    for _ in range(n_intentos):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                safe_prent("Status 200")
                return response
            elif response.status_code in [429, 403]:
                safe_prent(f"Error {response.status_code}: Intentando con User-Agent alternativo...")
                alt_response = fetch_url_with_ua_random(url)
                if alt_response.status_code == 200:
                    safe_prent("User-Agent alternativo funcionó (status 200).")
                    return alt_response
            else:
                safe_prent(f"Error al acceder (status {response.status_code}).")
        except requests.exceptions.ConnectionError:
            safe_prent("Error de conexión, esperando...")
            time.sleep(0.1)
    return None

def extract_ruts_from_html(html_text):
    safe_prent("Extrayendo RUTs del HTML...")
    soup = BeautifulSoup(html_text, 'html.parser')
    rut_pattern = re.compile(r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9Kk]\b', re.IGNORECASE)
    rut_pattern_without_dots = re.compile(r'\b\d{7,8}-[0-9Kk]\b', re.IGNORECASE)
    unique_ruts = set()
    tags_to_search = ["span", "div", "p", "li", "strong", "em"]
    for tag in tags_to_search:
        elements = soup.find_all(tag)
        for element in elements:
            text = element.get_text()
            posibles = rut_pattern.findall(text)
            posibles2 = rut_pattern_without_dots.findall(text)
            for rut in posibles:
                unique_ruts.add(rut)
            for rut in posibles2:
                unique_ruts.add(rut)
    if len(unique_ruts) == 0:
        safe_prent("No se han encontrado RUTs en el HTML.")
    return list(unique_ruts)

def load_sii_data():
    try:
        df_sii_fiscales = pd.read_csv(
            os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_fiscales.csv"),
            encoding="latin1",
            delimiter=';',
            on_bad_lines='skip'
        )[["RUT", "RAZON SOCIAL"]]

        df_sii_noPyme = pd.read_csv(
            os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_nomipyme.csv"),
            encoding="latin1",
            delimiter=';',
            on_bad_lines='skip'
        )[["RUT", "RAZON SOCIAL"]]

        df_sii_Pyme = pd.read_csv(
            os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_mipyme.csv"),
            encoding="latin1",
            delimiter=';',
            on_bad_lines='skip'
        )[["RUT", "RAZON SOCIAL"]]

        df_sii = pd.concat([df_sii_fiscales, df_sii_noPyme, df_sii_Pyme], ignore_index=True)
        return df_sii
    except Exception as e:
        safe_prent("Error al cargar datos SII:", e)
        return None

def buscar_rut_empresas(empresas, n_intentos, max_intentos=3,empresas_no_scrape=None):
    if empresas_no_scrape is None:
        empresas_no_scrape = set()

    load_json_cache()
    
    # Pre-barrido rapido
    empresas_faltantes = set(empresas)
    for emp in empresas_faltantes.copy():
        if emp in cache_ruts_empresas:
            info = cache_ruts_empresas[emp]
            if info.get("RUTs") or info.get("no_scrape"):
                empresas_faltantes.remove(emp)
    if empresas_faltantes:
        procesar_reglas_padre_hijo(empresas_faltantes, cache_ruts_empresas)
    
    df_sii = None
    if empresas_faltantes:
        safe_prent(f"Hay {len(empresas_faltantes)} empresas nuevas. Cargando BBDD del SII...")
        df_sii = load_sii_data()
        if df_sii is None:
            safe_prent("No se pudo cargar la base de datos del SII. Saltando búsqueda avanzada.")
            return [], list(empresas_faltantes)
    else:
        safe_prent("Todas las empresas están en caché. Saltando carga de SII y Web Scraping.")

    resultados_empresas = []
    
    while empresas_faltantes and n_intentos < max_intentos:
        for empresa in tqdm(list(empresas_faltantes), desc=f"Intento {n_intentos+1}"):
            if empresa in cache_ruts_empresas:
                cached_data = cache_ruts_empresas[empresa]
                if cached_data.get("nombre_mas_probable", "") == "" and cached_data.get("rut_mas_probable", "") == "":
                    if empresa in empresas_no_scrape or cached_data.get("no_scrape", False):
                        safe_prent(f"La empresa '{empresa}' tiene datos vacíos y está marcada para no hacer web scraping. Se omite.")
                    
                        empresas_faltantes.remove(empresa)
                        continue

            if verify_in_cache(empresa, cache_ruts_empresas, resultados_empresas, empresas_faltantes):
                continue

            nombre_sim, rut_sim, similitud = check_cache_similarity(empresa, cache_ruts_empresas)
            if nombre_sim and rut_sim:
                safe_prent(f"Encontrado match en cache para '{empresa}': '{nombre_sim}' con {similitud}% de similitud.")
                info_empresa = {
                    "Empresa": empresa,
                    "RUTs": [],
                    "nombres_sii": [[nombre_sim, rut_sim]],
                    "nombre_mas_probable": nombre_sim,
                    "rut_mas_probable": rut_sim,
                    "similitud": similitud
                }
                cache_ruts_empresas[empresa] = info_empresa
                save_json_cache()
                resultados_empresas.append(info_empresa)
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
                continue

            safe_prent(f"\nBuscando RUT para: {empresa}")
            time.sleep(0.1)
            ruts_encontrados = []
            for search_url in search_engines:
                url = search_url.format(query=empresa.replace(' ', '+'))
                safe_prent(f"Intentando con URL: {url}")
                headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
                }
                response = multiple_request_for_url(url, 3, headers)
                if response and response.status_code == 200:
                    posibles_ruts = extract_ruts_from_html(response.text)
                    if posibles_ruts:
                        safe_prent(f"RUTs encontrados para '{empresa}': {posibles_ruts}")
                        ruts_encontrados.extend(posibles_ruts)
                    if ruts_encontrados:
                        break

            if ruts_encontrados:
                lista_nombres_sii = obtener_nombres_sii(ruts_encontrados, df_sii)
                nombre_probable, rut_probable = fuzzy_nombre_mas_probable(empresa, lista_nombres_sii)
                info_empresa = {
                    "Empresa": empresa,
                    "RUTs": ruts_encontrados,
                    "nombres_sii": lista_nombres_sii,
                    "nombre_mas_probable": nombre_probable,
                    "rut_mas_probable": rut_probable
                }
                cache_ruts_empresas[empresa] = info_empresa
                save_json_cache()
                resultados_empresas.append(info_empresa)
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
            else:
                if empresa in empresas_no_scrape:
                    info_empresa = {
                        "Empresa": empresa,
                        "RUTs": [],
                        "nombres_sii": [],
                        "nombre_mas_probable": "",
                        "rut_mas_probable": "",
                        "no_scrape": True 
                    }
                    cache_ruts_empresas[empresa] = info_empresa
                    save_json_cache()
                    safe_prent(f"La empresa '{empresa}' se marca como no hacer web scraping.")
                else:
                    info_empresa = {
                        "Empresa": empresa,
                        "RUTs": [],
                        "nombres_sii": [],
                        "nombre_mas_probable": "",
                        "rut_mas_probable": ""
                    }
                    cache_ruts_empresas[empresa] = info_empresa
                    save_json_cache()
        
        if empresas_faltantes:
            safe_prent(f"Intento {n_intentos+1} finalizado. Empresas restantes: {len(empresas_faltantes)}")
            n_intentos += 1

    safe_prent("### Intentos terminados ###")
    if empresas_faltantes:
        safe_prent("Empresas sin RUT encontrado tras los intentos:")
        for empresa in empresas_faltantes:
            safe_prent(empresa)
    save_json_cache()
    return resultados_empresas, list(empresas_faltantes)

def cargar_csvs(*csv_paths, delimiter=';'):
    csv.field_size_limit(10**6)  
    data = []
    for csv_path in csv_paths:
        with open(csv_path, mode="r", encoding="latin-1") as f:
            csv_reader = csv.DictReader(f, delimiter=delimiter)
            for row in csv_reader:
                data.append(row)
    return data

def buscar_top_3_razon_social(data, nombre_a_buscar):
    razones_sociales = [(row["RAZON SOCIAL"], row["RUT"]) for row in data]
    mejores = process.extract(nombre_a_buscar, [rs[0] for rs in razones_sociales], scorer=fuzz.WRatio, limit=3)
    resultados = []
    for match_str, score, index in mejores:
        rut_asociado = razones_sociales[index][1]
        resultados.append({
            "RUT": rut_asociado,
            "RAZON SOCIAL": match_str,
            "PUNTUACION": score
        })
    return resultados

def buscar_en_SII(nombre_a_buscar, cache):
    csv1=os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_nomipyme.csv")
    csv2=os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_mipyme.csv")
    csv3=os.path.join(rutas_config.DIRECTORIO_DATA,"bbdd del sii","ee_empresas_fiscales.csv")
    data_unificada = cargar_csvs(csv1, csv2, csv3)
    top_3 = buscar_top_3_razon_social(data_unificada, nombre_a_buscar)
    safe_prent(f"Top 3 coincidencias para '{nombre_a_buscar}':")
    for item in top_3:
        safe_prent(f" - RUT: {item['RUT']}, RAZON SOCIAL: {item['RAZON SOCIAL']}, score: {item['PUNTUACION']}")
    ruts = [item["RUT"] for item in top_3]
    nombres_sii = [[item["RAZON SOCIAL"], item["RUT"]] for item in top_3]
    nombre_mas_probable = top_3[0]["RAZON SOCIAL"]
    rut_mas_probable = top_3[0]["RUT"]
    cache[nombre_a_buscar] = {
        "Empresa": nombre_a_buscar,
        "RUTs": ruts,
        "nombres_sii": nombres_sii,
        "nombre_mas_probable": nombre_mas_probable,
        "rut_mas_probable": rut_mas_probable
    }
    safe_prent(f"Datos de '{nombre_a_buscar}' actualizados mediante deep search.")
    save_json_cache()

def run_deep_search_for_missing(cache):
    missing = [empresa for empresa, data in cache.items() if not data.get("rut_mas_probable") and empresa not in empresas_no_scrape]
    if missing:
        safe_prent("Ejecutando deep search para las empresas faltantes...")
        for empresa in missing:
            safe_prent(f"Deep search para: {empresa}")
            buscar_en_SII(empresa, cache)

def optimize_cache_duplicates(cache):
    safe_prent("Iniciando optimización de duplicados en el cache...")
    group_by_rut = {}
    for key, data in cache.items():
        rut = data.get("rut_mas_probable", "")
        if rut:
            group_by_rut.setdefault(rut, []).append((key, data))
            
    for rut, entries in group_by_rut.items():
        if len(entries) > 1:
            freq = {}
            for key, data in entries:
                nombre = data.get("nombre_mas_probable", "")
                if nombre:
                    freq[nombre] = freq.get(nombre, 0) + 1
            if freq:
                nombre_common = max(freq, key=freq.get)
                common_count = freq[nombre_common]
                
                # --- CORRECCION AQUI: Se agrego el bucle for ---
                for key, data in entries:
                    nombre_actual = data.get("nombre_mas_probable", "")
                    if nombre_actual != nombre_common:
                        similarity = fuzz.ratio(nombre_common.upper(), nombre_actual.upper())
                        entry_count = freq.get(nombre_actual, 0)
                        if entry_count == 0:
                            continue
                        ratio = common_count / entry_count
                        if ratio > 5 and similarity >= 80:
                            safe_prent(f"Optimizando: '{nombre_actual}' se homologará a '{nombre_common}' (similitud: {similarity}%, ratio: {ratio:.2f})")
                            cache[key]["nombre_mas_probable"] = nombre_common
                            cache[key]["rut_mas_probable"] = rut
    save_json_cache()

def guardar_datos_en_csv(data, filename=os.path.join(rutas_config.DIRECTORIO_RESULTADOS, "CompiladoEmpresasConRUT.csv")):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            safe_prent("Error al decodificar JSON:", e)
            return
    with open(filename, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Subdivision", "Empresa", "RUT"])
        
        for key, value in data.items():
            empresa = value.get("Empresa", "").strip()
            nombre_mas_probable = value.get("nombre_mas_probable", "").strip()
            rut_mas_probable = value.get("rut_mas_probable", "").strip()
            
            if nombre_mas_probable or rut_mas_probable:  
                writer.writerow([empresa, nombre_mas_probable, rut_mas_probable])

    safe_prent(f"Archivo CSV generado exitosamente: {filename}")

sub_log_path=os.path.join(rutas_config.DIRECTORIO_LOGS, "sub_log_retiros.log")
def log_sub_message(message):
    with open(sub_log_path, "a") as log:
        log.write(f"{datetime.datetime.now()} - {message}\n")

if __name__ == "__main__":
    #load_json_cache() 
    #old_cache_keys = set(cache_ruts_empresas.keys())
    ###check_encoding_issues_in_cache(cache_ruts_empresas)


    #empresas = retiros_combined.dropna().drop_duplicates().tolist()
    #empresas = [fix_encoding(e) for e in empresas]
    #empresas_sin_rut = empresas.copy()
    #n_intentos = 0

    resultados, faltantes = buscar_rut_empresas(empresas, n_intentos, max_intentos=3)
    
    run_deep_search_for_missing(cache_ruts_empresas)
    
    optimize_cache_duplicates(cache_ruts_empresas)

    guardar_datos_en_csv(cache_ruts_empresas)
    
    df_ruts = pd.read_csv(csv_RUTS, sep=',')
    df_ruts = df_ruts.drop_duplicates()
    sys.path.append(os.path.join(DBUTIL, "src SQL"))
    from db_utils_V2 import subir_df_sql_overwrite
    subir_df_sql_overwrite(df_ruts,"EmpresaSubdivision")
    
    safe_prent(f"\nTotal de empresas procesadas: {len(cache_ruts_empresas)}")

    new_entries = set(cache_ruts_empresas.keys()) - old_cache_keys
    if new_entries:
        message=show_new_and_low_similarity(new_entries, cache_ruts_empresas)
        lines = message.split("\n")
        if len(lines) > 30: 
            summary = "\n".join(lines[:30])  
            summary += f"\n... y {len(lines) - 30} empresas más."
            log_sub_message(summary)
        else:
            log_sub_message(message)  
    else:
        log_sub_message("No se agregaron nuevos registros al cache en esta ejecucion.")