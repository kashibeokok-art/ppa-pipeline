import os
import pandas as pd
import glob
import logging
import re
import funciones
import rutas_config
import sys
import numpy as np

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
download_folder = rutas_config.DIRECTORIO_DESCARGA
procesados_iny_folder = rutas_config.DIRECTORIO_PROCESADOS_INY 
resultados_iny_folder = rutas_config.DIRECTORIO_RESULTADOS_INY
resultados_iny_concat_folder = rutas_config.DIRECTORIO_RESULTADOS_INY_CONCAT
procesados_folder = rutas_config.DIRECTORIO_PROCESADOS


def Procesar_barras(resultados_iny_concat):
    try:
        faltantes, barras_sql, barras_ant = funciones.revisar_faltantes_en_sql_vs_ultimo_concatenado(resultados_iny_concat)

        if not faltantes:
            logging.info('Todas las barras listas')
        else:
            logging.warning("Faltan:"*30)
            logging.warning(faltantes)

            lista_maestra_se = barras_sql['Nombre_SE'].dropna().unique().tolist()
            barras_ant[['Match_Nombre_SE', 'Score_Similitud']] = barras_ant['Barra'].apply(
            lambda x: pd.Series(funciones.obtener_mejor_match(x, lista_maestra_se))
            )
            respaldo_limpio = barras_sql[['Nombre_SE', 'latitud', 'longitud']].drop_duplicates(subset=['Nombre_SE'])
            df_resultado = pd.merge(
            left=barras_ant,
            right=respaldo_limpio,
            left_on='Match_Nombre_SE',
            right_on='Nombre_SE',
            how='left'
            )
            df_resultado = df_resultado.drop_duplicates()
            funciones.subir_barras_a_sql(df_resultado)
    except Exception as e:
        logging.error(f"Error al comparar barras: {e}")

def listar_cmgs(download_folder, patron_csv="cmg*.csv"):
    path_cmg = os.path.join(download_folder, patron_csv)
    lista_archivos_cmg = glob.glob(path_cmg)
    
    if not lista_archivos_cmg:
        logging.error(f"No se encontró ningún archivo con el patrón '{patron_csv}' en la carpeta de descargas.")
        raise FileNotFoundError("Sin archivo CMG para procesar.")
        
    ruta_cmg = lista_archivos_cmg[0]
    nombre_base_cmg = os.path.basename(ruta_cmg)
    
    coincidencia = re.search(r'cmg(\d{2})(\d{2})', nombre_base_cmg)
    
    if not coincidencia:
        logging.error(f"El archivo '{nombre_base_cmg}' fue encontrado, pero no coincide con el formato de fecha esperado (ej. cmg2602.csv).")
        raise ValueError("Formato de nombre CMG inválido.")
        
    anio_cmg, mes_cmg = coincidencia.groups()
    
    logging.info(f"CMG detectado exitosamente: {nombre_base_cmg} (Año: 20{anio_cmg}, Mes: {mes_cmg})")
    
    return ruta_cmg, anio_cmg, mes_cmg

def Procesar_cmg(r):
    Cols = ['nombre_barra_cmg', 'CMg[USD/MWh]', 'HORA', 'FECHA']

    df = pd.read_csv(r,sep=';', usecols=Cols)

    df['Fecha_Medicion'] = pd.to_datetime(df['FECHA'].astype(str), format='%Y%m%d')

    df = df.rename(columns={'nombre_barra_cmg':'Barra', 'HORA':'Hora'})
    df['Dia'] = df['Fecha_Medicion'].dt.day
    df = df.drop( columns=['FECHA', 'Fecha_Medicion'])
    df = df.groupby(['Hora','Barra','Dia'])['CMg[USD/MWh]'].mean().reset_index()
    return df

def procesar_archivos_inyecciones(anio_cmg, mes_cmg, cmg, download_folder, procesados_iny_folder, resultados_iny_folder, columnas_preprocesamiento):
    archivos_inyecciones = [
        f'nortetrans{anio_cmg}{mes_cmg}.csv',
        f'nortedist{anio_cmg}{mes_cmg}.csv', 
        f'surtrans{anio_cmg}{mes_cmg}.csv',
        f'surdist{anio_cmg}{mes_cmg}.csv',
        f'compraventas{anio_cmg}{mes_cmg}.csv'
    ]
    
    for arch_iny in archivos_inyecciones:
        path_iny = os.path.join(download_folder, arch_iny)
        archivos_iny_encontrados = glob.glob(path_iny)
        
        if not archivos_iny_encontrados:
            logging.info(f"No se encontraron archivos {arch_iny}")
            continue

        for ruta_iny in archivos_iny_encontrados:
            nombre_base_iny = os.path.basename(ruta_iny)
            
            nombre_sin_extension = re.sub(r'\d+', '', os.path.splitext(nombre_base_iny)[0])

            anio_iny, mes_iny = funciones.extraer_anio_mes_de_nombre(nombre_base_iny)
            
            pq_in = funciones.obtener_nombre_con_fecha(os.path.join(procesados_iny_folder, f"procesado_{nombre_sin_extension}.parquet"), anio_iny, mes_iny)
            pq_out = os.path.join(resultados_iny_folder, f"resultado_{nombre_sin_extension}{anio_iny}{mes_iny}.parquet")

            if not os.path.exists(pq_out):
                logging.info(f"Procesando inyección: {nombre_base_iny}")
                df = pd.read_csv(ruta_iny, sep=';', usecols=columnas_preprocesamiento)
                df = funciones.preprocesar_csv_raw(df, pq_in, cmg)
                df = funciones.calcular_bloques(df)
                df.to_parquet(pq_out, compression='snappy', engine='pyarrow', index=False)
            else:
                logging.info(f"[OMITIDO] El archivo {nombre_base_iny} ya estaba procesado.")

def procesar_archivos_retiros(anio_cmg, mes_cmg, cmg, procesados_folder, resultados_iny_folder):
    archivos_retiros = [
        f'retiros_tipo_R20{anio_cmg}{mes_cmg}.parquet', 
        f'retiros_tipo_LeT20{anio_cmg}{mes_cmg}.parquet', 
        f'retiros_tipo_LeD20{anio_cmg}{mes_cmg}.parquet'
    ]
    
    for arch_retiros in archivos_retiros:
        path_ret = os.path.join(procesados_folder, arch_retiros)
        archivos_ret = glob.glob(path_ret)
        
        if not archivos_ret:
            logging.info(f"No se encontraron archivos {arch_retiros}")
            continue
        
        for ruta_ret in archivos_ret:
            nombre_base_ret = os.path.basename(ruta_ret)
            if nombre_base_ret.startswith("retiros_tipo_R"):
                nombre_base_ret = f"retiros_tipo_R{anio_cmg}{mes_cmg}.parquet"
            if nombre_base_ret.startswith("retiros_tipo_LeT"):
                nombre_base_ret = f"retiros_tipo_LeT{anio_cmg}{mes_cmg}.parquet"
            if nombre_base_ret.startswith("retiros_tipo_LeD"):
                nombre_base_ret = f"retiros_tipo_LeD{anio_cmg}{mes_cmg}.parquet"
            
            anio_ret, mes_ret = funciones.extraer_anio_mes_de_nombre(nombre_base_ret)
            
            nombre_base_limpia = re.sub(r'\d+', '', os.path.splitext(nombre_base_ret)[0])
            
            pq_out_r = os.path.join(resultados_iny_folder, f"resultado_{nombre_base_limpia}{anio_ret}{mes_ret}.parquet")
            
            if not os.path.exists(pq_out_r):
                logging.info(f"Procesando retiros: {nombre_base_ret}")
                tipo = 'R' if nombre_base_ret.startswith('retiros_tipo_R') else 'L'
                df_retiro = pd.read_parquet(ruta_ret, columns=['Suministrador','Hora Mensual','Medida_kWh','Barra','Mes','Año'])
                df_retiro = funciones.procesar_ret_para_iny(df_retiro, tipo, cmg)
                df_retiro.to_parquet(pq_out_r, index=False)
            else:
                logging.info(f"[OMITIDO] El archivo {nombre_base_ret} ya estaba procesado.")

if __name__ == "__main__":

    logging.info("============================================================ \n")
    logging.info("Iniciando procesamiento de inyecciones mensual \n")
    logging.info("============================================================\n")

    columnas_preprocesamiento = [
                        'nombre_barra',
                        'tension', 
                        'Fecha_Medicion', 
                        'medida_3', 
                        'Nombre_Corto', 
                        'tipo',
                        'descripcion',
                        'ID_Contrato'
                    ]

    ruta_cmg, anio_cmg, mes_cmg = listar_cmgs(download_folder, patron_csv="cmg*.csv")

    cmg = Procesar_cmg(ruta_cmg)

    procesar_archivos_inyecciones(anio_cmg, mes_cmg, cmg, download_folder, procesados_iny_folder, resultados_iny_folder, columnas_preprocesamiento)

    procesar_archivos_retiros(anio_cmg, mes_cmg, cmg, procesados_folder, resultados_iny_folder)

    fechas_ya_procesadas = funciones.fechas_listas(resultados_iny_concat_folder)

    dfs_por_fecha = funciones.agrupar_archvios_por_fecha(resultados_iny_folder, fechas_ya_procesadas)


    logging.info("============================================================ \n")
    logging.info("Iniciando procesamiento de retiros de Suministradores \n")
    logging.info("============================================================\n")

try:
        fechas_ya_procesadas = funciones.fechas_listas(resultados_iny_concat_folder)
        
        # Como inyecciones y retiros están en la misma carpeta, esta función los agrupará juntos automáticamente.
        
        print(dfs_por_fecha)

        # Definimos las columnas maestras que queremos en la tabla final
        columnas_maestras = [
            "Barra", "Suministrador", "tipo", "descripcion", "Anio", 
            "Mes", "Nombre_Bloque", "Medida_GWh", "ID_Contrato", "Valorizado[USD]"
        ]

        for fecha, rutas in dfs_por_fecha.items():
            anio, mes = fecha
            
            # 1. Leemos todos los archivos (sin forzar columnas aún para evitar que explote si falta una)
            lista_dfs = [pd.read_parquet(r) for r in rutas]
            
            # 2. Concatenamos. Pandas alinea las columnas y rellena con nulos lo que no coincida
            df_mes_anio = pd.concat(lista_dfs, ignore_index=True)
            
            # 3. Nos aseguramos de que existan todas las columnas maestras (si alguna falta, la creamos vacía)
            for col in columnas_maestras:
                if col not in df_mes_anio.columns:
                    df_mes_anio[col] = None
                    
            # 4. Ahora sí, filtramos y ordenamos la tabla con las columnas exactas
            df_mes_anio = df_mes_anio[columnas_maestras]

            # 5. Limpieza de textos
            columnas_str = ["Barra", "Suministrador", "tipo", "descripcion", "Nombre_Bloque"]
            for col in columnas_str:
                if col in df_mes_anio.columns:
                    df_mes_anio[col] = df_mes_anio[col].astype(str).replace(['nan', 'None', '<NA>'], None)
            
            # 6. Transformaciones finales
            df_mes_anio["Medida_GWh"] = df_mes_anio["Medida_GWh"].astype(float)
            df_mes_anio = funciones.agregar_tecnologia(df_mes_anio)
            df_mes_anio = funciones.definir_tipo_columnas(df_mes_anio)

            # 7. Guardado
            nombre_archivo = f"Fin_iny{anio}{str(mes).zfill(2)}.parquet"
            ruta_salida = os.path.join(resultados_iny_concat_folder, nombre_archivo)
            
            df_mes_anio.to_parquet(ruta_salida, compression='snappy', index=False)
            logging.info(f"Archivo fusionado para {anio} y {mes}: {nombre_archivo}")

        # Post-procesamiento
        funciones.Cruzar_nombre_suministradores_cfinfis(resultados_iny_concat_folder)

except Exception as e:
    logging.error(f"Fallo en agregar cmg y procesar inyecciones con retiros: {e}")


funciones.subir_iny_a_sql(resultados_iny_concat_folder)



Procesar_barras(resultados_iny_concat_folder)