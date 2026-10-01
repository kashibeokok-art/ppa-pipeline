import pandas as pd
import os
import urllib
from sqlalchemy import create_engine, text

################## DATOS DELICADOS #######################
def obtener_engine_sql():
    print("Conectandose al servidor SQL")
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
##########################################################

def subir_diccionario_a_sql(excel_diccionario):
    print(f"Leyendo archivo para subir a SQL: {excel_diccionario}")
    
    try:
        df = pd.read_excel(excel_diccionario)
    except Exception as e:
        print(f"Error al leer el archivo excel: {e}")
        return
    
    for col in df:
        df[col] = df[col].astype(str)

    tabla_destino = 'DiccionarioSuministradores'
    engine = obtener_engine_sql()

    try:
        with engine.begin() as conn:
            print(f"Limpiando datos antiguos en la tabla '{tabla_destino}'")
            conn.execute(text(f"TRUNCATE TABLE {tabla_destino}"))
        
        print(f"[SUBIENDO] Insertando {len(df)} contratos actualizados")
        df.to_sql(
            name=tabla_destino, 
            con=engine, 
            if_exists='append',
            index=False, 
            schema='dbo',
            chunksize=1000
        )
        print("Base de datos actualizada correctamente.")
            
    except Exception as e:
        print(f"ERROR: Fallo la actualización de la tabla {tabla_destino}: {e}")
        raise
            
    finally:
        if engine:
            engine.dispose()
            print("SQL Listo.")

path = os.getcwd()
path_dic = os.path.join(path, "diccionario_suministradores.xlsx")
subir_diccionario_a_sql(path_dic)