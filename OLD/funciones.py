import sys
import time
import json
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
import os
import re
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import zipfile
import shutil
import ctypes
import pyodbc
from lxml import html
from urllib.parse import urljoin
import tqdm
from rapidfuzz import process, fuzz
import random
from fake_useragent import UserAgent
from datetime import datetime as dt
import glob
import holidays
import numpy as np
import urllib
from sqlalchemy import create_engine, text
import traceback
import gc
from datetime import datetime, timedelta
import logging
import calendar
import warnings
from scipy import stats
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  CONTRATOS  #######################################################################################################
##########################################################################################################################################
def descargar_datos_contratos(MAX_REINTENTOS, descargados_contratos_folder):
    try:
        logging.info('COMENZANDO DESCARGA DE CONTRATOS.XLSX')

        url = "https://icdp0af7ze.execute-api.us-east-1.amazonaws.com/prod/public"
        params = {
            "type": "descarga_publica", "empresa": "", "cliente": "",
            "tipoContrato": "", "suscripcion": "", "inicio": "",
            "termino": "", "idContrato": "", "iniciofechaTermino": "",
            "finfechaTermino": ""
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "es-US,es-419;q=0.9,es;q=0.8,en;q=0.7,de;q=0.6",
            "content-type": "application/json",
            "origin": "https://plataformamercado.coordinador.cl",
            "priority": "u=1, i",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        reintentos = 0
        
        while reintentos < MAX_REINTENTOS:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=120)

                if response.status_code == 200:
                    response_data = response.json()
                    download_url = response_data.get("data")
                    
                    if not download_url:
                        logging.error("Error: La API respondio correctamente, pero no entrego un enlace de descarga valido.")
                        return None

                    logging.info("Enlace de descarga obtenido")
                    
                    file_response = requests.get(download_url, timeout=60)

                    if file_response.status_code == 200:
                        os.makedirs(descargados_contratos_folder, exist_ok=True)
                        
                        fecha_actual = datetime.now().strftime("%y%m%d")
                        nombre_archivo = f"Contratos_{fecha_actual}.xlsx"
                        ruta_archivo = os.path.join(descargados_contratos_folder, nombre_archivo)

                        with open(ruta_archivo, "wb") as file:
                            file.write(file_response.content)
                        
                        logging.info("Archivo descargado correctamente")
                        return ruta_archivo 
                    else:
                        logging.error(f"Error al intentar descargar el archivo desde el enlace. Codigo: {file_response.status_code}")
                        return None

                elif response.status_code in [502, 503, 504]:
                    logging.error(f"Error en el servidor de la API ({response.status_code}).")
                    
                else:
                    logging.error(f"Error critico en la solicitud inicial. Codigo: {response.status_code}")
                    logging.error(response.text)
                    return None

            except requests.exceptions.RequestException as e:
                logging.error(f"Error de conexion a la red o Timeout: {e}")
                
            except Exception as e:
                logging.error(f"Error inesperado procesando la descarga: {e}")
                return None

            reintentos += 1
            if reintentos < MAX_REINTENTOS:
                logging.warning(f"Reintentando ({reintentos}/{MAX_REINTENTOS})")
                time.sleep(5)

        logging.error("Error persistente después de multiples intentos. No se pudo descargar el archivo.")
        return None
    except Exception as e:
        logging.error(f"Fallo en la descarga de contratos: {e}")

def obtener_archivo_mas_reciente(descargados_contratos_folder):
    matching_files = [os.path.join(descargados_contratos_folder, f) for f in os.listdir(descargados_contratos_folder) 
                      if re.match(r"Contratos_\d{6}\.xlsx", f)]
    
    if not matching_files:
        logging.warning("No se encontraron archivos que coincidan con el patron.")
        return None, None

    last_file = max(matching_files, key=os.path.getmtime)
    logging.info(f"Archivo mas reciente encontrado: {os.path.basename(last_file)}")

    fecha_str = re.search(r"Contratos_(\d{6})\.xlsx", last_file).group(1)
    fecha_ingreso = pd.to_datetime(fecha_str, format='%y%m%d').date()
    
    return last_file, fecha_ingreso

def limpiar_y_calcular_energia(df):
    hoy = datetime.now().date()
    
    df['Término'] = pd.to_datetime(df['Término'], errors='coerce').dt.date
    df = df[df['Término'] >= hoy].copy()

    columnas_energia = [col for col in df.columns if 'Energía' in col]

    for col in columnas_energia:    
        df[col] = df[col].astype(str).str.replace(',', '.', regex= False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    def remover_aislados_por_fila(row):
        anios_con_datos = []
        for col in columnas_energia:
            if not pd.isnull(row[col]):
                try:
                    anios_con_datos.append(int(col.split()[1]))
                except ValueError:
                    pass
        
        anios_con_datos.sort()
        anios_aislados = set()

        for i, anio in enumerate(anios_con_datos):
            prev_anio = anios_con_datos[i-1] if i > 0 else None
            next_anio = anios_con_datos[i+1] if i < len(anios_con_datos) - 1 else None

            if prev_anio is None and next_anio is not None and (next_anio - anio >= 2):
                anios_aislados.add(anio)
            elif next_anio is None and prev_anio is not None and (anio - prev_anio >= 2):
                anios_aislados.add(anio)
            elif (prev_anio is not None) and (next_anio is not None):
                if (anio - prev_anio >= 2) and (next_anio - anio >= 2):
                    anios_aislados.add(anio)
        
        for anio in anios_aislados:
            row[f"Energía {anio}"] = None
        return row

    logging.info("Removiendo datos de energia aislados")
    df = df.apply(remover_aislados_por_fila, axis=1)

    df['Promedio Energía (GWh)'] = df[columnas_energia].mean(axis=1) / 1000
    df['Máximo Energía (GWh)']   = df[columnas_energia].max(axis=1)  / 1000
    df['Mínimo Energía (GWh)']   = df[columnas_energia].min(axis=1)  / 1000

    cols_calc = ['Promedio Energía (GWh)', 'Máximo Energía (GWh)', 'Mínimo Energía (GWh)']
    df[cols_calc] = df[cols_calc].fillna(0)
    df.drop(columns=columnas_energia, inplace=True)

    df['Año Término'] = pd.to_datetime(df['Término']).dt.year.astype(int)
    df['Mes Término'] = pd.to_datetime(df['Término']).dt.month.astype(int)
    df['Año Inicio'] = pd.to_datetime(df['Inicio']).dt.year.astype(int)
    df['Mes Inicio'] = pd.to_datetime(df['Inicio']).dt.month.astype(int)

    return df

def actualizar_historico_contratos(df_nuevos, output_file, fecha_ingreso):

    diccionario_renombres = {
        'Id Contrato': 'ID_CONTRATO',
        'Empresa Suministradora': 'SUMINISTRADOR',
        'Rut Suministradora': 'RUT_SUM',
        'Tipo Suministrador': 'TIPO_SUM',
        'Tipo Contrato': 'TIPO_CONTRATO',
        'Red Distribuidora': 'RED_DISTRIBUIDORA',
        'Tipo Cliente': 'TIPO_CLIENTE',
        'Empresa Cliente': 'CLIENTE',
        'Rut Empresa Cliente': 'RUT_CLI',
        'Inicio': 'INICIO',
        'Término': 'TERMINO',
        'Fecha Renovación': 'FECHA_RENOVACION',
        'Región': 'REGION',
        'Sector Económico': 'SECTOR_ECONOMICO',  
        'Subsector Económico': 'SUBSECTOR_ECONOMICO',
        'ID puntos de Suministro': 'ID_PUNTO_SUMINISTRO',
        'Listado de puntos de Suministro': 'LISTADO_PUNTOS_DE_SUMINISTRO',
        'ID puntos de Retiro': 'ID_PUNTO_RETIRO',
        'Listado de puntos de Retiro': 'LISTADO_PUNTOS_DE_RETIRO',
        'Promedio Energía (GWh)': 'Promedio_Energia_GWh',
        'Máximo Energía (GWh)': 'Maximo_Energia_GWh',
        'Mínimo Energía (GWh)': 'Minimo_Energia_GWh',
        'Año Término': 'ANIO_TERMINO',
        'Mes Término': 'MES_TERMINO',
        'Año Inicio': 'ANIO_INICIO',
        'Mes Inicio': 'MES_INICIO',
        'Es Nuevo o Es Antiguo': 'ES_NUEVO_O_ANTIGUO',
        'Fecha de Ingreso': 'FECHA_DE_INGRESO'
    }
    
    logging.info("Preparando columnas de df nuevo")
    df_nuevos = df_nuevos.rename(columns=diccionario_renombres)

    print(df_nuevos)
    
    #df_nuevos['INICIO'] = pd.to_datetime(df_nuevos['INICIO'], errors='coerce')
    #df_nuevos['FECHA_DE_INGRESO'] = pd.to_datetime(df_nuevos['FECHA_DE_INGRESO'], errors='coerce')

    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    una_semana = hoy - timedelta(weeks=1)

    if os.path.exists(output_file):
        df_existente = pd.read_parquet(output_file)
        logging.info("Archivo historico cargado. Evaluando contratos")

        df_existente['ES_NUEVO_O_ANTIGUO'] = np.where(
            (pd.to_datetime(df_existente['INICIO'], errors='coerce').dt.normalize() >= pd.to_datetime(ayer)) &
            (pd.to_datetime(df_existente['FECHA_DE_INGRESO'], errors='coerce') >= pd.to_datetime(una_semana)),
            'Nuevo', 'Antiguo'
        )
        print(df_nuevos.info())
        df_filtrados = df_nuevos[~df_nuevos['ID_CONTRATO'].isin(df_existente['ID_CONTRATO'])].copy()
        df_filtrados['FECHA_DE_INGRESO'] = fecha_ingreso
        
        df_filtrados['ES_NUEVO_O_ANTIGUO'] = np.where(
            (pd.to_datetime(df_filtrados['INICIO'], errors='coerce') >= pd.to_datetime(ayer)) &
            (pd.to_datetime(df_filtrados['FECHA_DE_INGRESO'], errors='coerce') >= pd.to_datetime(una_semana)),
            'Nuevo', 'Antiguo'
        )

        df_final = pd.concat([df_existente, df_filtrados], ignore_index=True)
    else:
        logging.info("No existe historico. Creando base desde cero")
        df_nuevos['ES_NUEVO_O_ANTIGUO'] = np.where(
            pd.to_datetime(df_nuevos['INICIO'], errors='coerce') >= pd.to_datetime(ayer),
            'Nuevo', 'Antiguo'
        )
        df_nuevos['FECHA_DE_INGRESO'] = fecha_ingreso
        df_final = df_nuevos.copy()

    df_final.sort_values(by="ID_CONTRATO", ascending=False, inplace=True)
    return df_final

def formatear_y_guardar_salida(df_final, output_file):
    cols = ["Promedio Energía (GWh)", "Máximo Energía (GWh)", "Mínimo Energía (GWh)"]

    for c in cols:
        if df_final[c].dtype == 'object' or df_final[c].dtype.name == 'string':
            df_final[c] = df_final[c].astype(str).str.replace(',', '.', regex=False)
        
        df_final[c] = pd.to_numeric(df_final[c], errors='coerce')
        
        df_final[c] = df_final[c].round(4)

    df_final.to_parquet(output_file, index=False)
    logging.info(f"Archivo procesado y guardado exitosamente en '{output_file}'.")

def preparar_columnas_para_sql(df):
    
    cols = ["Promedio_Energia_GWh", "Maximo_Energia_GWh", "Minimo_Energia_GWh"]

    for c in cols:
        if df[c].dtype == 'object' or df[c].dtype.name == 'string':
            df[c] = df[c].astype(str).str.replace(',', '.', regex=False)
        
        df[c] = pd.to_numeric(df[c], errors='coerce')
        
        df[c] = df[c].round(4)

    
    diccionario_renombres = {
        'Id Contrato': 'ID_CONTRATO',
        'Empresa Suministradora': 'SUMINISTRADOR',
        'Rut Suministradora': 'RUT_SUM',
        'Tipo Suministrador': 'TIPO_SUM',
        'Tipo Contrato': 'TIPO_CONTRATO',
        'Red Distribuidora': 'RED_DISTRIBUIDORA',
        'Tipo Cliente': 'TIPO_CLIENTE',
        'Empresa Cliente': 'CLIENTE',
        'Rut Empresa Cliente': 'RUT_CLI',
        'Inicio': 'INICIO',
        'Término': 'TERMINO',
        'Fecha Renovación': 'FECHA_RENOVACION',
        'Región': 'REGION',
        'Sector Económico': 'SECTOR_ECONOMICO',  
        'Subsector Económico': 'SUBSECTOR_ECONOMICO',
        'ID puntos de Suministro': 'ID_PUNTO_SUMINISTRO',
        'Listado de puntos de Suministro': 'LISTADO_PUNTOS_DE_SUMINISTRO',
        'ID puntos de Retiro': 'ID_PUNTO_RETIRO',
        'Listado de puntos de Retiro': 'LISTADO_PUNTOS_DE_RETIRO',
        'Promedio Energía (GWh)': 'Promedio_Energia_GWh',
        'Máximo Energía (GWh)': 'Maximo_Energia_GWh',
        'Mínimo Energía (GWh)': 'Minimo_Energia_GWh',
        'Año Término': 'ANIO_TERMINO',
        'Mes Término': 'MES_TERMINO',
        'Año Inicio': 'ANIO_INICIO',
        'Mes Inicio': 'MES_INICIO',
        'Es Nuevo o Es Antiguo': 'ES_NUEVO_O_ANTIGUO',
        'Fecha de Ingreso': 'FECHA_DE_INGRESO'
    }
    
    logging.info("Preparando columnas para SQL")
    df_sql = df.rename(columns=diccionario_renombres).copy()
    
    df_sql['INICIO'] = pd.to_datetime(df_sql['INICIO'], errors='coerce')
    df_sql['FECHA_DE_INGRESO'] = pd.to_datetime(df_sql['FECHA_DE_INGRESO'], errors='coerce')
    
    return df_sql

def limpiar_filas_para_sql(df):
    logging.info("LIMPIANDO FILAS")
    df_clean = df.copy()
    
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
    
    reemplazos_tildes = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U"
    }
    
    for col in df_clean.columns:
        
        if df_clean[col].dtype == 'object' or df_clean[col].dtype.name == 'string':
            
            df_clean[col] = df_clean[col].apply(
                lambda x: str(x).replace('\x00', '').strip() if pd.notnull(x) else x
            )
            
            for con_tilde, sin_tilde in reemplazos_tildes.items():
                df_clean[col] = df_clean[col].str.replace(con_tilde, sin_tilde, regex=False)
            
            valores_a_nulo = ['', 'nan', 'NaN', 'None', 'null']
            df_clean[col] = df_clean[col].replace(valores_a_nulo, np.nan)
            
            df_clean[col] = df_clean[col].where(pd.notnull(df_clean[col]), None)
            
        elif pd.api.types.is_numeric_dtype(df_clean[col]):
            pass
            
        elif pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].where(pd.notnull(df_clean[col]), None)

    logging.info("LIMPIEZA TERMINADA")
    return df_clean

def subir_contratos_a_sql(parquet_contratos):
    logging.info(f"Leyendo archivo para subir a SQL: {parquet_contratos}")
    
    try:
        df = pd.read_parquet(parquet_contratos)
    except Exception as e:
        logging.error(f"Error al leer el archivo parquet: {e}")
        return
    columnas_fecha = ['INICIO', 'FECHA_DE_INGRESO']

    for col in columnas_fecha:
        if col in df.columns:

            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            
            df[col] = df[col].replace({'NaT': None, 'nan': None, np.nan: None})

    tabla_destino = 'Contratos'
    engine = obtener_engine_sql()

    try:
        with engine.begin() as conn:
            logging.info(f"Limpiando datos antiguos en la tabla '{tabla_destino}'")
            conn.execute(text(f"TRUNCATE TABLE {tabla_destino}"))
        
        logging.info(f"[SUBIENDO] Insertando {len(df)} contratos actualizados")
        df.to_sql(
            name=tabla_destino, 
            con=engine, 
            if_exists='append',
            index=False, 
            schema='dbo',
            chunksize=1000
        )
        logging.info("Base de datos actualizada correctamente.")
            
    except Exception as e:
        logging.error(f"ERROR: Fallo la actualización de la tabla {tabla_destino}: {e}")
        traceback.print_exc()
        raise
            
    finally:
        if engine:
            engine.dispose()
            logging.info("SQL Listo.")
        
        if 'df' in locals():
            del df
            gc.collect()
##########################################################################################################################################
######################  DESCARGAR RET/INY/CMG  ###########################################################################################
##########################################################################################################################################
def Obtener_links_de_Plabacom():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    #chrome_options.add_argument("--headless=new")

    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    df = pd.DataFrame()

    try:

        logging.info("Entrando en Plabacom")

        driver.get("https://plabacom.coordinador.cl/pages")

        menu_descargas = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Descargas')]"))
        )
        menu_descargas.click()
        time.sleep(1)

        try:
            submenu = driver.find_element(By.XPATH, "//a[contains(@href, '/downloads/list')]")
            if submenu.is_displayed():
                submenu.click()
                time.sleep(2)
        except Exception as e:
            logging.error(f"Cambio la Plataforma de Plabacom actualiza las funciones de descarga: {e}")
            raise 
    
        time.sleep(1) 

        logs = driver.get_log('performance')
        api_url = None
    
        for entry in logs:
            try:
                message_json = json.loads(entry['message'])
                message = message_json.get('message', {})
            
                if "Network.requestWillBeSent" in message.get('method', ''):
                    params = message.get('params', {})
                    request = params.get('request', {})
                    url = request.get('url', '')
                
                    if "api/presigned-urls" in url:
                        api_url = url
                        break 
            except Exception:
                continue 
    
        if not api_url:
            raise Exception("No se encontró la URL 'presigned-urls'.")

        session = requests.Session()
    
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        session.headers.update({"User-Agent": driver.execute_script("return navigator.userAgent;")})

        respuesta = session.get(api_url)
        datos_archivos = respuesta.json()

        links_zip = []
        patron = re.compile(r"^03[- ]Bases[- ]de[- ]Datos_(\d{2})(\d{2})_BD\d{2}\.zip$", re.IGNORECASE)
        for archivo in datos_archivos:
            nombre = archivo.get('label', 'Sin Nombre')
            match = patron.match(nombre)
            url = archivo.get('url')
        
            if match:
                links_zip.append({"nombre": nombre, "url": url})

        if links_zip:
            df = pd.DataFrame(links_zip)
            logging.info(f"Se encontraron: {len(df)} links de descarga.")             
        else:
            logging.info("No se encontraron coincidencias con 03 Bases de Datos_(año)(mes)_BD01.zip")
        
    except Exception as e:
        logging.info(f"Error: {e}")
        logging.error(traceback.format_exc())

    finally:
        driver.quit()
    return df

def revisar_archivos_faltantes(resultados_folder):
    carpeta = os.path.basename(resultados_folder)
    logging.info(f"Iniciando escaneo de meses faltantes en: {carpeta}")
    try:
        today = date.today()
        meses_esperados = set()
    
        for i in range(1, 4): 
            mes_calculado = today.month - i
            anio_calculado = today.year
        
            while mes_calculado <= 0:
                mes_calculado += 12
                anio_calculado -= 1
            
            anio_corto = anio_calculado - 2000
            meses_esperados.add((anio_corto, mes_calculado))

        meses_encontrados = set()
    
        if os.path.exists(resultados_folder):
            for archivo in os.listdir(resultados_folder):
            
                if archivo.startswith("resultado_retiros_tipo_") and archivo.endswith(".parquet"):
                
                    match = re.search(r'(\d{4})(\d{2})', archivo)
                    if match:
                        yyyy = int(match.group(1))
                        mm = int(match.group(2))
                        yy = yyyy - 2000
                    
                        meses_encontrados.add((yy, mm))
                    
        else:
            logging.warning(f"Aviso: No se encontro la ruta {carpeta}")

        missing_files = meses_esperados - meses_encontrados

        return missing_files

    except Exception as e:
        logging.error(f'Error: {e}')

        return set()

def Filtrar_link_descarga_necesario(df_archivos, tupla_fecha):
    try:
        anio_buscado = tupla_fecha[0]
        mes_buscado = tupla_fecha[1]

        patron = r"_(\d{2})(\d{2})_BD"
        df_temp = df_archivos.copy()

        df_temp[['Anio_temp', 'Mes_temp']] = df_temp['nombre'].str.extract(patron).astype(int)

        match = df_temp[(df_temp['Anio_temp']==anio_buscado) & (df_temp['Mes_temp']==mes_buscado)]
    
        if not match.empty:
            url_encontrada = match.iloc[0]['url']
            nombre_archivo = match.iloc[0]['nombre']

            logging.info(f"Link encontrado para {nombre_archivo}")

            return {
                'nombre':nombre_archivo,
                'url':url_encontrada
            }
        else:
            logging.error(f"No se encontro archivo en Plabacom para {anio_buscado},{mes_buscado}")
            return []
    except Exception as e:
        logging.error(f"Fallo el filtro de links necesarios: {e}")
        raise

def Descargar_Archivo(link_descarga, download_folder, max_intentos=3):
    url = link_descarga['url']
    nombre_archivo = link_descarga['nombre']
    ruta_completa = os.path.join(download_folder, nombre_archivo)
    
    for intento in range(1, max_intentos + 1):
        logging.info(f"Iniciando descarga de: {nombre_archivo} (Intento {intento}/{max_intentos})")
        
        try:

            with requests.get(url, stream=True, timeout=120) as respuesta:
                respuesta.raise_for_status()
                
                chunk_size = 1024 * 1024
                
                with open(ruta_completa, 'wb') as f:
                    for data in respuesta.iter_content(chunk_size=chunk_size):
                        if data:
                            f.write(data)
            
            logging.info(f"Descarga Completada Exitosamente: {nombre_archivo}")
            return ruta_completa 
                
        except Exception as e:
            logging.error(f"Error en la descarga de {nombre_archivo} (Intento {intento}): {e}")
            
            if os.path.exists(ruta_completa):
                try:
                    os.remove(ruta_completa)
                    logging.info("Archivo parcial incompleto eliminado correctamente.")
                except Exception as ex_borrado:
                    logging.error(f"No se pudo borrar el archivo parcial: {ex_borrado}")
            
            if intento < max_intentos:
                logging.info("Esperando 5 segundos antes de reintentar")
                time.sleep(5)
            else:
                logging.error(f"Se agotaron los {max_intentos} intentos. No se pudo descargar {nombre_archivo}.")
                sys.exit()
                return None
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  PROCESAR ZIP  ####################################################################################################
##########################################################################################################################################
def find_all_zips(directory):
    if not os.path.exists(directory):
        logging.info('No existe la carpeta de descargas')
        return []
    zip_files = [os.path.join(directory, file)
                 for file in os.listdir(directory) if file.lower().endswith('.zip')]
    if not zip_files:
        logging.info("No se encontraron archivos .zip en la carpeta.")
        return []
    zip_files.sort(key=os.path.getmtime, reverse=True)
    logging.info("Archivos .zip encontrados para procesar:")
    for idx, zip_path in enumerate(zip_files):
        logging.info(f"  {idx + 1}. {zip_path}")
    return zip_files

def extract_zip(zip_path):
    """
    Extrae un archivo .zip. Si es el ZIP principal, usa solo el número de 
    año/mes (ej. '2601') como nombre de carpeta para acortar la ruta.
    Para ZIPs internos, acorta el nombre original.
    Retorna la carpeta donde se extrajo o None si ocurre un error.
    """
    if not os.path.exists(zip_path):
        logging.info(f"ERROR: Archivo ZIP no encontrado: {zip_path}")
        return None
        
    base_dir = os.path.dirname(zip_path)
    zip_name = os.path.basename(zip_path)
    name_without_ext = os.path.splitext(zip_name)[0]
    
    match = re.search(r'_(\d{4})_', name_without_ext)
    
    if match:
        folder_name = match.group(1)
    else:
        folder_name = name_without_ext[:20].strip()
        
    extract_to = os.path.join(base_dir, folder_name)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
        logging.info(f"Se extrajo: {zip_name} -- {extract_to}")
        
    except zipfile.BadZipFile:
        logging.info(f"ERROR: Archivo ZIP dañado o corrupto: {zip_path}")
        return None
    except NotImplementedError as e:
        logging.info(f"ERROR: No se pudo extraer '{zip_path}' (metodo no soportado): {e}")
        return None
    except Exception as e:
        logging.info(f"ERROR inesperado al extraer '{zip_path}': {e}")
        return None
        
    return extract_to

def limpiar_extraccion_descargada(directory):
    """
    Recorre el directorio indicado y elimina:
    - Carpetas que comiencen con "04 Precio" o "05 Pro".
    - Archivos que comiencen con "Fpen" o "Registros".
    
    Parámetros:
    directory (str): La ruta de la carpeta que se va a limpiar.
    """
    if not os.path.exists(directory):
        logging.info(f"El directorio para limpiar no existe: {directory}")
        return

    logging.info(f"Iniciando limpieza en: {directory}")
    
    # Definimos lo que queremos buscar (todo en minúsculas para evitar problemas de mayúsculas)
    prefijos_archivos = ('fpen', 'registros', 'retiros_informe')
    prefijos_carpetas = ('04 precio', '05 pro')

    # Usamos topdown=False para eliminar de adentro hacia afuera de forma segura
    for root, dirs, files in os.walk(directory, topdown=False):
        
        # 1. Eliminar archivos que coincidan
        for file in files:
            if file.lower().startswith(prefijos_archivos):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    logging.info(f"Archivo eliminado: {file}")
                except Exception as e:
                    logging.info(f"ERROR al eliminar el archivo '{file}': {e}")
                    
        # 2. Eliminar carpetas que coincidan
        for d in dirs:
            if d.lower().startswith(prefijos_carpetas):
                dir_path = os.path.join(root, d)
                try:
                    # shutil.rmtree elimina la carpeta y todo su contenido
                    shutil.rmtree(dir_path)
                    logging.info(f"Carpeta eliminada: {d}")
                except Exception as e:
                    logging.info(f"ERROR al eliminar la carpeta '{d}': {e}")
                    
    logging.info("-" * 60)

def renombrar_medidas(directory, numero):
    logging.info(f"Iniciando renombrado de archivos 'Medidas' en: {directory}")
    
    # Diccionario con las reglas de reemplazo (todo en minúsculas para comparar fácil)
    mapeo_nombres = {
        "compraventas": "compraventas",
        "norte distribución": "nortedist",
        "norte": "nortetrans",
        "sur distribución": "surdist",
        "sur": "surtrans"
    }
    
    # Recolectamos las rutas primero para evitar errores al modificar el disco mientras buscamos
    elementos_a_renombrar = []
    
    for root, dirs, files in os.walk(directory):
        # Buscamos en archivos (porque los de la imagen son .zip)
        for file in files:
            if file.lower().startswith("medidas_valorizadas_15min_"):
                elementos_a_renombrar.append((root, file, True)) # True = es archivo
                
        # Por si en algún momento se extraen y son carpetas, también las buscamos
        for d in dirs:
            if d.lower().startswith("medidas_valorizadas_15min_"):
                elementos_a_renombrar.append((root, d, False)) # False = es carpeta

    # Procedemos a renombrar
    if not elementos_a_renombrar:
        logging.info("No se encontraron archivos de 'Medidas' para renombrar.")
        return

    for root, nombre_original, es_archivo in elementos_a_renombrar:
        # Separar el nombre de la extensión (ej. '.zip')
        nombre_sin_ext, ext = os.path.splitext(nombre_original)
        
        # Quitamos la parte inicial para quedarnos solo con la zona (ej. "Norte Distribución")
        sufijo = nombre_sin_ext.lower().replace("medidas_valorizadas_15min_", "").strip()
        
        # Verificamos si esa zona está en nuestro diccionario de reemplazo
        if sufijo in mapeo_nombres:
            nuevo_nombre_base = mapeo_nombres[sufijo]
            
            # Construimos el nuevo nombre: base + numero + extension
            nuevo_nombre_completo = f"{nuevo_nombre_base}{numero}{ext}"
            
            ruta_antigua = os.path.join(root, nombre_original)
            ruta_nueva = os.path.join(root, nuevo_nombre_completo)
            
            try:
                os.rename(ruta_antigua, ruta_nueva)
                logging.info(f"Renombrado: '{nombre_original}' --- '{nuevo_nombre_completo}'")
            except Exception as e:
                logging.info(f"ERROR al renombrar '{nombre_original}': {e}")
                
    logging.info("-" * 60)

def find_and_extract_mdb(directory, download_folder):
    """
    Busca y extrae archivos .mdb en el directorio (y subdirectorios),
    excluyendo aquellas carpetas cuyo nombre siga el patrón "Retiros_*_15min".
    Copia cada .mdb en ZIP_DIRECTORY con su nombre original.
    """
    mdb_files_found = []
    for root, dirs, files in os.walk(directory):
        # Excluir carpetas que sigan el patrón "retiros_*_15min"
        dirs[:] = [d for d in dirs if not re.match(r'retiros_.*_15min', d.lower())]
        for file in files:
            full_path = os.path.join(root, file)
            if file.lower().endswith('.mdb'):
                destination = os.path.join(download_folder, file)
                try:
                    shutil.copy2(full_path, destination)  # Preserva metadatos
                    logging.info(f"Archivo .mdb copiado: {destination}")
                    mdb_files_found.append(destination)
                except Exception as e:
                    logging.info(f"ERROR al copiar '{file}': {e}")
            elif file.lower().endswith('.zip'):
                extracted_folder = extract_zip(full_path)
                if extracted_folder:
                    logging.info(f"Se extrajo '{file}' en '{extracted_folder}'")
                    mdb_files_found.extend(find_and_extract_mdb(extracted_folder))
                else:
                    logging.info(f"No se pudo extraer '{file}'.")
    return mdb_files_found

def extraer_zips_internos(directory):
    """
    Recorre el directorio buscando archivos .zip.
    Extrae cada .zip en una nueva carpeta con su mismo nombre.
    Luego, renombra los archivos extraídos para que coincidan con el nombre del ZIP original.
    """
    if not os.path.exists(directory):
        logging.info(f"El directorio no existe: {directory}")
        return

    logging.info(f"Iniciando extracción y renombrado de ZIPs en: {directory}")
    
    # 1. Recolectamos todas las rutas
    zips_a_extraer = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.zip'):
                zips_a_extraer.append(os.path.join(root, file))
                
    if not zips_a_extraer:
        logging.info("No se encontraron archivos .zip para extraer en esta ruta.")
        return

    # 2. Extraer y renombrar
    for zip_path in zips_a_extraer:
        base_dir = os.path.dirname(zip_path)
        nombre_zip = os.path.basename(zip_path)
        nombre_carpeta = os.path.splitext(nombre_zip)[0] # Ej: 'compraventas2601'
        ruta_extraccion = os.path.join(base_dir, nombre_carpeta)
        
        if not os.path.exists(ruta_extraccion):
            os.makedirs(ruta_extraccion)
            
        try:
            # Extraemos los archivos
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(ruta_extraccion)
            logging.info(f"Extraído: '{nombre_zip}' --- Carpeta: '{nombre_carpeta}'")
            
            # --- NUEVA LÓGICA: Renombrar los archivos extraídos ---
            archivos_extraidos = os.listdir(ruta_extraccion)
            
            for index, filename in enumerate(archivos_extraidos):
                ruta_antigua = os.path.join(ruta_extraccion, filename)
                
                # Solo renombramos si es un archivo (ignoramos si extrajo subcarpetas)
                if os.path.isfile(ruta_antigua):
                    extension = os.path.splitext(filename)[1] # Ej: '.csv' o '.mdb'
                    
                    # Si solo hay 1 archivo, le ponemos el nombre exacto del ZIP
                    if len(archivos_extraidos) == 1:
                        nuevo_nombre = f"{nombre_carpeta}{extension}"
                    # Si hay más de 1, le agregamos un índice para no sobrescribir
                    else:
                        nuevo_nombre = f"{nombre_carpeta}_{index + 1}{extension}"
                        
                    ruta_nueva = os.path.join(ruta_extraccion, nuevo_nombre)
                    
                    # Renombramos (verificando que no se llame ya igual)
                    if ruta_antigua != ruta_nueva:
                        os.rename(ruta_antigua, ruta_nueva)
                        logging.info(f"Archivo renombrado a: {nuevo_nombre}")
            
        except zipfile.BadZipFile:
            logging.info(f"ERROR: El archivo '{nombre_zip}' esta dañado o no es valido.")
        except Exception as e:
            logging.info(f"ERROR inesperado al extraer '{nombre_zip}': {e}")

    logging.info("-" * 60)

def copiar_archivos_utiles(source_dir, dest_dir):
    """
    Recorre 'source_dir' y sus subcarpetas. Copia todos los archivos que NO 
    sean .zip ni .rar hacia 'dest_dir'.
    
    Parámetros:
    source_dir (str): La carpeta donde vamos a buscar los archivos.
    dest_dir (str): La carpeta final donde vamos a pegar los archivos.
    """
    if not os.path.exists(source_dir):
        logging.info(f"La carpeta de origen no existe: {source_dir}")
        return

    # Si la carpeta de destino no existe, la creamos
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    logging.info(f"Iniciando copiado de archivos hacia: {dest_dir}")
    
    archivos_copiados = 0

    # Recorremos la carpeta de origen
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # Obtenemos la extensión del archivo y la convertimos a minúsculas
            # splitext divide "archivo.csv" en ("archivo", ".csv")
            extension = os.path.splitext(file)[1].lower()
            
            # Filtramos: Si NO es .zip y NO es .rar, entonces lo copiamos
            if extension not in ['.zip', '.rar']:
                ruta_origen = os.path.join(root, file)
                ruta_destino = os.path.join(dest_dir, file)
                
                try:
                    # shutil.copy2 copia el archivo conservando sus fechas originales
                    shutil.copy2(ruta_origen, ruta_destino)
                    logging.info(f"Copiado: {file}")
                    archivos_copiados += 1
                except Exception as e:
                    logging.info(f"Error al copiar '{file}': {e}")

    logging.info(f"Proceso finalizado. Se copiaron {archivos_copiados} archivos en total.")
    logging.info("-" * 60)

def listar_carpetas(directorio):
    """Imprime la estructura de carpetas y subcarpetas encontradas en el directorio."""
    logging.info("Estructura de carpetas encontradas:")
    for raiz, subcarpetas, archivos in os.walk(directorio):
        nivel = raiz.replace(directorio, "").count(os.sep)
        indentacion = " " * (nivel * 4)
        logging.info(f"{indentacion} {os.path.basename(raiz)}")
        for subcarpeta in subcarpetas:
            logging.info(f"{indentacion}     {subcarpeta}")

def cambiar_permisos_y_eliminar(ruta):
    """Forza el cambio de permisos y elimina la carpeta indicada."""
    try:
        # Cambia atributos para establecer permisos normales
        ctypes.windll.kernel32.SetFileAttributesW(ruta, 128)  # FILE_ATTRIBUTE_NORMAL
        shutil.rmtree(ruta)
        logging.info(f"Carpeta eliminada: {ruta}")
    except PermissionError:
        logging.info(f"Permiso denegado al intentar eliminar: {ruta}")
    except OSError as e:
        logging.info(f"Error al eliminar '{ruta}': {e}")

def limpiar_archivos_sistema(ruta):
    """
    Elimina archivos del sistema que pueden impedir que una carpeta se considere vacía,
    como 'desktop.ini' o 'Thumbs.db'.
    """
    system_files = ["desktop.ini", "Thumbs.db"]
    for sf in system_files:
        sf_path = os.path.join(ruta, sf)
        if os.path.exists(sf_path):
            try:
                os.remove(sf_path)
                logging.info(f"Archivo del sistema eliminado: {sf_path}")
            except Exception as e:
                logging.info(f"No se pudo eliminar {sf_path}: {e}")

def eliminar_archivos_y_subcarpetas(directorio):
    """
    Elimina archivos con extensión .zip, .csv, .xlsx o .mdb que se encuentren en subcarpetas,
    y luego intenta eliminar las subcarpetas que estén vacías o que solo contengan archivos
    del sistema.
    
    Se saltea el directorio raíz para no eliminar archivos que estén directamente en él.
    """
    if not os.path.exists(directorio):
        logging.info(f"El directorio '{directorio}' no existe.")
        return

    listar_carpetas(directorio)

    # Recorre el árbol de directorios de forma bottom-up (de abajo hacia arriba)
    for raiz, subcarpetas, archivos in os.walk(directorio, topdown=False):
        # Si no estamos en el directorio raíz, elimina archivos con las extensiones indicadas
        if raiz != directorio:
            for archivo in archivos:
                ruta_archivo = os.path.join(raiz, archivo)
                if archivo.endswith(('.zip','.csv', '.xlsx', '.mdb', '.pdf', '.tsv')):
                    try:
                        os.remove(ruta_archivo)
                        logging.info(f"Archivo eliminado: {ruta_archivo}")
                    except Exception as e:
                        logging.info(f"Error al eliminar '{ruta_archivo}': {e}")
        # Para cada subcarpeta, primero intentamos eliminar archivos del sistema
        for subcarpeta in subcarpetas:
            ruta_subcarpeta = os.path.join(raiz, subcarpeta)
            limpiar_archivos_sistema(ruta_subcarpeta)
            try:
                # Si luego de limpiar, la carpeta está vacía, se elimina
                if not os.listdir(ruta_subcarpeta):
                    cambiar_permisos_y_eliminar(ruta_subcarpeta)
                else:
                    # Muestra qué contiene la carpeta si no está vacía
                    contenido = os.listdir(ruta_subcarpeta)
                    logging.info(f"La carpeta '{ruta_subcarpeta}' NO esta vacía: {contenido}")
            except Exception as e:
                logging.info(f"Error al procesar '{ruta_subcarpeta}': {e}")
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  PROCESAR ACCESS  #################################################################################################
##########################################################################################################################################
def extraer_anio_mes_de_nombre(nombre_archivo):
    match = re.search(r'([0-9]{2})([0-9]{2})', nombre_archivo)
    
    if match:
        anio = f"20{match.group(1)}" 
        mes = match.group(2)
        return anio, mes
    else:
        return None, None

def obtener_nombre_con_fecha(ruta_base, anio, mes):
    nombre, extension = os.path.splitext(ruta_base)
    nuevo_nombre = f"{nombre}{anio}{mes}{extension}"
    return nuevo_nombre

def obtener_driver_access():
    drivers_disponibles = pyodbc.drivers()
    buscados = [
        'Microsoft Access Driver (*.mdb, *.accdb)', 
        'Microsoft Access Driver (*.mdb)', 
        'Driver do Microsoft Access (*.mdb)', 
        'MS Access Database'
    ]
    for d in buscados:
        if d in drivers_disponibles:
            return d
    raise RuntimeError(f"No se encontró driver Access. Instalados: {drivers_disponibles}")

def guardar_parquet(df_out, nombre_archivo):
        if not df_out.empty:
            df_out.to_parquet(
                nombre_archivo,
                engine='pyarrow',
                index=False,
                compression='snappy'
            )
            logging.info(f"Archivo guardado: {nombre_archivo} ({len(df_out)} registros)")
        else:
            logging.info(f"Aviso: Dataset vacio para {nombre_archivo}, no se guarda.")

def extraer_R(archivo_path, ruta_salida):
    nombre_base = os.path.basename(archivo_path)
    anio, mes = extraer_anio_mes_de_nombre(nombre_base)
    
    if anio is None or mes is None:
        logging.info(f"No se pudo extraer fecha desde el archivo: {nombre_base}. Se omite.")
        return

    access_driver = obtener_driver_access()
    
    logging.info(f"Iniciando conexion con {nombre_base}")
    
    try:
        with pyodbc.connect(driver=access_driver, dbq=archivo_path, autocommit=True) as bb:
            logging.info("Conexion exitosa.")
            
            query_unificada = """
            SELECT DISTINCT Suministrador, [Hora Mensual], Medida_kWh, Barra, Retiro
            FROM dbo_Retiros 
            WHERE Tipo = 'R'
            """
            df_R = pd.read_sql(query_unificada, bb)
            if df_R.empty:
                logging.info(f"Advertencia: No se encontraron datos R en {nombre_base}")
                return
            df_R['Mes'] = mes
            df_R['Año'] = anio
    except Exception as e:
        logging.info(f"Error procesando {nombre_base}: {e}")
        return

    os.makedirs(ruta_salida, exist_ok=True)
    output_path_R= obtener_nombre_con_fecha(os.path.join(ruta_salida, "retiros_tipo_R.parquet"), anio, mes)
    guardar_parquet(df_R, output_path_R)

def extraer_L(archivo_path, ruta_salida):
    nombre_base = os.path.basename(archivo_path)
    anio, mes = extraer_anio_mes_de_nombre(nombre_base)
    
    if anio is None or mes is None:
        logging.info(f"No se pudo extraer fecha desde el archivo: {nombre_base}. Se omite.")
        return

    access_driver = obtener_driver_access()
    
    logging.info(f"\nIniciando conexión con {nombre_base}")
    
    try:
        with pyodbc.connect(driver=access_driver, dbq=archivo_path, autocommit=True) as bb:
            logging.info("Conexión exitosa.")
            
            query_unificada = """
            SELECT DISTINCT Suministrador, [Hora Mensual], Medida_kWh, Barra, Retiro
            FROM dbo_Retiros 
            WHERE Tipo = 'L'
            """
            df_L = pd.read_sql(query_unificada, bb)
            if df_L.empty:
                logging.info(f"Advertencia: No se encontraron datos L en {nombre_base}")
                return
            df_L['Mes'] = mes
            df_L['Año'] = anio
    except Exception as e:
        logging.info(f"Error procesando {nombre_base}: {e}")
        return

    os.makedirs(ruta_salida, exist_ok=True)
    output_path_L= obtener_nombre_con_fecha(os.path.join(ruta_salida, "retiros_tipo_LeT.parquet"), anio, mes)
    guardar_parquet(df_L, output_path_L)

def extraer_LD(archivo_path, ruta_salida):
    nombre_base = os.path.basename(archivo_path)
    anio, mes = extraer_anio_mes_de_nombre(nombre_base)
    
    if anio is None or mes is None:
        logging.info(f"No se pudo extraer fecha desde el archivo: {nombre_base}. Se omite.")
        return

    access_driver = obtener_driver_access()
    
    logging.info(f"\nIniciando conexión con {nombre_base}")
    
    try:
        with pyodbc.connect(driver=access_driver, dbq=archivo_path, autocommit=True) as bb:
            logging.info("Conexión exitosa.")
            
            query_unificada = """
            SELECT DISTINCT Suministrador, [Hora Mensual], Medida_kWh, Barra, Retiro
            FROM dbo_Retiros 
            WHERE Tipo = 'L_D'
            """
            df_LD = pd.read_sql(query_unificada, bb)
            if df_LD.empty:
                logging.info(f"Advertencia: No se encontraron datos L en {nombre_base}")
                return
            df_LD['Mes'] = mes
            df_LD['Año'] = anio
    except Exception as e:
        logging.info(f"Error procesando {nombre_base}: {e}")
        return

    os.makedirs(ruta_salida, exist_ok=True)
    output_path_LD= obtener_nombre_con_fecha(os.path.join(ruta_salida, "retiros_tipo_LeD.parquet"), anio, mes)
    guardar_parquet(df_LD, output_path_LD)
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  ACTUALIZAR_SII  ##################################################################################################
##########################################################################################################################################
def establecer_conexion(url):
    try:
        encabezados = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        logging.info(f"Intentando conectar a: {url}")
        
        respuesta = requests.get(url, headers=encabezados, timeout=10)
        
        if respuesta.status_code == 200:
            logging.info("Conexion a la pagina del SII exitosa")
            return respuesta
        else:
            logging.info(f"Error al conectar: {respuesta.status_code}")
            return None
            
    except requests.exceptions.RequestException as error:
        logging.info(f"No se logro establecer conexion: {error}")
        return None

def buscar_enlace_especifico(respuesta_web, url_base, terminacion_buscada):
    logging.info(f"Buscando un archivo que termine en '{terminacion_buscada}'")
    arbol_html = html.fromstring(respuesta_web.content)
    todos_los_enlaces = arbol_html.xpath('//a/@href')
    
    for enlace in todos_los_enlaces:
        if enlace.endswith(terminacion_buscada):
            enlace_completo = urljoin(url_base, enlace)
            logging.info("Archivo encontrado")
            return enlace_completo
            
    logging.info(f"ERROR: No se encontro ningun link con terminacion {terminacion_buscada}, actualizar el codigo en la funcion 'buscar_enlace_especifico'")
    return None

def descargar_archivo(url_descarga, nombre_archivo, ruta_carpeta_destino):
    os.makedirs(ruta_carpeta_destino, exist_ok=True)
    ruta_completa = os.path.join(ruta_carpeta_destino, nombre_archivo)
    
    logging.info(f"Iniciando descarga de archivo en: {ruta_completa}")
    
    try:
        encabezados = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0'}
        respuesta_descarga = requests.get(url_descarga, headers=encabezados, stream=True, timeout=30)
        
        if respuesta_descarga.status_code == 200:
            with open(ruta_completa, 'wb') as archivo:
                for fragmento in respuesta_descarga.iter_content(chunk_size=8192):
                    archivo.write(fragmento)
            logging.info("Descarga completada")
            return ruta_completa
        else:
            logging.info(f"ERROR en la descarga: {respuesta_descarga.status_code}")
            return None
    except Exception as e:
        logging.info(f"ERROR al descargar: {e}")
        return None

def extraer_y_eliminar_zip(ruta_archivo_zip, carpeta_destino):
    logging.info("\nIniciando la extraccion del archivo del zip")
    try:
        with zipfile.ZipFile(ruta_archivo_zip, 'r') as archivo_zip:
            archivo_zip.extractall(carpeta_destino)
            logging.info("Extraccion lista")
            
        os.remove(ruta_archivo_zip)
        logging.info("Archivo zip descargado, eliminado")
        return True
        
    except zipfile.BadZipFile:
        logging.info("ERROR: El archivo descargado no es un .zip esta corrupto.")
        return False
    except Exception as e:
        logging.info(f"ERROR: al extraer o eliminar el archivo: {e}")
        return False

def transformar_txt_a_parquet(ruta_txt, ruta_parquet):
    logging.info("\nLimpiando SII.txt y almacenandolo en formato .parquet")
    
    try:
        df = pd.read_csv(ruta_txt, sep='\t', dtype=str, encoding='latin1')
        
        df['RUT'] = df['RUT'].str.strip()
        df['DV'] = df['DV'].str.strip()
        df['RAZON_SOCIAL'] = df['RAZON_SOCIAL'].str.strip()
        
        df['RUT'] = df['RUT'] + '-' + df['DV']
        
        df_final = df[['RUT', 'RAZON_SOCIAL']].copy()
        df_final.to_parquet(ruta_parquet, engine='pyarrow', index=False)
        logging.info("Archivo almacenado en formato parquet")
        return True
        
    except Exception as e:
        logging.info(f"ERROR en la transformacion: {e}")
        return False
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  RETIROS PROMEDIO  ################################################################################################
##########################################################################################################################################
def parse_year_month_from_filename(filename):
    match = re.search(r'(\d{6})', filename)
    if not match:
        return None
    yyyymm = match.group(1)
    year = int(yyyymm[:4])
    month = int(yyyymm[4:])
    return (year, month)

def find_missing_files(procesados_folder, resultados_folder):
    today = dt.today()
    limit_year = today.year - 3
    limit_month = today.month
    
    pattern = os.path.join(procesados_folder, "retiros_tipo_*.parquet")
    all_files = glob.glob(pattern)
    
    missing_files = []
    
    for ruta_entrada in all_files:
        nombre_archivo = os.path.basename(ruta_entrada)
        
        combo = parse_year_month_from_filename(nombre_archivo)
        if combo is None:
            continue
            
        year, month = combo
        
        if (year < limit_year) or (year == limit_year and month < limit_month):
            continue
            
        nombre_esperado_salida = f"resultado_{nombre_archivo}"
        ruta_salida_esperada = os.path.join(resultados_folder, nombre_esperado_salida)
        
        if not os.path.exists(ruta_salida_esperada):
            missing_files.append(ruta_entrada)
    return missing_files

def drop_unnamed_column(df):
    cols_to_drop = [c for c in df.columns if 'Unnamed' in c]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df

def normalize_year_column(df):
    if 'Año' in df.columns:
        if 'Anio' in df.columns:
            df['Anio'] = df['Anio'].fillna(df['Año'])
            df = df.drop(columns=['Año'])
        else:
            df = df.rename(columns={'Año': 'Anio'})
    return df

def calcular_consumo_mensual_barra(df):
    columnas_agrupacion = ['Anio', 'Mes', 'Barra', 'Retiro']

    df_mensual = df.groupby(columnas_agrupacion, as_index=False)['Medida_kWh'].sum().reset_index()
    
    #df_mensual = df_mensual.drop_duplicates()

    df_mensual['Medida_kWh'] = (df_mensual['Medida_kWh'] / 1000).abs()

    df_mensual = df_mensual.rename(columns = {'Medida_kWh':'Consumo_Mensual_MWh'})
    
    df_mensual = drop_unnamed_column(df_mensual)
    df_mensual['Mes'] = df_mensual['Mes'].astype(int)
    df_mensual['Anio'] = df_mensual['Anio'].astype(int)
    return df_mensual

def completar_horas_faltantes(df):

    claves = ['Anio', 'Mes', 'Retiro', 'Barra']

    df_unicos = df[claves].drop_duplicates()

    def obtener_total_horas(fila):
        anio = int(fila['Anio'])
        mes = int(fila['Mes'])
        dias_del_mes = calendar.monthrange(anio, mes)[1]
        return dias_del_mes * 24
    df_unicos['Max_Horas'] = df_unicos.apply(obtener_total_horas, axis=1)
    df_unicos['Hora Mensual'] = df_unicos['Max_Horas'].apply(lambda x: list(range(1, x + 1)))
    df_plantilla = df_unicos.explode('Hora Mensual').drop(columns=['Max_Horas'])
    df_plantilla['Hora Mensual'] = df_plantilla['Hora Mensual'].astype(int)
    df_final = pd.merge(
        df_plantilla, 
        df, 
        on=['Anio', 'Mes', 'Retiro', 'Barra', 'Hora Mensual'], 
        how='left'
    )
    df_final['Medida_MWh'] = df_final['Medida_MWh'].fillna(0.0)
    df_final = drop_unnamed_column(df_final)
    return df_final

def Preprocesar_dataframe(df):

    logging.info("Transformando medida de [kWh] a [MWh]")

    df['Medida_kWh'] = (df['Medida_kWh'] / 1000).abs()
    df = df.rename(columns={'Medida_kWh':'Medida_MWh'})

    logging.info("OK")

    logging.info("Sumando retiro por Cliente y Barra")

    group_cols1 = ['Anio', 'Mes', 'Retiro', 'Barra', 'Hora Mensual']
    df= df.groupby(group_cols1)['Medida_MWh'].sum().reset_index()
    #grouped = df.groupby(group_cols1)['Medida_MWh']
    #df['Medida_MWh'] = grouped.transform('sum')
    #df = df.drop_duplicates()

    logging.info("OK")

    logging.info("Rellenando horas faltantes")

    df = completar_horas_faltantes(df)

    logging.info("OK")

    logging.info("Transformando hora mensual a hora diaria y obteniendo categoria de dia")

    df.sort_values(by='Hora Mensual', inplace=True)
    if 'Fecha' not in df.columns:
        dia_del_mes = ((df['Hora Mensual'] - 1) // 24) + 1
        df['Fecha'] = dia_del_mes.astype(str).str.zfill(2) + '/' + \
                      df['Mes'].astype(str).str.zfill(2) + '/' + \
                      df['Anio'].astype(str)
    df['Hora_Diaria'] = (df['Hora Mensual'] - 1) % 24 + 1
    df['ParsedDate'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', dayfirst=True, errors='coerce')
    df['Anio'] = df['Anio'].astype(int)
    df['Dia de la Semana'] = df['ParsedDate'].dt.day_name()
    anios_unicos = df['Anio'].dropna().unique().tolist()
    feriados_chile = holidays.CL(years=anios_unicos)
    cond_nulo = df['ParsedDate'].isnull()
    cond_fin_semana = df['ParsedDate'].dt.weekday >= 5
    cond_feriado = df['ParsedDate'].isin(feriados_chile)
    es_no_habil = cond_nulo | cond_fin_semana | cond_feriado
    df['Categoría Día'] = np.where(es_no_habil, 'PROMEDIO_DiaNoHabil', 'PROMEDIO_DiaHabil')
    df = df.drop(columns=['Hora Mensual', 'Fecha', 'ParsedDate', 'Dia de la Semana'])

    logging.info("OK")
    return df

def calcular_perfil_por_bloque(df):

    condiciones = [
        (df['Hora_Diaria'].between(1, 8)) | (df['Hora_Diaria'] == 24),
        (df['Hora_Diaria'].between(9, 18)),
        (df['Hora_Diaria'].between(19, 23))
    ]
    nombres_bloques = ['A', 'B', 'C']
    df['Nombre_Bloque'] = np.select(condiciones, nombres_bloques, default='Desconocido')

    logging.info("Calculando retiro promedio por bloques RAW, Dia habil y dia no habil")

    Columnas = ['Anio', 'Mes', 'Retiro', 'Barra', 'Nombre_Bloque']
    grouped = df.groupby(Columnas)['Medida_MWh']
    df['RAW_Promedio_Bloque_MWh'] = grouped.transform('mean')
    Columnas = ['Anio', 'Mes', 'Retiro', 'Barra', 'Nombre_Bloque','Categoría Día']
    grouped = df.groupby(Columnas)['Medida_MWh']
    df['RAW_Promedio_Bloque_HabilNoHabil_MWh'] = grouped.transform('mean')
    df = df.drop(columns=['Hora_Diaria', 'Medida_MWh'])
    df = df.drop_duplicates()

    logging.info("OK")

    logging.info("Pivoteando dia habil y no habil")

    columnas_indice = ['Anio', 'Mes', 'Retiro', 'Barra','Nombre_Bloque','RAW_Promedio_Bloque_MWh']
    pivot = pd.pivot_table(
        df,
        index=columnas_indice,
        columns='Categoría Día',
        values='RAW_Promedio_Bloque_HabilNoHabil_MWh',
        aggfunc='first' 
    ).reset_index()
    pivot.columns.name = None
    pivot['Mes'] = pivot['Mes'].astype(int)
    logging.info("OK")

    del df
    return pivot

def calcular_medidas(df):

    group_cols1 = ['Anio', 'Mes', 'Retiro', 'Barra', 'Hora_Diaria']
    grouped = df.groupby(group_cols1)['Medida_MWh']
    df['RAW_Promedio_MWh'] = grouped.transform('mean')
    df['RAW_Desviacion_MWh'] = grouped.transform('std').fillna(0.0)
    df['RAW_Max_MWh'] = grouped.transform('max')
    group_cols1 = ['Anio', 'Mes', 'Retiro', 'Barra', 'Hora_Diaria','Categoría Día']
    grouped = df.groupby(group_cols1)['Medida_MWh']
    df['Promedio_Dia_semana_MWh'] = grouped.transform('mean')
    df = df.drop(columns=['Medida_MWh'])
    df = df.drop_duplicates()
    df['Mes'] = df['Mes'].astype(int)
    return df

def Promedio_habilNohabil_a_columna(df):

    columnas_indice = [
    'Anio', 'Mes', 'Retiro', 'Barra', 'Hora_Diaria', 
    'RAW_Promedio_MWh', 'RAW_Desviacion_MWh', 'RAW_Max_MWh'
    ]

    pivot = pd.pivot_table(
        df,
        index=columnas_indice,
        columns='Categoría Día',
        values='Promedio_Dia_semana_MWh',
        aggfunc='first' 
    ).reset_index()

    pivot.columns.name = None

    return pivot

def guardar_retiro_mensual_barra(df_mensual, ruta_entrada, resultados_folder):
    nombre_archivo = os.path.basename(ruta_entrada)
    
    nombre_salida = f"mensual_{nombre_archivo}"
    ruta_salida = os.path.join(resultados_folder, nombre_salida)
    df_mensual = drop_unnamed_column(df_mensual)
    df_mensual.to_parquet(ruta_salida, index=False, engine='pyarrow', compression='snappy')
    
    return ruta_salida

def guardar_resultado_individual(df, ruta_entrada, resultados_folder):
    nombre_archivo = os.path.basename(ruta_entrada)
    
    nombre_salida = f"resultado_{nombre_archivo}"
    ruta_salida = os.path.join(resultados_folder, nombre_salida)
    
    df.to_parquet(ruta_salida, index=False, engine='pyarrow', compression='snappy')
    df = drop_unnamed_column(df)
    return ruta_salida

def guardar_resultado_bloques(df, ruta_entrada, resultados_folder):
    nombre_archivo = os.path.basename(ruta_entrada)
    
    nombre_salida = f"perfil_bloque_{nombre_archivo}"
    ruta_salida = os.path.join(resultados_folder, nombre_salida)
    
    df.to_parquet(ruta_salida, index=False, engine='pyarrow', compression='snappy')
    df = drop_unnamed_column(df)
    return ruta_salida
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
######################  SUBIR RETIRO PROMEDIO Y BLOQUE A SLQ #############################################################################
##########################################################################################################################################
def obtener_engine_sql():
    logging.info("Conectandose al servidor SQL")
    server = '<REDACTADO>'  # credenciales retiradas antes de publicar (ver CLAUDE.md, ADR-006)
    database = '<REDACTADO>'
    username = '<REDACTADO>'
    password = '<REDACTADO>'
    driver = '{ODBC Driver 17 for SQL Server}'
    
    params = urllib.parse.quote_plus(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=300;'
    )
    
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}", 
        fast_executemany=True,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={'timeout': 300}
    )
    return engine

def subir_carpeta_a_sql(resultados_folder):
    engine = obtener_engine_sql()
    archivos = glob.glob(os.path.join(resultados_folder, "*.parquet"))
    
    if not archivos:
        logging.info("No se encontraron archivos .parquet en la carpeta.")
        return

    logging.info("Consultando registros existentes en la base de datos")
    existentes_retiros = set()
    existentes_bloques = set()
    existentes_mensual = set()
    
    try:
        with engine.connect() as conn:
            try:
                res_retiros = conn.execute(text("SELECT DISTINCT Anio, Mes FROM EstadisticasRetirosV2")).fetchall()
                existentes_retiros = set((row[0], row[1]) for row in res_retiros)
            except Exception:
                logging.warning("No se encontro la tabla EstadisticasRetirosV2")
            try:
                res_bloques = conn.execute(text("SELECT DISTINCT Anio, Mes FROM RetiroBloques")).fetchall()
                existentes_bloques = set((row[0], row[1]) for row in res_bloques)
            except Exception:
                logging.warning("No se encontro la tabla RetiroBloques")
            try:
                res_mensual = conn.execute(text("SELECT DISTINCT Anio, Mes FROM RetiroHistoricoMensual")).fetchall()
                existentes_mensual = set((row[0], row[1]) for row in res_mensual)
            except Exception:
                logging.warning("No se encontro la tabla RetiroHistoricoMensual")
    except Exception as e:
        logging.error(f"ERROR: No se pudo leer el datos de SQL (¿Tablas vacías o no creadas?): {e}")
        return

    logging.info(f"SQL: {existentes_retiros} meses en Retiros, {existentes_bloques} meses en Bloques y {existentes_mensual} meses en Retiro Mensual.")
    

    for archivo in archivos:
        nombre_base = os.path.basename(archivo)
        
        match = re.search(r'(\d{4})(\d{2})', nombre_base)
        if not match:
            logging.warninr(f"Ignorado (Sin fecha en el nombre): {nombre_base}")
            continue
            
        anio_file = int(match.group(1))
        mes_file = int(match.group(2))
        
        if nombre_base.startswith("perfil_bloque_"):
            tabla_destino = 'RetiroBloques'
            
            if (anio_file, mes_file) in existentes_bloques:
                logging.info(f"[OMITIDO] {anio_file}-{mes_file:02d} ya existe en {tabla_destino}. Archivo: {nombre_base}")
                continue
                
            df = pd.read_parquet(archivo, engine='pyarrow')
            
        elif nombre_base.startswith("resultado_retiros_"):
            tabla_destino = 'EstadisticasRetirosV2'
            
            if (anio_file, mes_file) in existentes_retiros:
                logging.info(f"[OMITIDO] {anio_file}-{mes_file:02d} ya existe en {tabla_destino}. Archivo: {nombre_base}")
                continue
                
            df = pd.read_parquet(archivo, engine='pyarrow')

        elif nombre_base.startswith("mensual_retiros"):
            tabla_destino = 'RetiroHistoricoMensual'
            if (anio_file, mes_file) in existentes_mensual:
                logging.info(f"[OMITIDO] {anio_file}-{mes_file:02d} ya existe en {tabla_destino}. Archivo: {nombre_base}")
                continue
            df = pd.read_parquet(archivo, engine='pyarrow')
            
        else:
            continue

        try:
            logging.info(f"[SUBIENDO] Nuevos datos detectados: {anio_file}-{mes_file:02d} -> {tabla_destino} ({len(df)} filas)")
            df = drop_unnamed_column(df)
            columnas_a_borrar = ['index', 'Index', 'Score_Similitud', 'Columna_Temporal']
            for col in columnas_a_borrar:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    logging.info(f"Columna {col} eliminada desde {archivo}")
            df.to_sql(
                name=tabla_destino, 
                con=engine, 
                if_exists='append', 
                index=False, 
                schema='dbo',
                chunksize=50000,
            )
            logging.info(f" -> EXITO subiendo {nombre_base}")
            
        except Exception as e:
            logging.error(f"ERROR: Fallo la subida del archivo {nombre_base}: {e}")
            traceback.print_exc()
    if engine:
        engine.dispose()
        logging.info("Proceso de subida a SQL finalizado y conexion terminada")

def subir_empresa(resultados_folder):
    engine = obtener_engine_sql()
    tabla_destino = 'EmpresaSubdivision'
    
    logging.info(f"Iniciando subida de empresas homologadas desde: {resultados_folder}")
    path = os.path.join(resultados_folder,'CompiladoEmpresasConRUT.csv')
    try:
        df = pd.read_csv(path, sep=',')
        
    except Exception as e:
        logging.error(f"Error fatal al leer el archivo maestro: {e}")
        return

    try:
        with engine.begin() as conn: 
            logging.info(f"Vaciando tabla '{tabla_destino}' (TRUNCATE TABLE)...")
            try:
                conn.execute(text(f"TRUNCATE TABLE {tabla_destino}"))
            except Exception as e:
                logging.warning(f"No se pudo truncar (quizás la tabla aún no existe): {e}")
        
        logging.info(f"[SUBIENDO] Insertando {len(df)} registros en {tabla_destino}")
        
        safe_chunksize = max(1, 2000 // len(df.columns))
        
        df.to_sql(
            name=tabla_destino, 
            con=engine, 
            if_exists='append',
            index=False, 
            schema='dbo',
            chunksize=safe_chunksize 
        )
        logging.info(" -> EXITO Cliente Subdivision actualizado en SQL Server.")
        
    except Exception as e:
        logging.error(f"ERROR: Falló la actualización de la tabla maestra: {e}")
        traceback.print_exc()
        
    finally:
        if engine:
            engine.dispose()
            logging.info("Conexión SQL terminada Homologacion de clientes.")
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
###################### PROCESAR INY y COMPRAVENTA ################################################################################
##########################################################################################################################################
def leer_y_filtrar_TIPO(df, tipos_validos=['C_FIN','C_FIS','L', 'L_D', 'R','G']):
    filas_iniciales = len(df)
    logging.info(f"Filtrando por tipos: {tipos_validos}")
    
    df_filtrado = df[df['tipo'].isin(tipos_validos)].copy()
    
    filas_eliminadas = filas_iniciales - len(df_filtrado)
    logging.info(f"Se eliminaron {filas_eliminadas} filas. Quedan {len(df_filtrado)}.")
    
    return df_filtrado

def estandarizar_barra_iny(row):
    t = str(row['tension']).zfill(3)
    n = str(row['nombre_barra'])

    guiones_faltantes = 17 - len(n) - len(t)

    if guiones_faltantes > 0:
        return n + ('_' * guiones_faltantes) + t
    else:
        return n + '_' + t



def preprocesar_csv_raw(df, pq_in, cmg):

    df = drop_unnamed_column(df)

    df = leer_y_filtrar_TIPO(df, tipos_validos=['C_FIN','C_FIS','G'])
    print(df)

    df['Fecha_Medicion'] = pd.to_datetime(df['Fecha_Medicion'])

    df['Anio'] = df['Fecha_Medicion'].dt.year
    df['Mes'] = df['Fecha_Medicion'].dt.month
    df['Hora'] = df['Fecha_Medicion'].dt.hour + 1
    df['Dia'] = df['Fecha_Medicion'].dt.day

    df['Mes'] = df['Mes'].astype(int)
    df['Anio'] = df['Anio'].astype(int)
    df['Hora'] = df['Hora'].astype(int)
    df['Dia'] = df['Dia'].astype(int)



    df['Barra'] = df.apply(estandarizar_barra_iny, axis=1)
    df = pd.merge(
    df,
    cmg,
    on = ['Barra', 'Hora', 'Dia'],
    how='left'
    )

    df = df.drop(columns=['Dia','Fecha_Medicion'])
    df = df.drop(columns=['tension','nombre_barra'])
    df['Valorizado[USD]'] = df['medida_3'] * df['CMg[USD/MWh]']/1000
    df['medida_3'] = df['medida_3']/1000000
    print(df)
    df = df.rename(columns={'Nombre_Corto':'Suministrador', 'medida_3':'Medida_GWh'})
    COLS = [
        'Barra', 
        'Suministrador', 
        'tipo',
        'descripcion',
        'Anio',
        'Mes',
        'Hora',
        'ID_Contrato'
    ]
    df = df.groupby(COLS, dropna=False)[['Medida_GWh', 'Valorizado[USD]']].sum().reset_index()
    print(df)
    df.to_parquet(pq_in, engine='pyarrow', compression='snappy')
    return df

def calcular_bloques(df):

    condiciones = [
        (df['Hora'].between(1, 8)) | (df['Hora'] == 24),
        (df['Hora'].between(9, 18)),
        (df['Hora'].between(19, 23))
    ]
    nombres_bloques = ['A', 'B', 'C']
    df['Nombre_Bloque'] = np.select(condiciones, nombres_bloques, default='Desconocido')
    df = df.drop(columns='Hora')
    logging.info("Calculando iny por bloque")
    columnas_iny = ['Barra', 'Anio','Mes', 'Suministrador', 'Nombre_Bloque','descripcion','tipo','ID_Contrato']
    df = df.groupby(columnas_iny, dropna=False)[['Medida_GWh', 'Valorizado[USD]']].sum().reset_index()
    #df = df.rename(columns={'Medida_MWh':'Iny_sum_BLOQUE_MWh'})
    #grouped = df.groupby(columnas_iny)['Medida_MWh']
    #df['Iny_promedio_bloque_MWh'] = grouped.transform('mean')
    #df = df.drop(columns='Medida_MWh')
    #df = df.drop_duplicates()
    return df

def extraer_anio_mes_de_nombre_iny(nombre_archivo):

    match = re.search(r'(\d{4})(\d{2})', nombre_archivo)
    
    if match:
        anio = int(match.group(1))
        mes = int(match.group(2))
        
        if 1 <= mes <= 12:
            return anio, mes
        else:
            return None, None
    else:
        return None, None

def procesar_y_vincular_retiros(cmg, carpeta_origen, carpeta_destino, dict_fechas_referencia):
    archivos_procesados_match = {}
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta creada: {carpeta_destino}")

    lista_archivos = os.listdir(carpeta_origen)
    
    for file in lista_archivos:
        if file.endswith(".parquet"):
            coincidencia = re.search(r'retiros_tipo_(R|LeT|LeD)', file)
            if coincidencia:
                tipo = coincidencia.group(1)
                if tipo in ("LeT", "LeD"):
                    tipo = "L"
                anio, mes = extraer_anio_mes_de_nombre_iny(file) 
                fecha_key = (anio, mes)
                
                if fecha_key in dict_fechas_referencia:
                    print(f"Procesando archivo para {fecha_key}: {file}")
                    
                    ruta_original = os.path.join(carpeta_origen, file)
                    df_retiro = pd.read_parquet(ruta_original, columns=['Suministrador','Hora Mensual','Medida_kWh','Barra','Mes','Año'])
                    df_retiro['Dia'] = ((df_retiro['Hora Mensual'] - 1) // 24) + 1
                    df_retiro['Medida_kWh'] = df_retiro['Medida_kWh']/1000000
                    df_retiro = df_retiro.rename(columns={'Medida_kWh':'Medida_GWh'})
                    df_retiro['Hora'] = (df_retiro['Hora Mensual'] - 1) % 24 + 1
                    df_retiro = pd.merge(
                        df_retiro,
                        cmg,
                        on = ['Barra', 'Dia', 'Hora'],
                        how = 'left'
                    )
                    df_retiro['Valorizado[USD]'] = df_retiro['CMg[USD/MWh]'] * df_retiro['Medida_GWh']*1000
                    df_retiro = df_retiro.drop(columns=['Hora Mensual', 'Dia', 'CMg[USD/MWh]'])
                    condiciones = [
                    (df_retiro['Hora'].between(1, 8)) | (df_retiro['Hora'] == 24),
                    (df_retiro['Hora'].between(9, 18)),
                    (df_retiro['Hora'].between(19, 23))
                    ]
                    nombres_bloques = ['A', 'B', 'C']
                    df_retiro['Nombre_Bloque'] = np.select(condiciones, nombres_bloques, default='Desconocido')
                    df_retiro = df_retiro.drop(columns='Hora')
                    df_retiro = df_retiro.groupby(['Suministrador','Barra','Mes','Año','Nombre_Bloque'], dropna=False)[['Medida_GWh','Valorizado[USD]']].sum().reset_index()
                    df_retiro = df_retiro.rename(columns={'Año':'Anio'})
                    df_retiro['Anio'] = df_retiro['Anio'].astype(int)
                    df_retiro['Mes'] = df_retiro['Mes'].astype(int)
                    df_retiro['descripcion'] = 'RETIRO'
                    df_retiro['tipo'] = tipo
                    df_retiro['ID_Contrato'] = 0.1
                    nuevo_nombre = f"procesado_{file}"
                    ruta_nueva = os.path.join(carpeta_destino, nuevo_nombre)
                    
                    df_retiro.to_parquet(ruta_nueva, index=False)
                    
                    if fecha_key not in archivos_procesados_match:
                        archivos_procesados_match[fecha_key] = []
                        
                    archivos_procesados_match[fecha_key].append(ruta_nueva)
                
    return archivos_procesados_match

def procesar_ret_para_iny(df_retiro, tipo, cmg):
    
    df_retiro['Dia'] = ((df_retiro['Hora Mensual'] - 1) // 24) + 1
    df_retiro['Medida_kWh'] = df_retiro['Medida_kWh']/1000000
    df_retiro = df_retiro.rename(columns={'Medida_kWh':'Medida_GWh'})
    df_retiro['Hora'] = (df_retiro['Hora Mensual'] - 1) % 24 + 1
    df_retiro = pd.merge(
        df_retiro,
        cmg,
        on = ['Barra', 'Dia', 'Hora'],
        how = 'left'
    )
    df_retiro['Valorizado[USD]'] = df_retiro['CMg[USD/MWh]'] * df_retiro['Medida_GWh']*1000
    df_retiro = df_retiro.drop(columns=['Hora Mensual', 'Dia', 'CMg[USD/MWh]'])
    condiciones = [
    (df_retiro['Hora'].between(1, 8)) | (df_retiro['Hora'] == 24),
    (df_retiro['Hora'].between(9, 18)),
    (df_retiro['Hora'].between(19, 23))
    ]
    nombres_bloques = ['A', 'B', 'C']
    df_retiro['Nombre_Bloque'] = np.select(condiciones, nombres_bloques, default='Desconocido')
    df_retiro = df_retiro.drop(columns='Hora')
    df_retiro = df_retiro.groupby(['Suministrador','Barra','Mes','Año','Nombre_Bloque'], dropna=False)[['Medida_GWh','Valorizado[USD]']].sum().reset_index()
    df_retiro = df_retiro.rename(columns={'Año':'Anio'})
    df_retiro['Anio'] = df_retiro['Anio'].astype(int)
    df_retiro['Mes'] = df_retiro['Mes'].astype(int)
    df_retiro['descripcion'] = 'RETIRO'
    df_retiro['tipo'] = tipo
    df_retiro['ID_Contrato'] = 0.1
    return df_retiro

def fechas_listas(resultados_iny_concat_folder):
    existentes = os.listdir(resultados_iny_concat_folder)
    patron_fecha = r'(\d{4})(\d{2})'

    fechas_listas = set() 

    for archivo in existentes:
        coincidencia = re.search(patron_fecha, archivo)
        if coincidencia:
            anio, mes = coincidencia.groups()
            fechas_listas.add((int(anio), int(mes)))
    return fechas_listas

def agrupar_archvios_por_fecha(resultados_iny_folder, fechas_listas_calculadas):
    lista_resultados_iny = os.listdir(resultados_iny_folder)
    dfs_por_fecha = {}
    for file in lista_resultados_iny:
        if file.endswith(".parquet"):
            anio,mes = extraer_anio_mes_de_nombre_iny(file)
            fecha_key = (anio,mes)
            
            # Buscamos en el parámetro que le pasamos, no en la función
            if fecha_key in fechas_listas_calculadas:
                continue
                
            if fecha_key not in dfs_por_fecha:
                dfs_por_fecha[fecha_key] = []
                
            ruta_completa = os.path.join(resultados_iny_folder,file)
            dfs_por_fecha[fecha_key].append(ruta_completa)
            
    return dfs_por_fecha

def agregar_tecnologia(df_mes_anio):
    condiciones = [
    df_mes_anio['descripcion'].str.contains('PMGD_FV|PMG__FV|PMG_FV|PMGS_FV|CTRL_FV|_FV_|PMGD_SGT|PMGD_AX|PMGD_PLAZA', case=False),
    df_mes_anio['descripcion'].str.contains('PMGD_TE|PMG_TE|CTRL_TE|CTRL_QBLANCA|PMGD_RES|PGMD_LAPORTADA', case=False),
    df_mes_anio['descripcion'].str.contains('PMGD_BG|PMGD_BM|CTRL_BM', case=False),
    df_mes_anio['descripcion'].str.contains('PMGD_HP|CTRL_HP|PMG__HP', case=False),
    df_mes_anio['descripcion'].str.contains('CTRL_EO|CTR_EO|PMG__EO', case=False),
    df_mes_anio['descripcion'].str.contains('BESS', case=False),
    df_mes_anio['descripcion'].str.contains('CSP', case=False),
    df_mes_anio['descripcion'].str.contains('CTRL_GT', case=False),
    df_mes_anio['descripcion'].str.contains('CTRL_HE', case=False)
    ]
    tecnologia = ['Fotovoltaica', 'Termica', 'Biogas_Biomasa', 'Hidraulica_Pasada','Eolica','BESS','CSP', 'Geotermica','Hidraulica_Embalse']

    df_mes_anio['Tecnologia'] = np.select(condiciones, tecnologia, default='Desconocido')
    return df_mes_anio

def definir_tipo_columnas(df_mes_anio):
    df_mes_anio['Anio'] = df_mes_anio['Anio'].astype(int)
    df_mes_anio['Mes'] = df_mes_anio['Mes'].astype(int)
    df_mes_anio['ID_Contrato'] = df_mes_anio['ID_Contrato'].astype(str)
    df_mes_anio['Barra'] = df_mes_anio['Barra'].astype(str)
    df_mes_anio['Suministrador'] = df_mes_anio['Suministrador'].astype(str)
    df_mes_anio['Nombre_Bloque'] = df_mes_anio['Nombre_Bloque'].astype(str)
    df_mes_anio['Medida_GWh'] = df_mes_anio['Medida_GWh'].astype(float)
    df_mes_anio['Valorizado[USD]'] = df_mes_anio['Valorizado[USD]'].astype(float)
    df_mes_anio['descripcion'] = df_mes_anio['descripcion'].astype(str)
    df_mes_anio['tipo'] = df_mes_anio['tipo'].astype(str)
    df_mes_anio['Tecnologia'] = df_mes_anio['Tecnologia'].astype(str)
    return df_mes_anio

def Cruzar_nombre_suministradores_cfinfis(resultados_iny_concat_folder):
    Cambiar_descripcion = os.listdir(resultados_iny_concat_folder)

    for file in Cambiar_descripcion:
        if not file.endswith(".parquet"):
            continue

        path = os.path.join(resultados_iny_concat_folder, file)

        df = pd.read_parquet(path)

        condicion = df['tipo'].isin(['C_FIN', 'C_FIS'])

        df_filtrado = df[condicion]
        conteos = df_filtrado['descripcion'].value_counts()
        descripciones_con_par = conteos[conteos == 2].index

        filtro_final = condicion & df['descripcion'].isin(descripciones_con_par)

        df.loc[filtro_final, 'descripcion'] = (
        df[filtro_final].groupby('descripcion')['Suministrador']
        .transform(lambda x: x.iloc[::-1].values)
        )

        df.to_parquet(path, index=False)

def subir_iny_a_sql(resultados_iny_concat_folder):
    engine = obtener_engine_sql()
    archivos = glob.glob(os.path.join(resultados_iny_concat_folder, "*.parquet"))
    
    if not archivos:
        logging.info("No se encontraron archivos .parquet en la carpeta.")
        return

    logging.info("Consultando registros existentes en la base de datos")
    existentes_iny_bloques = set()

    try:
        with engine.connect() as conn:
            try:
                res_iny = conn.execute(text("SELECT DISTINCT Anio, Mes FROM BalanceGenerador")).fetchall()
                existentes_iny_bloques = set(
                    (int(row[0]), int(row[1])) 
                    for row in res_iny 
                    if row[0] is not None and row[1] is not None
                )
            except Exception:
                logging.warning("No se encontro la tabla BalanceGenerador")
    except Exception as e:
        logging.error(f"ERROR: No se pudo leer el datos de SQL (¿Tablas vacías o no creadas?): {e}")
        return

    logging.info(f"SQL: {existentes_iny_bloques} meses en BalanceGenerador.")
    
    for archivo in archivos:
        nombre_base = os.path.basename(archivo)
        
        match = re.search(r'(\d{4})(\d{2})', nombre_base)
        if not match:
            logging.warninr(f"Ignorado (Sin fecha en el nombre): {nombre_base}")
            continue
            
        anio_file = int(match.group(1))
        mes_file = int(match.group(2))
        
        if nombre_base.endswith(".parquet"):
            tabla_destino = 'BalanceGenerador'
            
            if (anio_file, mes_file) in existentes_iny_bloques:
                logging.info(f"[OMITIDO] {anio_file}-{mes_file:02d} ya existe en {tabla_destino}. Archivo: {nombre_base}")
                continue
                
            df = pd.read_parquet(archivo, engine='pyarrow')
            df = df.rename(columns={'Valorizado[USD]': 'Valorizado_USD'})
            df['ID_Contrato'] = df['ID_Contrato'].replace(['', ' ', 'None'], np.nan)
            df['ID_Contrato'] = pd.to_numeric(df['ID_Contrato'], errors='coerce')
            
        else:
            continue

        try:
            logging.info(f"[SUBIENDO] Nuevos datos detectados: {anio_file}-{mes_file:02d} -> {tabla_destino} ({len(df)} filas)")
            
            df.to_sql(
                name=tabla_destino, 
                con=engine, 
                if_exists='append', 
                index=False, 
                schema='dbo',
                chunksize=50000 
            )
            logging.info(f" -> EXITO subiendo {nombre_base}")
            
        except Exception as e:
            logging.error(f"ERROR: Fallo la subida del archivo {nombre_base}: {e}")
            traceback.print_exc()
    if engine:
        engine.dispose()
        logging.info("Proceso de subida a SQL finalizado y conexion terminada")
##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
###################### LIMPIEZA ##########################################################################################################
##########################################################################################################################################
'''
def subir_barras_a_sql(mapa_folder):
    engine = obtener_engine_sql()
    tabla_destino = 'MaestroSubestaciones'
    
    logging.info(f"Iniciando subida del Maestro de Subestaciones desde: {mapa_folder}")
    path = os.path.join(mapa_folder,'Barra_Y_SUBESTACION.parquet')
    try:
        df = pd.read_parquet(path)
        
    except Exception as e:
        logging.error(f"Error fatal al leer el archivo maestro: {e}")
        return

    try:
        with engine.begin() as conn: 
            logging.info(f"Vaciando tabla '{tabla_destino}' (TRUNCATE TABLE)...")
            try:
                conn.execute(text(f"TRUNCATE TABLE {tabla_destino}"))
            except Exception as e:
                logging.warning(f"No se pudo truncar (quizás la tabla aún no existe): {e}")
        
        logging.info(f"[SUBIENDO] Insertando {len(df)} subestaciones en {tabla_destino}")
        
        safe_chunksize = max(1, 2000 // len(df.columns))
        
        df.to_sql(
            name=tabla_destino, 
            con=engine, 
            if_exists='append',
            index=False, 
            schema='dbo',
            chunksize=safe_chunksize 
        )
        logging.info(" -> EXITO Maestro de Subestaciones actualizado en SQL Server.")
        
    except Exception as e:
        logging.error(f"ERROR: Falló la actualización de la tabla maestra: {e}")
        traceback.print_exc()
        
    finally:
        if engine:
            engine.dispose()
            logging.info("Conexión SQL terminada para el Maestro.")
'''
def limpieza_download_folder(download_folder):
    if os.path.exists(download_folder):
        for file in os.listdir(download_folder):
            logging.info(f'Eliminando {file}')
            path = os.path.join(download_folder, file)
            os.remove(path)
    else:
        logging.info(f'No se encontro la carpeta de descargas: {download_folder}')

def limpieza_servidor_SQL_retiros():
    engine = obtener_engine_sql()

    logging.info('Revisando entradas antiguas de Reporte PPA [ RETIROS ]')

    existentes_retiros = set()
    existentes_bloques = set()
    existentes_mensual = set()

    try:
        with engine.connect() as conn:
            try:
                res_retiros = conn.execute(text("SELECT DISTINCT Anio, Mes FROM EstadisticasRetirosV2")).fetchall()
                existentes_retiros = set((row[0], row[1]) for row in res_retiros)
            except Exception:
                logging.warning("No se encontro la tabla EstadisticasRetirosV2")
            try:
                res_bloques = conn.execute(text("SELECT DISTINCT Anio, Mes FROM RetiroBloques")).fetchall()
                existentes_bloques = set((row[0], row[1]) for row in res_bloques)
            except Exception:
                logging.warning("No se encontro la tabla RetiroBloques")
            try:
                res_mensual = conn.execute(text("SELECT DISTINCT Anio, Mes FROM RetiroHistoricoMensual")).fetchall()
                existentes_mensual = set((row[0], row[1]) for row in res_mensual)
            except Exception:
                logging.warning("No se encontro la tabla RetiroHistoricoMensual")
    except Exception as e:
        logging.error(f"ERROR: No se pudo leer el datos de SQL (¿Tablas vacías o no creadas?): {e}")
        return
    
    logging.info(f"Se encontraron entradas para los meses : {existentes_retiros} en la tabla: EstadisticasRetirosV2")
    logging.info(f"Se encontraron entradas para los meses : {existentes_bloques} en la tabla: RetiroBloques")
    logging.info(f"Se encontraron entradas para los meses : {existentes_mensual} en la tabla: RetiroHistoricoMensual")
    
    today = date.today()
    meses_esperados = set()
    for i in range(1, 37): 
        mes_calculado = today.month - i
        anio_calculado = today.year
        while mes_calculado <= 0:
            mes_calculado += 12
            anio_calculado -= 1
        meses_esperados.add((anio_calculado, mes_calculado))

    print(tuple(sorted(meses_esperados)))
    print(len(meses_esperados))

    a_borrar_retiros = existentes_retiros - meses_esperados
    a_borrar_bloques = existentes_bloques - meses_esperados
    a_borrar_mensual = existentes_mensual - meses_esperados

    try:
        with engine.begin() as conn:
            for anio, mes in a_borrar_retiros:
                conn.execute(
                    text("DELETE FROM EstadisticasRetirosV2 WHERE Anio = :anio AND Mes = :mes"),
                    {"anio": anio, "mes": mes}
                )
                logging.info(f"Eliminado de EstadisticasRetirosV2: Año {anio}, Mes {mes}")

            for anio, mes in a_borrar_bloques:
                conn.execute(
                    text("DELETE FROM RetiroBloques WHERE Anio = :anio AND Mes = :mes"),
                    {"anio": anio, "mes": mes}
                )
                logging.info(f"Eliminado de RetiroBloques: Año {anio}, Mes {mes}")

            for anio, mes in a_borrar_mensual:
                conn.execute(
                    text("DELETE FROM RetiroHistoricoMensual WHERE Anio = :anio AND Mes = :mes"),
                    {"anio": anio, "mes": mes}
                )
                logging.info(f"Eliminado de RetiroHistoricoMensual: Año {anio}, Mes {mes}")

        logging.info("Limpieza de base de datos finalizada con exito")

    except Exception as e:
        logging.error(f"Error al intentar eliminar registros antiguos: {e}")

def limpieza_servidor_SQL_inyecciones():
    engine = obtener_engine_sql()

    logging.info('Revisando entradas antiguas de Reporte PPA [ INYECCIONES ]')

    existentes_inyecciones = set()

    try:
        with engine.connect() as conn:
            try:
                res_inyecciones = conn.execute(text("SELECT DISTINCT Anio, Mes FROM BalanceGenerador")).fetchall()
                existentes_inyecciones = set((row[0], row[1]) for row in res_inyecciones)
            except Exception:
                logging.warning("No se encontro la tabla BalanceGenerador")
    except Exception as e:
        logging.error(f"ERROR: No se pudo leer el datos de SQL (¿Tablas vacías o no creadas?): {e}")
        return
    
    logging.info(f"Se encontraron entradas para los meses : {existentes_inyecciones} en la tabla: BalanceGenerador")

    
    today = date.today()
    meses_esperados = set()
    for i in range(1, 25): 
        mes_calculado = today.month - i
        anio_calculado = today.year
        while mes_calculado <= 0:
            mes_calculado += 12
            anio_calculado -= 1
        meses_esperados.add((anio_calculado, mes_calculado))

    print(tuple(sorted(meses_esperados)))
    print(len(meses_esperados))

    a_borrar_inyecciones = existentes_inyecciones - meses_esperados

    try:
        with engine.begin() as conn:
            for anio, mes in a_borrar_inyecciones:
                conn.execute(
                    text("DELETE FROM BalanceGenerador WHERE Anio = :anio AND Mes = :mes"),
                    {"anio": anio, "mes": mes}
                )
                logging.info(f"Eliminado de BalanceGenerador: Año {anio}, Mes {mes}")
        logging.info("Limpieza de base de datos finalizada con exito")

    except Exception as e:
        logging.error(f"Error al intentar eliminar registros antiguos: {e}")

##########################################################################################################################################
##########################################################################################################################################

##########################################################################################################################################
###################### PROCESAR BARRAS ###################################################################################################
##########################################################################################################################################
def revisar_ultimo_arch_concat(resultados_iny_concat):
    fechas_encontradas = []
    Lista = os.listdir(resultados_iny_concat)
    for file in Lista:
        if file.startswith("Fin_iny"):
            anio,mes=extraer_anio_mes_de_nombre_iny(file)
            fechas_encontradas.append((int(anio), int(mes)))
    if fechas_encontradas:
        anio_reciente, mes_reciente = max(fechas_encontradas)
        Reciente = str(anio_reciente) + str(mes_reciente).zfill(2)
    arch_reciente = [archivo for archivo in Lista if Reciente in archivo]
    path = os.path.join(resultados_iny_concat,arch_reciente[0])
    barras_ant = pd.read_parquet(path, columns = ['Barra'])
    logging.info(barras_ant)
    return barras_ant

def descargar_barras_de_sql():
    intentos = 3
    Delay = 20
    engine = obtener_engine_sql()

    query = "SELECT * FROM dbo.MaestroSubestaciones"

    for intento in range(1, intentos + 1):
        try:
            df_barras_sql = pd.read_sql(query, con=engine)

            return df_barras_sql
        
        except Exception as e:
            logging.warning(f"Error en descarga de barras desde sql: {e}")
            if intento < intentos:
                time.sleep(Delay)
                logging.warning(f"Reintentando: {intento}")
            else:
                logging.error("No se pudo descargar la base de barras desde sql")
                raise

def Mostrar_Barras_sin_coordenadas(df):
    df = df.drop(columns=['Nombre', 'Region_Nombre', 'Nombre_SE'])
    df = df.dropna(subset=['Barra'])
    casos_sin_coordenadas = df[
        df['Longitud'].isna() |
        df['Latitud'].isna()
    ]
    if not casos_sin_coordenadas.empty:
        logging.warning(f"Se encontraron {len(casos_sin_coordenadas)} barras con coordenadas faltantes")
        logging.warning("ESTOS CASOS PUEDEN GENERAR FALLAS EN EL CALCULO DE LOS GRAFICOS Y TABLAS EN POWERBI")
        logging.warning("Es prioritario arreglarlos")
        print(casos_sin_coordenadas)
    else:
        logging.info("Todas las barras procesadas tienen coordenadas asociadas")

def subir_barras_a_sql(df):
    logging.info("Leyendo archivo para subir a SQL: Diccionario con fuzzy")
    intentos = 3
    Delay = 20
    tabla_destino = 'MaestroSubestaciones'
    engine = obtener_engine_sql()
    for intento in range(1, intentos + 1):
        try:
            with engine.begin() as conn:
                logging.info(f"Limpiando datos antiguos en la tabla '{tabla_destino}'")
                conn.execute(text(f"TRUNCATE TABLE {tabla_destino}"))
            
            logging.info(f"[SUBIENDO] Insertando {len(df)} contratos actualizados")
            df.to_sql(
                name=tabla_destino, 
                con=engine, 
                if_exists='append',
                index=False, 
                schema='dbo',
                chunksize=1000
            )
            logging.info("Base de datos actualizada correctamente.")
                
        except Exception as e:
            logging.error(f"ERROR: Fallo la actualización de la tabla {tabla_destino}: {e}")
            if intento < intentos:
                time.sleep(Delay)
                logging.warning(f"Reintentando: {intento}")
            else:
                logging.error(f"No se pudo cargar la base de barras a SQL: {e}")
                raise
        finally:
            if engine:
                engine.dispose()
                logging.info("SQL Listo.")

def revisar_faltantes_en_sql_vs_ultimo_concatenado(resultados_iny_concat):
    barras_ant = revisar_ultimo_arch_concat(resultados_iny_concat)
    barras_sql = descargar_barras_de_sql()
    Mostrar_Barras_sin_coordenadas(barras_sql)
    barras_sql = barras_sql.dropna(subset=['Barra'])
    grande = set(barras_sql['Barra'].dropna())
    peque = set(barras_ant['Barra'].dropna())
    faltantes=list(peque-grande)
    return faltantes, barras_sql, barras_ant

def limpiar_prefijo_se(df, nombre_columna):
    try:
        df[nombre_columna] = df[nombre_columna].str.replace('S/E ', '', regex=False)
        df[nombre_columna] = df[nombre_columna].str.strip()
        
        print(f"Eliminado prefijo 'S/E ' de {nombre_columna}.")
        
    except KeyError:
        print(f"Error: La columna '{nombre_columna}' no existe en el DataFrame.")
    except Exception as e:
        print(f"Error al limpiar los datos: {e}")
    return df

def obtener_mejor_match(nombre_buscar, opciones):

    if pd.isna(nombre_buscar):
        return None, 0.0
    
    resultado = process.extractOne(
        query=str(nombre_buscar), 
        choices=opciones, 
        scorer=fuzz.token_sort_ratio
    )
    
    if resultado:
        return resultado[0], resultado[1]
    return None, 0.0

