import pandas as pd
import funciones
import rutas_config
import os
import logging
import json
from tqdm import tqdm
import time
import random
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
from rapidfuzz import process, fuzz
import csv
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cache_folder = rutas_config.DIRECTORIO_CACHE
resultados_folder = rutas_config.DIRECTORIO_RESULTADOS
cache_file = os.path.join(cache_folder, 'cache_ruts_empresas.json')
csv_ruts = pd.read_csv(os.path.join(cache_folder, 'CompiladoEmpresasConRUT.csv'), sep = ';')
base_sii = rutas_config.DIRECTORIO_sii

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

search_engines = [
    "https://www.google.com/search?q={query}+RUT+empresa+Chile",
    "https://www.portalchile.org/search?q={query}+RUT+empresa+Chile",
    "https://www.bing.com/search?q={query}+RUT+empresa+Chile",
    "https://search.yahoo.com/search?p={query}+RUT+empresa+Chile",
    "https://duckduckgo.com/?q={query}+RUT+empresa+Chile"
]
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

def ACTUALIZAR_SII(ruta_carpeta_destino):
    url_objetivo = "https://www.sii.cl/sobre_el_sii/nominapersonasjuridicas.html"
    
    conexion = funciones.establecer_conexion(url_objetivo)
    
    if conexion:
        url_del_zip = funciones.buscar_enlace_especifico(conexion, url_objetivo, "PUB_NOMBRES_PJ.zip")
        
        if url_del_zip:
            ruta_del_archivo_descargado = funciones.descargar_archivo(url_del_zip, "BaseSII.zip", ruta_carpeta_destino)
            
            if ruta_del_archivo_descargado:
                extraccion_exitosa = funciones.extraer_y_eliminar_zip(ruta_del_archivo_descargado, ruta_carpeta_destino)
                
                if extraccion_exitosa:
                    archivos_en_carpeta = os.listdir(ruta_carpeta_destino)
                    ruta_txt = None
                    
                    for nombre_archivo in archivos_en_carpeta:
                        if nombre_archivo.endswith('.txt') and 'PUB_NOMBRES_PJ' in nombre_archivo:
                            ruta_txt = os.path.join(ruta_carpeta_destino, nombre_archivo)
                            break
                    
                    if ruta_txt:
                        ruta_parquet = os.path.join(ruta_carpeta_destino, "BaseSII.parquet")
                        logging.info(ruta_txt)
                        transformacion_exitosa = funciones.transformar_txt_a_parquet(ruta_txt, ruta_parquet)
                        
                        if transformacion_exitosa:
                            logging.info("\nLimpiando carpeta")
                            
                            for elemento in os.listdir(ruta_carpeta_destino):
                                ruta_elemento = os.path.join(ruta_carpeta_destino, elemento)
                                
                                if not elemento.endswith('.parquet'):
                                    try:
                                        if os.path.isfile(ruta_elemento):
                                            os.remove(ruta_elemento)
                                        elif os.path.isdir(ruta_elemento):
                                            shutil.rmtree(ruta_elemento)
                                    except Exception as e:
                                        logging.error(f"No se pudo eliminar {elemento}: {e}")
                    else:
                        logging.error("ERROR: No se encontro el archivo txt despues de descomprimir")

def obtener_nuevos_registros_de_empresas(resultados_folder):

    archivos_resultado = os.listdir(resultados_folder)

    archivo_mas_reciente_R = None
    archivo_mas_reciente_LeT = None
    archivo_mas_reciente_LeD = None

    fecha_mas_reciente_R = (0, 0)
    fecha_mas_reciente_LeT = (0, 0)
    fecha_mas_reciente_LeD = (0, 0)

    for file in archivos_resultado:
        if file.startswith("mensual_retiros_tipo_R"):
            anio, mes = funciones.extraer_anio_mes_de_nombre_iny(file)

            if anio is not None and mes is not None:
                fecha_actual = (anio, mes)
                
                if fecha_actual > fecha_mas_reciente_R:
                    fecha_mas_reciente_R = fecha_actual 
                    archivo_mas_reciente_R = file
        elif file.startswith("mensual_retiros_tipo_LeT"):
            anio, mes = funciones.extraer_anio_mes_de_nombre_iny(file)

            if anio is not None and mes is not None:
                fecha_actual = (anio, mes)
                
                if fecha_actual > fecha_mas_reciente_LeT:
                    fecha_mas_reciente_LeT = fecha_actual 
                    archivo_mas_reciente_LeT = file
        elif file.startswith("mensual_retiros_tipo_LeD"):
            anio, mes = funciones.extraer_anio_mes_de_nombre_iny(file)

            if anio is not None and mes is not None:
                fecha_actual = (anio, mes)
                
                if fecha_actual > fecha_mas_reciente_LeD:
                    fecha_mas_reciente_LeD = fecha_actual 
                    archivo_mas_reciente_LeD = file

    df_Retiros_R = pd.read_parquet((os.path.join(resultados_folder,archivo_mas_reciente_R)), columns = ['Retiro'])['Retiro'].unique()
    df_Retiros_LeT = pd.read_parquet((os.path.join(resultados_folder,archivo_mas_reciente_LeT)), columns = ['Retiro'])['Retiro'].unique()
    df_Retiros_LeD = pd.read_parquet((os.path.join(resultados_folder,archivo_mas_reciente_LeD)), columns = ['Retiro'])['Retiro'].unique()

    todos_los_retiros_unicos = list(set(df_Retiros_R) | set(df_Retiros_LeT) | set(df_Retiros_LeD))

    df_retiros_combinados = pd.DataFrame(todos_los_retiros_unicos, columns=['Retiro'])
    df_retiros_combinados = df_retiros_combinados['Retiro'].dropna().drop_duplicates().tolist()

    return df_retiros_combinados

def load_json_cache(CACHE_FILE):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding="utf-8") as file:
            cache_ruts_empresas = json.load(file)
        logging.info(f"Cache cargada desde '{CACHE_FILE}' con exito.")
    else:
        with open(CACHE_FILE, 'w', encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        logging.info(f"Archivo de cache '{CACHE_FILE}' no encontrado. Se creó un archivo vacío.")
        cache_ruts_empresas = {}
    return cache_ruts_empresas

def fix_encoding(nombre):
    replacements = {
        "Ã‘": "Ñ",
        "Ã¡": "á", 
        "Ã©": "é",
        "Ã­": "í", 
        "Ã³": "ó", 
        "Ãº": "ú", 
        "Ã¼": "ü", 
        "Â¿": "¿", 
        "Â¡": "¡",
        "Â": "" 
    }
    
    if not isinstance(nombre, str):
        return nombre
        
    for wrong, correct in replacements.items():
        nombre = nombre.replace(wrong, correct)
        
    return nombre.strip()

def save_json_cache(cache_data, CACHE_FILE):
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            with open(CACHE_FILE, 'w', encoding="utf-8") as file:
                json.dump(cache_data, file, ensure_ascii=False, indent=4)
            return 
        except PermissionError:
            intentos += 1
            logging.warning(f"El archivo está bloqueado por otro programa (Intento {intentos}/{max_intentos}). Esperando 2 segundos...")
            time.sleep(2)

def procesar_reglas_padre_hijo(empresas_faltantes, cache, CACHE_FILE):
    
    configuracion_grupos = [
        {
            "padre_nombre": "CODELCO",
            "padre_rut": "61704000-k",
            "hijos": ["CODELCO","CODELCO A-D.ALMAGRO", "CODELCO A-EL LLANO", "CODELCO A-MAQUI", "CODELCO ANDINA-SALADILLO", "CODELCO CHILE - DIVISION ANDINA", "CODELCO CHILE DIVISION ANDINA", "CODELCO MINEROS", "CODELCO VENTANAS", "DESALADORA_CODELCO", "MIN_CODELCO_SALAR", "MINERA_MINISTRO_HALES_CODELCO", "CHUQUICAMATA", "MIN_RTOMIC", "MINERA_GABY",
            "EMPRESA NACIONAL DE MINERIA", "CODELCO A-EL LLANO_GME", "CODELCO A-EL LLANO", "CODELCO3", "MINERA_GABY_GME", "CHUQUIA1_GME",
            "CODELCO VENTANAS_GME", "GR_P_L.MAQU", "GR_P_MAITEN", "CODELCO_MINERO_110_GR_POWER", "CODELCO MINEROS_GME", "MINERA_MINISTRO_HALES_CODELCO_GME", "MIN_RTOMIC_GME",
            "GR_P_R.TOMI", "CODELCO ANDINA-SALADILLO_GME", "GR_P_SALADI" , "GR_P_1_SALAR", "MIN_CODELCO_SALAR_110_GME","CODELCO_DCH",
            "MIN_CODELCO_SALAR_220_GME", "GR_P_SALAR", "TCHITACK_GME", "GR_P_TCHITA", "CODELCO CDTAMAYA_GME", "GR_P_CD.TAM", "CODELCO_DRT",
            "CHUQUIA1_GME", "GR_P_D.ALMA", "GR_P_EL.LLA" ,"GR_P_ELCOBR", "GR_P1_CHUQUI", "GR_P_CHUQUI"
            ]
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
            "hijos": ["CMPC","FORSAC S.A.","AUTOPRODUCTOR CORDILLERA CMPC", "AUTOPRODUCTOR TISSUE CMPC", "C_CTRL_BM_CMPC_LAJA", "C_CTRL_TE_CMPC PACIFICO", "CMPC  TISSUE S.A", "CMPC (MININCO)", "CMPC AGA LAJA", "CMPC CARTULINAS-MAULE", "CMPC CELULOSA", "CMPC CORONEL", "CMPC ERCO", "CMPC INDURA", "CMPC LAJA", "CMPC LOS ANGELES", "CMPC MAD-MININCO", "CMPC MULCHEN", "CMPC PACIFICO", "CMPC PLYWOOD",  "CMPC SANTAFE", "CMPC TISSUE", "CMPC TISSUE S A", "CMPC_TISSUE", "PLANTA CARTULINAS MAULE CMPC", "PLANTA CARTULINAS VALDIVIA CMPC", "PLANTA CHIMOLSA CMPC", "PLANTA TISSUE CMPC", "FORESTAL MININCO SPA",
            "CMPC LAJA"
            ]
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
            logging.info(f" > Match: '{empresa}' es hijo de '{datos_padre['nombre']}'")
            procesados += 1

    if procesados > 0:
        logging.info(f"Se resolvieron {procesados} empresas mediante agrupación familiar.")
        save_json_cache(cache_ruts_empresas,CACHE_FILE)
    else:
        logging.info("No se encontraron coincidencias en las reglas de grupos.")

    return empresas_faltantes

def load_sii_data():
    try:
        df_sii = pd.read_parquet(
        os.path.join(rutas_config.DIRECTORIO_sii, "BaseSII.parquet"),
        columns=["RUT", "RAZON_SOCIAL"]
        )
        return df_sii
    except Exception as e:
        logging.info("Error al cargar datos SII:", e)
        return None

def verify_in_cache(empresa, cache, resultados_empresas, empresas_faltantes):
    if empresa in cache:
        info = cache[empresa]
        if info and isinstance(info, dict):
            if info.get("RUTs") and len(info.get("RUTs")) > 0:
                resultados_empresas.append(info)
                logging.info(f"El RUT de la empresa '{empresa}' ya está en el cache.")
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
                return True
    return False

def check_cache_similarity(empresa, cache):
    if not isinstance(empresa, str) or not empresa.strip():
        return "", "", 0

    best_match = None
    best_score = 0
    empresa_upper = empresa.upper()
    
    for key, data in cache.items():
        nombre_prob = data.get("nombre_mas_probable", "")
        
        if nombre_prob:
            score = fuzz.ratio(empresa_upper, nombre_prob.upper())
            
            if score > best_score:
                best_score = score
                best_match = data
                
            if best_score == 100:
                break
                
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
                logging.info("Status 200")
                return response
            elif response.status_code in [429, 403]:
                logging.info(f"Error {response.status_code}: Intentando con User-Agent alternativo...")
                alt_response = fetch_url_with_ua_random(url)
                if alt_response.status_code == 200:
                    logging.info("User-Agent alternativo funcionó (status 200).")
                    return alt_response
            else:
                logging.info(f"Error al acceder (status {response.status_code}).")
        except requests.exceptions.ConnectionError:
            logging.info("Error de conexión, esperando...")
            time.sleep(0.1)
    return None

def extract_ruts_from_html(html_text):
    logging.info("Extrayendo RUTs del HTML...")
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
        logging.info("No se han encontrado RUTs en el HTML.")
    return list(unique_ruts)

def obtener_nombres_sii(ruts_encontrados, df_sii):
    if not {'RUT', 'RAZON_SOCIAL'}.issubset(df_sii.columns):
        raise ValueError("El DataFrame debe contener las columnas 'RUT' y 'RAZON SOCIAL'")
    
    ruts_norm = {normalizar_rut(rut) for rut in ruts_encontrados}
    df_sii['RUT_NORMALIZADO'] = df_sii['RUT'].apply(normalizar_rut)
    df_filtrado = df_sii[df_sii['RUT_NORMALIZADO'].isin(ruts_norm)]
    nombres_ruts = list(zip(df_filtrado['RAZON_SOCIAL'], df_filtrado['RUT']))
    return nombres_ruts

def normalizar_rut(rut):
    return re.sub(r'\.', '', rut)

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

def buscar_rut_empresas(CACHE_FILE,empresas, n_intentos, max_intentos=3,empresas_no_scrape=None):

    empresas_faltantes = set(empresas)
    for emp in empresas_faltantes.copy():
        if emp in cache_ruts_empresas:
            info = cache_ruts_empresas[emp]
            if info.get("RUTs"):
                empresas_faltantes.remove(emp)
    if empresas_faltantes:
        procesar_reglas_padre_hijo(empresas_faltantes, cache_ruts_empresas, CACHE_FILE)
    
    df_sii = None
    if empresas_faltantes:
        logging.info(f"Hay {len(empresas_faltantes)} empresas nuevas. Cargando BBDD del SII")
        df_sii = load_sii_data()
        if df_sii is None:
            logging.info("No se pudo cargar la base de datos del SII. Saltando búsqueda avanzada.")
            return [], list(empresas_faltantes)
    else:
        logging.info("Todas las empresas estan en cache. Saltando carga de SII y Web Scraping.")

    resultados_empresas = []
    
    while empresas_faltantes and n_intentos < max_intentos:
        for empresa in tqdm(list(empresas_faltantes), desc=f"Intento {n_intentos+1}"):

            if verify_in_cache(empresa, cache_ruts_empresas, resultados_empresas, empresas_faltantes):
                continue

            nombre_sim, rut_sim, similitud = check_cache_similarity(empresa, cache_ruts_empresas)
            if nombre_sim and rut_sim:
                logging.info(f"Encontrado match en cache para '{empresa}': '{nombre_sim}' con {similitud}% de similitud.")
                info_empresa = {
                    "Empresa": empresa,
                    "RUTs": [],
                    "nombres_sii": [[nombre_sim, rut_sim]],
                    "nombre_mas_probable": nombre_sim,
                    "rut_mas_probable": rut_sim,
                    "similitud": similitud
                }
                cache_ruts_empresas[empresa] = info_empresa
                save_json_cache(cache_ruts_empresas,CACHE_FILE)
                resultados_empresas.append(info_empresa)
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
                continue

            logging.info(f"Buscando RUT para: {empresa}")
            time.sleep(0.1)
            ruts_encontrados = []
            for search_url in search_engines:
                url = search_url.format(query=empresa.replace(' ', '+'))
                logging.info(f"Intentando con URL: {url}")
                headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
                }
                response = multiple_request_for_url(url, 3, headers)
                if response and response.status_code == 200:
                    posibles_ruts = extract_ruts_from_html(response.text)
                    if posibles_ruts:
                        logging.info(f"RUTs encontrados para '{empresa}': {posibles_ruts}")
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
                save_json_cache(cache_ruts_empresas,CACHE_FILE)
                resultados_empresas.append(info_empresa)
                if empresa in empresas_faltantes:
                    empresas_faltantes.remove(empresa)
            else:
                if empresas_no_scrape is not None and empresa in empresas_no_scrape:
                    info_empresa = {
                        "Empresa": empresa,
                        "RUTs": [],
                        "nombres_sii": [],
                        "nombre_mas_probable": "",
                        "rut_mas_probable": "",
                        "no_scrape": True 
                    }
                    cache_ruts_empresas[empresa] = info_empresa
                    save_json_cache(cache_ruts_empresas,CACHE_FILE)
                    logging.info(f"La empresa '{empresa}' se marca como no hacer web scraping.")
                else:
                    info_empresa = {
                        "Empresa": empresa,
                        "RUTs": [],
                        "nombres_sii": [],
                        "nombre_mas_probable": "",
                        "rut_mas_probable": ""
                    }
                    cache_ruts_empresas[empresa] = info_empresa
                    save_json_cache(cache_ruts_empresas,CACHE_FILE)
        
        if empresas_faltantes:
            logging.info(f"Intento {n_intentos+1} finalizado. Empresas restantes: {len(empresas_faltantes)}")
            n_intentos += 1

    logging.info("### Intentos terminados ###")
    if empresas_faltantes:
        logging.info("Empresas sin RUT encontrado tras los intentos:")
        for empresa in empresas_faltantes:
            logging.info(empresa)
    save_json_cache(cache_ruts_empresas,CACHE_FILE)
    return resultados_empresas, list(empresas_faltantes)

def buscar_top_3_razon_social(df_sii, nombre_a_buscar):
    if df_sii is None or df_sii.empty: 
        return []
    
    razones_lista = df_sii['RAZON_SOCIAL'].tolist()
    
    mejores = process.extract(nombre_a_buscar, razones_lista, scorer=fuzz.WRatio, limit=3)
    
    resultados = []
    for match_str, score, index in mejores:
        rut_asociado = df_sii.iloc[index]['RUT']
        
        resultados.append({
            "RUT": rut_asociado, 
            "RAZON_SOCIAL": match_str, 
            "PUNTUACION": score
        })
        
    return resultados

def buscar_en_SII(nombre_a_buscar, cache, CACHE_FILE):
    df_sii = load_sii_data()
    top_3 = buscar_top_3_razon_social(df_sii, nombre_a_buscar)
    logging.info(f"Top 3 coincidencias para '{nombre_a_buscar}':")
    ruts = [item["RUT"] for item in top_3]
    nombres_sii = [[item["RAZON_SOCIAL"], item["RUT"]] for item in top_3]
    nombre_mas_probable = top_3[0]["RAZON_SOCIAL"]
    rut_mas_probable = top_3[0]["RUT"]
    cache[nombre_a_buscar] = {
        "Empresa": nombre_a_buscar,
        "RUTs": ruts,
        "nombres_sii": nombres_sii,
        "nombre_mas_probable": nombre_mas_probable,
        "rut_mas_probable": rut_mas_probable
    }
    logging.info(f"Datos de '{nombre_a_buscar}' actualizados mediante deep search.")
    save_json_cache(cache_ruts_empresas,CACHE_FILE)

def run_deep_search_for_missing(cache, cache_file):
    missing = [empresa for empresa, data in cache.items() if not data.get("rut_mas_probable")]
    if missing:
        logging.info("Ejecutando deep search para las empresas faltantes...")
        for empresa in missing:
            logging.info(f"Deep search para: {empresa}")
            buscar_en_SII(empresa, cache, cache_file)

def optimize_cache_duplicates(cache, CACHE_FILE):
    logging.info("Iniciando optimización de duplicados en el cache...")
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
                            logging.info(f"Optimizando: '{nombre_actual}' se homologará a '{nombre_common}' (similitud: {similarity}%, ratio: {ratio:.2f})")
                            cache[key]["nombre_mas_probable"] = nombre_common
                            cache[key]["rut_mas_probable"] = rut
    save_json_cache(cache_ruts_empresas,CACHE_FILE)

def guardar_datos_en_csv(data, filename=os.path.join(cache_folder, "CompiladoEmpresasConRUT.csv")):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            logging.info("Error al decodificar JSON:", e)
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

    logging.info(f"Archivo CSV generado exitosamente: {filename}")

intentos = 3
for intento in range(1, intentos + 1):
    try:

        ACTUALIZAR_SII(base_sii)
        cache_ruts_empresas = load_json_cache(cache_file)
        old_cache_keys = set(cache_ruts_empresas.keys())
        empresas = obtener_nuevos_registros_de_empresas(resultados_folder)
        empresas = [fix_encoding(e) for e in empresas]
        empresas_sin_rut = empresas.copy()
        n_intentos = 0
        resultados, faltantes = buscar_rut_empresas(cache_file ,empresas, n_intentos, max_intentos=3)
        run_deep_search_for_missing(cache_ruts_empresas, cache_file)
        optimize_cache_duplicates(cache_ruts_empresas, cache_file)
        guardar_datos_en_csv(cache_ruts_empresas)
        funciones.subir_empresa(cache_folder)
        break
    except Exception as e:
        if intento < intentos:
            logging.error(f"Fallo en homologar barras: {e}")
            logging.info(f"Reintentando: {intento}")
        else:
            logging.error(f"Fallo el codigo de homologacion: {e}")
            raise