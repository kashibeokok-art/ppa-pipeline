import pandas as pd
import funciones
import datetime as dt
import logging
import numpy as np
from scipy import stats

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)


archivo_csv = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\descargados\nortetrans2511.csv"

columnas_iny = ['nombre_barra', 'tension', 'Fecha_Medicion', 'medida_1', 'medida_2', 'medida_2a', 'medida_3', 'Nombre_Corto', 'tipo','descripcion']
df = pd.read_csv(archivo_csv, sep=';', usecols=columnas_iny, low_memory=False)
print(df.info())
df = funciones.drop_unnamed_column_iny(df)
#df = funciones.leer_y_filtrar_TIPO(df, tipos_validos=['C_FIN','C_FIS','L', 'L_D', 'R','G'])
df = funciones.leer_y_filtrar_TIPO(df, tipos_validos=['G'])

df = df.drop(columns='tipo')

print(df['Nombre_Corto'].unique())
#df['MEDIDA'] = df[['medida_1', 'medida_2', 'medida_2a', 'medida_3']].mode(axis=1)[0]


matriz_valores = df[['medida_1', 'medida_2','medida_2a' ,'medida_3']].values

resultados = stats.mode(matriz_valores, axis=1, keepdims=False)

df['MEDIDA'] = resultados[0]
df = df.drop(columns=['medida_1','medida_2','medida_2a','medida_3'])
df['MEDIDA'] = pd.to_numeric(df['MEDIDA'], errors='coerce').fillna(0.0)

r = r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\Engiequincemin.csv"
df1 = df[df['Nombre_Corto']=='ENGIE']
df1.to_csv(r,index=False)


df['Fecha_Medicion'] = pd.to_datetime(df['Fecha_Medicion'])

df['Anio'] = df['Fecha_Medicion'].dt.year
df['Mes'] = df['Fecha_Medicion'].dt.month
df['Hora'] = df['Fecha_Medicion'].dt.hour + 1

df['Mes'] = df['Mes'].astype(int)
df['Anio'] = df['Anio'].astype(int)
df['Hora'] = df['Hora'].astype(int)

df = df.drop(columns='Fecha_Medicion')
#df = df.drop_duplicates()
columnas_iny = ['nombre_barra', 'tension', 'Anio','Mes', 'Nombre_Corto','Hora','descripcion']
grouped = df.groupby(columnas_iny)['MEDIDA']
df['MEDIDA'] = grouped.transform('sum')
df['MEDIDA'] = df['MEDIDA']/1000
df = df.rename(columns={'MEDIDA':'Medida_MWh'})
df = df.drop_duplicates()

r=r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\Engiehorario.csv"
df2 = df[df['Nombre_Corto']=='ENGIE']
df2.to_csv(r,index=False)


r=r"C:\Users\caraya.practica\OneDrive - Generadora Metropolitana\Escritorio\Reporte PPA V2\Engiebloques.csv"
df2 = df[df['Nombre_Corto']=='ENGIE']
df2.to_csv(r,index=False)
print(df.info())
print(df.head())

#df_horario = df.groupby(
##    columnas_iny + [pd.Grouper(key='Fecha_Medicion', freq='h')]
#    )['MEDIDA'].sum()#.reset_index()
#print(df_horario.info())
#print(df_horario.head())

#df_horario.to_csv()

# =SI(Y(G2>=9;G2<=18);"B";SI(Y(G2>=19;G2<=23);"C";"A"))