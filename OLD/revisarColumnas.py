import pandas as pd
import logging
import os

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
#           df = pd.read_parquet(a, engine='pyarrow', filters =[('Retiro', '==', 'CHUQUICAMATA')])
#           df.to_csv(a1, sep= ';')

def transformar_csv_A_parquet(PATH_IN, PATH_OUT):
    df = pd.read_csv(PATH_IN, sep = ';')
    print(df.info())
    print(df.head())
    pd.to_paquet(PATH_OUT, engine='pyarrow', compression='snappy')

def leer_columna_con_valor_en_fila_y_guardar_en_CSV(Path_Parquet, Nombre_Columna, Nombre_Fila,Path_csv):
    df = pd.read_parquet(Path_Parquet, engine='pyarrow', filters =[(Nombre_Columna, '==', Nombre_Fila)])
    df.to_csv(Path_csv, sep=';')

#Path_Parquet = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte Destilado\descargados\cmg2512_15min_formateado.parquet"
#Nombre_Columna = 'nombre_barra'
#Nombre_Fila = 'NOGALES'
#Path_csv = fr"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte Destilado\descargados\{Nombre_Fila}.csv"
#leer_columna_con_valor_en_fila_y_guardar_en_CSV(Path_Parquet, Nombre_Columna, Nombre_Fila,Path_csv)

def info_df(PATH_IN):
    df = pd.read_parquet(PATH_IN, engine='pyarrow')
    #df = pd.read_csv(PATH_IN, sep = ';')
    logging.info(df.info())
    #print(df.head())
    #print(df['Nombre_Corto'].unique())
    #logging.info(df.head())
    #print(len(df['nombre_barra_cmg'].unique()))

#r = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\descargados\compraventas2511.csv"
#info_df(r)

#r = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\procesados_iny"


'''
lista = os.listdir(r)
for file in lista:
    path = os.path.join(r,file)
    df = pd.read_parquet(path)
    file = os.path.splitext(file)[0]
    df.to_csv(os.path.join(r,f"{file}.csv"))
'''

#r = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\procesados\retiros_tipo_LeT202601.parquet"

#Subdivisiones_codelco = ["CODELCO","CODELCO A-D.ALMAGRO", "CODELCO A-EL LLANO", "CODELCO A-MAQUI", "CODELCO ANDINA-SALADILLO", "CODELCO CHILE - DIVISION ANDINA", "CODELCO CHILE DIVISION ANDINA", "CODELCO MINEROS", "CODELCO VENTANAS", "DESALADORA_CODELCO", "MIN_CODELCO_SALAR", "MINERA_MINISTRO_HALES_CODELCO", "CHUQUICAMATA", "MIN_RTOMIC", "MINERA_GABY", "EMPRESA NACIONAL DE MINERIA"]

#df = pd.read_parquet(r, filters=[('Retiro','in',Subdivisiones_codelco)])

r = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\resultados_iny_concat\Fin_iny202501.parquet"
#df = pd.read_parquet(r)
info_df(r)
#df.to_parquet(r, index=False)