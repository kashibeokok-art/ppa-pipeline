import os
import pandas as pd
import logging
##############################################
import rutas_config                          #  Importe de rutas de carpetas
import funciones                             #  Importe de funciones utilizadas
##############################################
import sys

def procesar_datos_contratos(descargados_contratos_folder, resultados_contratos_folder):
    try:
        logging.info("INICIANDO PROCESAMIENTO DE CONTRATOS ")
        
        #output_csv = os.path.join(resultados_contratos_folder, "Contratos_Libres(Procesados).csv")
        output_parquet_sql = os.path.join(resultados_contratos_folder, "Contratos_SQL.parquet")

        last_file, fecha_ingreso = funciones.obtener_archivo_mas_reciente(descargados_contratos_folder)
        if not last_file:
            logging.info("Proceso abortado: No hay archivos para procesar.")
            return

        logging.info(f"Leyendo archivo de Excel: {os.path.basename(last_file)}")
        df = pd.read_excel(last_file, header=1, engine='openpyxl')
        
        columnas_interes = [
            'Id Contrato', 'Empresa Suministradora', 'Rut Suministradora', 
            'Tipo Suministrador', 'Tipo Contrato', 'Red Distribuidora', 
            'Tipo Cliente', 'Empresa Cliente', 'Rut Empresa Cliente',
            'Inicio', 'Término', 'Fecha Renovación', 'Región',
            'Sector Económico', 'Subsector Económico', 
            'ID puntos de Suministro', 'Listado de puntos de Suministro', 
            'ID puntos de Retiro', 'Listado de puntos de Retiro'
        ] + [f'Energía {year}' for year in range(1986, 2061)]
        
        columnas_presentes = [col for col in columnas_interes if col in df.columns]
        df = df[columnas_presentes]

        logging.info("LIMPIANDO DATOS")
        df_limpio = funciones.limpiar_y_calcular_energia(df)

        logging.info("DESIGNANDO NUEVOS O ANTIGUO")
        
        df_final = funciones.actualizar_historico_contratos(df_limpio, output_parquet_sql, fecha_ingreso)

        logging.info("PREPARANDO PARA SQL")
        df_para_sql = funciones.preparar_columnas_para_sql(df_final)
        
        df_para_sql = funciones.limpiar_filas_para_sql(df_para_sql)

        df_para_sql.to_parquet(output_parquet_sql, index=False, engine='pyarrow')

        #logging.info("REINICIANDO TABLA SQL")
        #funciones.formatear_y_guardar_salida(df_para_sql, output_parquet_sql)

        logging.info("CARGANDO A SQL")
        funciones.subir_contratos_a_sql(output_parquet_sql)

        logging.info("CONTRATOS EXITOSO")
    except Exception as e:
        logging.error(f"Error en el procesamiento de contratos: {e}")
        sys.exit(1)

#f
if __name__ == "__main__":

    logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    try:
        descargados_contratos_folder = rutas_config.DIRECTORIO_DESCARGA_CONTRATOS
        resultados_contratos_folder = rutas_config.DIRECTORIO_RESULTADOS_CONTRATOS

        funciones.descargar_datos_contratos(5, descargados_contratos_folder)
        procesar_datos_contratos(descargados_contratos_folder, resultados_contratos_folder)
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error en main diario: {e}")
        sys.exit(1)
    
