import os
import pandas as pd
import glob
import shutil
import logging
import sys
import subprocess

##############################################
import rutas_config                          #  Importe de rutas de carpetas
import funciones                             #  Importe de funciones utilizadas
##############################################

def procesar_ZIP(download_folder):
    logging.info("222222222222222222222222222222222222222222222222222222 \n")

    logging.info("Iniciando procesamiento de archivos ZIP \n")
    zip_files = funciones.find_all_zips(download_folder)
    if not zip_files:
        logging.info(f"No se encontro ningun archivo .zip en '{download_folder}'.")
        return
    for zip_file in zip_files:
        extracted_path = funciones.extract_zip(zip_file)
        if extracted_path:
            numero_mes_anio = os.path.basename(extracted_path)
            funciones.limpiar_extraccion_descargada(extracted_path)
            funciones.renombrar_medidas(extracted_path, numero_mes_anio)
        else:
            logging.error(f"Error al extraer el archivo ZIP: '{zip_file}'.")
            continue
        try:
            funciones.extraer_zips_internos(extracted_path)
            funciones.copiar_archivos_utiles(extracted_path, download_folder)
        except Exception as e:
            logging.error(f"Error al procesar los archivos de '{extracted_path}': {e}")
        try:
            os.remove(zip_file)
            logging.error(f"Archivo ZIP '{zip_file}' eliminado.")
        except FileNotFoundError:
            logging.error(f"Archivo ZIP '{zip_file}' no existe, no se puede eliminar.")
        except PermissionError:
            logging.error(f"No se tienen permisos para eliminar el archivo ZIP '{zip_file}'.")
        except Exception as e:
            logging.error(f"ERROR al eliminar '{zip_file}': {e}")

    funciones.eliminar_archivos_y_subcarpetas(download_folder)

    logging.info("222222222222222222222222222222222222222222222222222222 \n")

def ACCESS(download_folder, procesados_folder):
    archivos_mdb = glob.glob(os.path.join(download_folder, '*.mdb'))
    if not archivos_mdb:
        logging.info("No se encontraron archivos .mdb en la carpeta.")
        return
    for archivo_mdb in archivos_mdb:
        nombre_base = os.path.basename(archivo_mdb)
        anio, mes = funciones.extraer_anio_mes_de_nombre(nombre_base)
        if anio is None or mes is None:
            continue
        
        pq_LeT = funciones.obtener_nombre_con_fecha(os.path.join(procesados_folder, "retiros_tipo_LeT.parquet"), anio, mes)
        pq_LeD = funciones.obtener_nombre_con_fecha(os.path.join(procesados_folder, "retiros_tipo_LeD.parquet"), anio, mes)
        pq_R = funciones.obtener_nombre_con_fecha(os.path.join(procesados_folder, "retiros_tipo_R.parquet"), anio, mes)

        if not (os.path.exists(pq_R) and os.path.exists(pq_LeT) and os.path.exists(pq_LeD)):
            logging.info(f"Procesando {nombre_base}")
            funciones.extraer_R(archivo_mdb, procesados_folder)
            funciones.extraer_L(archivo_mdb, procesados_folder)
            funciones.extraer_LD(archivo_mdb, procesados_folder)
        else:
            logging.info(f"Archivos ya existen para {nombre_base}. No se procesa.")

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

def Dia_mensual_representativo(procesados_folder, resultados_folder):
    missing_files = funciones.find_missing_files(procesados_folder, resultados_folder)

    if not missing_files:

        logging.info("No hay archivos pendientes de procesar de retiros.")

        return

    else:

        logging.info("Archivos pendientes por procesar de retiros:")

        for file in missing_files:
            logging.info(file)
    for file in missing_files:

        logging.info(f"Procesando archivo: {file}")

        cols_retiros = ['Hora Mensual', 'Medida_kWh','Barra', 'Retiro', 'Mes', 'Año']
        df= pd.read_parquet(file, engine="pyarrow", columns=cols_retiros)
        df = funciones.drop_unnamed_column(df)
        df = funciones.normalize_year_column(df)

        logging.info("Calculando el consumo mensual por barra")

        df_mensual = funciones.calcular_consumo_mensual_barra(df)

        logging.info(f"Guardando archivo de retiro mensual total en {resultados_folder}")

        funciones.guardar_retiro_mensual_barra(df_mensual, file, resultados_folder)
        del df_mensual

        logging.info("Comenzando preprocesamiento de los retiros")

        df = funciones.Preprocesar_dataframe(df)

        logging.info("Preprocesamiento listo")

        logging.info("Calculando retiro por bloque horario")

        df_bloque = funciones.calcular_perfil_por_bloque(df)

        logging.info("Guardando retiro promedio por bloque")

        funciones.guardar_resultado_bloques(df_bloque, file, resultados_folder)

        logging.info("OK")

        logging.info("Calculando retiro promedio horario mensual y por dia habil no habil")

        df = funciones.calcular_medidas(df)
        df = funciones.Promedio_habilNohabil_a_columna(df)

        logging.info("Guardando retiro promedio horario mensual")

        funciones.guardar_resultado_individual(df, file, resultados_folder)

def subir_sql(resultados_folder):
    funciones.subir_carpeta_a_sql(resultados_folder)

def eliminar_archivos_access(carpeta_objetivo):
    logging.info(f"Iniciando limpieza de archivos Access en: {carpeta_objetivo}")
    
    extensiones = ["*.mdb", "*.accdb"]
    archivos_eliminados = 0
    
    for ext in extensiones:

        ruta_busqueda = os.path.join(carpeta_objetivo, ext)
        archivos_encontrados = glob.glob(ruta_busqueda)
        
        for archivo in archivos_encontrados:

            try:
                os.remove(archivo)
                logging.info(f"Archivo eliminado: {os.path.basename(archivo)}")
                archivos_eliminados += 1
            except PermissionError:
                logging.warning(f"No se pudo eliminar {os.path.basename(archivo)}. ¿Esta abierto en otro programa?")
            except Exception as e:
                logging.error(f"Error inesperado al eliminar {os.path.basename(archivo)}: {e}")
                
    logging.info(f"Limpieza completada. Total de archivos Access eliminados: {archivos_eliminados}")

if __name__ == "__main__":

    logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    download_folder = rutas_config.DIRECTORIO_DESCARGA
    procesados_folder = rutas_config.DIRECTORIO_PROCESADOS
    resultados_folder = rutas_config.DIRECTORIO_RESULTADOS
    cache_folder = rutas_config.DIRECTORIO_CACHE
    cache_file_path = os.path.join(rutas_config.DIRECTORIO_CACHE,"cache_ruts_empresas.json")
    base_sii = rutas_config.DIRECTORIO_sii
    hom_retiros = os.path.join(rutas_config.DATA_DIR, "Hom_Retiros.py")
    main_iny = os.path.join(rutas_config.DATA_DIR, "main_mensual_iny.py")

    logging.info("============================================================ \n")
    logging.info("Iniciando procesamiento de retiros mensual \n")
    logging.info("============================================================\n")

    try:

        #ACTUALIZAR_SII(base_sii)

        faltantes = sorted(funciones.revisar_archivos_faltantes(resultados_folder))
            
        if not faltantes:
            logging.info('Retiros al dia, no hay archivos pendientes')
            sys.exit(0)

        logging.info('Faltan los siguientes meses para procesar:')
        logging.info(faltantes)

        for tupla in faltantes:

            logging.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \n')
            logging.info(f"Iniciando descarga y procesamiento de Retiro {tupla} \n")
            logging.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \n')

            Links = funciones.Obtener_links_de_Plabacom()
            Link_descarga = funciones.Filtrar_link_descarga_necesario(Links, tupla)
            if not Link_descarga:
                continue
            else:
                funciones.Descargar_Archivo(Link_descarga, download_folder, max_intentos=3)
                intentos = 3
                for intento in range(1, intentos + 1):
                    try:
                        procesar_ZIP(download_folder)
                    except Exception as e:
                        if intento < intentos:
                            logging.warning(f"Reintentando: {intento}")
                        else:
                            logging.error(f"fallo en el codigo de Procesamiento de ZIP: {e}")
                for intento in range(1, intentos + 1):
                    try:
                        ACCESS(download_folder, procesados_folder)
                    except Exception as e:
                        if intento < intentos:
                            logging.warning(f"Reintentando: {intento}")
                        else:
                            logging.error(f"fallo en el codigo de Procesamiento ACCESS: {e}")
                for intento in range(1, intentos + 1):
                    try:
                        eliminar_archivos_access(download_folder)
                    except Exception as e:
                        if intento < intentos:
                            logging.warning(f"Reintentando: {intento}")
                        else:
                            logging.error(f"fallo en el codigo de eliminacion de archivos ACCESS: {e}")
                for intento in range(1, intentos + 1):
                    try:
                        Dia_mensual_representativo(procesados_folder, resultados_folder)
                    except Exception as e:
                        if intento < intentos:
                            logging.warning(f"Reintentando: {intento}")
                        else:
                            logging.error(f"fallo en el codigo de CALCULO de retiros: {e}")
                for intento in range(1, intentos + 1):
                    try:
                        subir_sql(resultados_folder)
                    except Exception as e:
                        if intento < intentos:
                            logging.warning(f"Reintentando: {intento}")
                        else:
                            logging.error(f"fallo en el codigo de Subir retiros a SQL: {e}")

                logging.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \n')
                logging.info(f"Finalizado descarga y procesamiento de Retiro {tupla} \n")
                logging.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \n')

            intentos = 3
            for intento in range(1, intentos + 1):
                try:
                    subprocess.run([sys.executable, main_iny], check=True)
                    break
                except Exception as e:
                    if intento < intentos:
                        logging.warning(f"Reintentando: {intento}")
                    else:
                        logging.error(f"fallo en el codigo de inyecciones: {e}")
                        raise
        intentos = 3
        for intento in range(1, intentos + 1):
            try:
                subprocess.run([sys.executable, hom_retiros], check=True)
                break
            except Exception as e:
                if intento < intentos:
                    logging.warning(f"Reintentando: {intento}")
                else:
                    logging.error(f"fallo en el codigo de homologacion: {e}")
                    raise
        

    except Exception as e:
        logging.error(f"Error en main_mensual: {e}")
        raise
    finally:
        funciones.limpieza_download_folder(download_folder)

        funciones.limpieza_servidor_SQL_retiros()

        funciones.limpieza_servidor_SQL_inyecciones()