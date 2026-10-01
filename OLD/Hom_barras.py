import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import rutas_config
import funciones
from sqlalchemy import text
import time
import logging
from rapidfuzz import process, fuzz
import sys

resultados_iny_concat = rutas_config.DIRECTORIO_RESULTADOS_INY_CONCAT

def crear_sesion():
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    return session

def descargar_desde_api(endpoint):
    base_url = "https://api-infotecnica.coordinador.cl/v1/"
    url = f"{base_url}{endpoint.lstrip('/')}"
    
    session = crear_sesion()
    
    try:
        respuesta = session.get(url, verify=False, timeout=30)
        respuesta.raise_for_status()
        
        datos = respuesta.json()

        if isinstance(datos, dict):
            registros = datos.get('items', datos.get('results', datos.get('data', [datos])))
        else:
            registros = datos
            
        df = pd.json_normalize(registros)
        return df

    except requests.exceptions.RequestException as e:
        return pd.DataFrame()

def revisar_ultimo_arch_concat():
    fechas_encontradas = []
    Lista = os.listdir(resultados_iny_concat)
    for file in Lista:
        if file.startswith("Fin_iny"):
            anio,mes=funciones.extraer_anio_mes_de_nombre_iny(file)
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
    engine = funciones.obtener_engine_sql()

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

    tabla_destino = 'MaestroSubestaciones'
    engine = funciones.obtener_engine_sql()

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

def Procesar_barras(resultados_iny_concat):
    try:
        faltantes, barras_sql, barras_ant = revisar_faltantes_en_sql_vs_ultimo_concatenado(resultados_iny_concat)

        if not faltantes:
            print('Todas las barras listas')
        else:
            print("Faltan:"*30)
            print(faltantes)
            respaldo_sql = barras_sql.copy()
            barras_sql = limpiar_prefijo_se(barras_sql, "Nombre_SE")
            lista_maestra_se = barras_sql['Nombre_SE'].dropna().unique().tolist()
            barras_ant[['Match_Nombre_SE', 'Score_Similitud']] = barras_ant['Barra'].apply(
            lambda x: pd.Series(obtener_mejor_match(x, lista_maestra_se))
            )
            respaldo_limpio = respaldo_sql[['Nombre_SE', 'latitud', 'longitud']].drop_duplicates(subset=['Nombre_SE'])
            df_resultado = pd.merge(
            left=barras_ant,
            right=respaldo_limpio,
            left_on='Match_Nombre_SE',
            right_on='Nombre_SE',
            how='left'
            )
            subir_barras_a_sql(df_resultado)
    except Exception as e:
        logging.error(f"Error al comparar barras: {e}")
        sys.exit(1)