import os
import re
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import rutas_config
from thefuzz import process, fuzz
import logging
import funciones
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

resultados_folder = rutas_config.DIRECTORIO_RESULTADOS
resultados_iny_folder = rutas_config.DIRECTORIO_RESULTADOS_INY
mapa_folder = rutas_config.DIRECTORIO_MAPA

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def limpiar_nombre_sucio(texto: str) -> str:
    if pd.isna(texto) or not isinstance(texto, str): 
        return ""
        
    texto = texto.upper()
    texto = re.sub(r'_+\d+$', '', texto)
    texto = texto.replace('_', '').replace('.', '')
    texto = re.sub(r'\bS\s+', '', texto)
    texto = re.sub(r'\bSTA\s+', '', texto)
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)
    
    return " ".join(texto.split())

def limpiar_nombre_oficial(texto: str) -> str:
    if pd.isna(texto) or not isinstance(texto, str): 
        return ""
        
    texto = texto.upper()
    texto = re.sub(r'^(BA\s+)?S/E\s+', '', texto)       
    texto = re.sub(r'^TAP\s+OFF\s+', '', texto)         
    texto = re.sub(r'\d+(\.|,)?\d*\s*K?V.*', '', texto) 
    texto = re.sub(r'\(.*?\)', '', texto)               
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)
    texto = re.sub(r'\bCENTRAL\b\s*', '', texto)
    texto = re.sub(r' ', '', texto)
    
    return " ".join(texto.split())

def procesar_dataframe_maestro(df_se: pd.DataFrame, df_barras: pd.DataFrame) -> pd.DataFrame:
    if df_se.empty or df_barras.empty:
        return pd.DataFrame()

    df_full = pd.merge(df_se, df_barras, left_on='id', right_on='id_subestacion', how='left')
    
    df_full['nombre_barra'] = df_full['nombre_barra'].fillna(df_full['nombre_SE'])
    df_full = df_full.drop(columns=['id_subestacion'], errors='ignore')
    
    correcciones_manuales = {
        "S/E CABO LEONES II": (-71.225, -28.435),
        "TAP OFF MAESTRANZA": (-70.762, -34.208),
        "S/E CHIU CHIU": (-68.65, -22.342),
        "S/E SANTA CRUZ": (-71.3657, -34.6388)
    }
    
    for nombre, (lon, lat) in correcciones_manuales.items():
        mask = df_full['nombre_SE'] == nombre
        if mask.any():
            df_full.loc[mask, ['longitud', 'latitud']] = [lon, lat]
            
    return df_full

def descargar_maestro_desde_api() -> pd.DataFrame:
    
    df_se_raw = descargar_desde_api("subestaciones/extended/")
    df_barras_raw = descargar_desde_api("barras/")
    
    if df_se_raw.empty or df_barras_raw.empty:
        return pd.DataFrame()

    cols_se_deseadas = ["id", "nombre", "region_nombre", "longitud", "latitud"]
    cols_se_ok = [c for c in cols_se_deseadas if c in df_se_raw.columns]
    
    df_se = df_se_raw[cols_se_ok].copy()
    df_se = df_se.rename(columns={'nombre': 'nombre_SE'})
    
    cols_barras_deseadas = ["id_subestacion", "nombre"]
    cols_barras_ok = [c for c in cols_barras_deseadas if c in df_barras_raw.columns]
    
    df_barras = df_barras_raw[cols_barras_ok].copy()
    df_barras = df_barras.rename(columns={'nombre': 'nombre_barra'})
    
    return procesar_dataframe_maestro(df_se, df_barras)

def obtener_barras_recientes(resultados_folder):
    prefijos = [
        'mensual_retiros_tipo_R', 
        'mensual_retiros_tipo_LeT', 
        'mensual_retiros_tipo_LeD'
    ]
    
    archivos_recientes = {prefijo: (0, 0, "") for prefijo in prefijos}

    lista_archivos = [f for f in os.listdir(resultados_folder) if f.endswith('.parquet')]
    
    for file in lista_archivos:
        for prefijo in prefijos:
            if file.startswith(prefijo):
                match = re.search(r'(\d{4})(\d{2})', file)
                if match:
                    anio_file = int(match.group(1))
                    mes_file = int(match.group(2))
                    
                    fecha_actual = (anio_file, mes_file)
                    fecha_guardada = (archivos_recientes[prefijo][0], archivos_recientes[prefijo][1])
                    
                    if fecha_actual > fecha_guardada:
                        archivos_recientes[prefijo] = (anio_file, mes_file, file)
                break

    todas_las_barras = set()
    
    for prefijo, datos in archivos_recientes.items():
        nombre_archivo = datos[2]
        
        if nombre_archivo:
            ruta_completa = os.path.join(resultados_folder, nombre_archivo)
            logging.info(f"Extrayendo 'Barra' de: {nombre_archivo}")
            
            try:
                df = pd.read_parquet(ruta_completa, columns=['Barra'])
                
                barras_unicas_archivo = df['Barra'].dropna().unique()
                todas_las_barras.update(barras_unicas_archivo)
                
            except Exception as e:
                logging.info(f"Error al leer {nombre_archivo}: {e}")
        else:
            logging.info(f"Aviso: No se encontraron archivos para el tipo {prefijo}")
            
    logging.info("-" * 60)
    logging.info(f"Total de barras únicas obtenidas: {len(todas_las_barras)}")
    lista_ordenada = sorted(list(todas_las_barras))
    df_resultado = pd.DataFrame(lista_ordenada, columns=['Barra'])
    return df_resultado

def obtener_barras_recientes_iny(resultados_iny_folder):
    prefijos = [
        'resultado_compraventa', 
        'resultado_nortedist', 
        'resultado_nortetrans',
        'resultado_surdist',
        'resultado_surtrans'
    ]
    
    archivos_recientes = {prefijo: (0, 0, "") for prefijo in prefijos}

    lista_archivos = [f for f in os.listdir(resultados_iny_folder) if f.endswith('.parquet')]
    
    for file in lista_archivos:
        for prefijo in prefijos:
            if file.startswith(prefijo):
                match = re.search(r'(\d{4})(\d{2})', file)
                if match:
                    anio_file = int(match.group(1))
                    mes_file = int(match.group(2))
                    
                    fecha_actual = (anio_file, mes_file)
                    fecha_guardada = (archivos_recientes[prefijo][0], archivos_recientes[prefijo][1])
                    
                    if fecha_actual > fecha_guardada:
                        archivos_recientes[prefijo] = (anio_file, mes_file, file)
                break

    todas_las_barras = set()
    
    for prefijo, datos in archivos_recientes.items():
        nombre_archivo = datos[2]
        
        if nombre_archivo:
            ruta_completa = os.path.join(resultados_iny_folder, nombre_archivo)
            logging.info(f"Extrayendo 'nombre_barra' de: {nombre_archivo}")
            
            try:
                df = pd.read_parquet(ruta_completa, columns=['nombre_barra'])
                
                barras_unicas_archivo = df['nombre_barra'].dropna().unique()
                todas_las_barras.update(barras_unicas_archivo)
                
            except Exception as e:
                logging.info(f"Error al leer {nombre_archivo}: {e}")
        else:
            logging.info(f"Aviso: No se encontraron archivos para el tipo {prefijo}")
            
    logging.info("-" * 60)
    logging.info(f"Total de barras únicas obtenidas: {len(todas_las_barras)}")
    lista_ordenada = sorted(list(todas_las_barras))
    df_resultado = pd.DataFrame(lista_ordenada, columns=['nombre_barra'])
    return df_resultado

df = descargar_maestro_desde_api()
df['nombre_barra'] = df['nombre_barra'].str.upper()
df['Barra_SE'] = df['nombre_barra']
df = df[~df['nombre_barra'].str.contains('MOVIL', na=False, case=False)]
df['nombre_barra'] = df['nombre_barra'].apply(limpiar_nombre_oficial)
df = df.drop(columns='id')
df = df.drop_duplicates()

df_barra_retiros = obtener_barras_recientes(resultados_folder)

df_barra_retiros['Barra_cruce'] = df_barra_retiros['Barra'].apply(limpiar_nombre_sucio)
df_barra_retiros = df_barra_retiros.drop_duplicates()

mapeo_manual = {

    # 1. AGRUPACIONES DE LA MISMA SUBESTACIÓN (Nuevas, Ampliaciones y Anexos)
    'CARDONES': 'NUEVACARDONES',
    'MAITENCILLO': 'NUEVAMAITENCILLO',
    'LAMPA': 'NUEVALAMPA',
    'PAZUCAR': 'NUEVAPANDEAZUCAR',
    'ANCUD': 'NUEVAANCUD',
    'CHUQUICAMATA': 'NUEVACHUQUICAMATA',
    'NVICTORIA': 'NUEVAVICTORIA',
    'RENCA': 'NUEVARENCA',
    'NPANQUEHUE': 'NUEVAPANQUEHUE',
    'VENTANAS': 'CODELCOVENTANAS', 
    'ZALDIVAR': 'NUEVAZALDIVAR',
    'ESCONDIDA': 'ESCONDIDANORTE',

    # 2. ABREVIATURAS DE CIUDADES Y LUGARES
    'PMONTT': 'PUERTOMONTT',
    'PVARAS': 'PUERTOVARAS',
    'PCOLORADA': 'PUNTACOLORADA',
    'PCORTES': 'PUNTADECORTES',
    'PPEUCO': 'PUNTAPEUCO',
    'PLASCASAS': 'PADRELASCASAS',
    'PALMONTE': 'POZOALMONTE',
    'TAMARILLA': 'TIERRAAMARILLA',
    'SFMOSTAZAL': 'SANFRANCISCODEMOSTAZAL',
    'SVICENTETT': 'SANVICENTEDETAGUATAGUA',
    'DALMAGRO': 'DIEGODEALMAGRO',
    'PALTO': 'PUENTEALTO',
    'MPATRIA': 'MONTEPATRIA',
    'VALEGRE': 'VILLAALEGRE',
    'BJOSDMNA': 'BAJOSDEMENA',
    
    # 3. NOMBRES COMPUESTOS Y PERSONAS
    'AJAHUEL': 'ALTOJAHUEL',
    'ADECORDOVA': 'ALONSODECORDOVA',
    'CPINTO': 'CARRERAPINTO',
    'HFUENTES': 'HERNANFUENTES',
    'MDEVELASCO': 'MANSODEVELASCO',
    'RTOMIC': 'RADOMIROTOMIC',
    'LORDCOCHRANE': 'COCHRANE',
    'DALCAHUE': 'SANPEDRODALCAHUE',

    # 4. INDUSTRIALES, MINERAS Y PLANTAS
    'CBIOBIO': 'CEMENTOSBIOBIOCENTRO',
    'CELPACIFICO': 'CELULOSAPACIFICO',
    'CONSTIT': 'PLANTACONSTITUCION',
    'PARAUCO': 'PLANTAARAUCO',
    'VALDIVIA': 'PLANTAVALDIVIA',
    'QUINTERO': 'GNLQUINTERO',
    'MBLANCOS': 'MANTOSBLANCOS',
    'MAESTRANZA': 'BATAPMAESTRANZA',
    'TOFFMAURO': 'BATAPOFFMAURO',
    'TOFFDOLORES': 'DOLORES',
    'PACIFICO': 'TERMOPACIFICO',
    'CHAGRES': 'FUNDICIONCHAGRES',
    'TMELON': 'CEMENTOMELON',
    'TAPPOLPAICO': 'PRINCIPALPLANTAPOLPAICO',
    'GRANEROS': 'GRANEROSINDURA',
    'LINDURA': 'LIRQUENINDURA',
    'VICTORIA': 'VICTORIAFFCC',
    'LAUTARO': 'LAUTAROFFCC',
    'CDARICA': 'DIESELARICA',
    'CDTAMAYA': 'DIESELTAMAYA',
    
    # 5. PARQUES RENOVABLES (Eólicos / Solares)
    'PETALTAL': 'PARQUEEOLICOTALTAL',
    'SANJUAN': 'PARQUEEOLICOSANJUAN',
    
    # 6. REDUCCIONES DE NOMBRES VARIOS
    'LINNORTE': 'LINARESNORTE',
    'CDRAGON': 'CERRODRAGON',
    'SGORDA': 'SIERRAGORDA',
    'CANTERAS': 'LASCANTERAS',
    'COMPANIA': 'LASCOMPANIAS',
    'CALERAC': 'CALERACENTRO',
    'LCOLORADAS': 'LOMALOSCOLORADOS',
    'MAULE': 'MAULEJT5N',
    'EMPALME': 'TENOEMPALME',
    'MALLOA': 'MALLOANUEVA',
    'QTILCOCO': 'QUINTADETILCOCO',
    'MARCHIHUE': 'MARCHIGE',
    'PLACERES': 'LOSPLACERES',
    'PANCHA': 'PLAYAANCHA',
    'ELMELON': 'TUNELELMELON',
    'ANDES': 'LOSANDES',
    'NEGRA': 'LANEGRA',
    'TACCNORTE': 'ACCESONORTE'
}

umbral = 85
diccionario = {}

barras_se = df['nombre_barra'].dropna().unique()
barras_retiros_unicas = df_barra_retiros['Barra_cruce'].dropna().unique() 

for barra_sucia, barra_oficial in mapeo_manual.items():
    if barra_sucia in barras_retiros_unicas and barra_oficial in barras_se:
        diccionario[barra_oficial] = barra_sucia

for barra_oficial in barras_se:
    if barra_oficial in diccionario:
        continue
        
    mejor_match, puntaje = process.extractOne(
        barra_oficial, 
        barras_retiros_unicas,
        scorer=fuzz.ratio 
    )
    
    if puntaje >= umbral:
        diccionario[barra_oficial] = mejor_match
    else:
        pass

df['Llave_Final'] = df['nombre_barra'].map(diccionario)

df_final = pd.merge(
    df, 
    df_barra_retiros,
    left_on='Llave_Final',
    right_on='Barra_cruce',
    how='left'
)
df_final = df_final.drop_duplicates()


mapeo_manual = {

    # 1. PARQUES RENOVABLES (Solares, Eólicos)
    'PERENAICO': 'PARQUEEOLICORENAICO',
    'PELBAIRES': 'PARQUEEOLICOLOSBUENOSAIRES',
    'ESPERANZA': 'PARQUEEOLICOLAESPERANZA',
    'SANTSOLAR': 'SANTIAGOSOLAR',
    'PVSOLDESIERTO': 'SOLDELDESIERTO',
    'CDOMINADOR': 'CERRODOMINADOR',
    'LACRUZ': 'LACRUZSOLAR',
    'SANPEDROEOL': 'SANPEDRODALCAHUEEBP1',
    'CTRMACHICURA': 'PFVMACHICURA',
    
    # 2. ESTACIONES DE BOMBEO / INDUSTRIALES / MINERAS
    'BOMBEO2': 'ESTACIONDEBOMBEON2',
    'BOMBEO3': 'ESTACIONDEBOMBEON3',
    'BOMBEO4': 'ESTACIONDEBOMBEON4',
    'ELVCAPRI': 'ELEVADORACAPRICORNIO',
    'COLLAHUASI': 'COLLAHUASIUNITARIAN1',
    'CTIGRE': 'BACERROTIGRE',
    'CBIOBIO': 'TCBB',
    'DAMIGOS': 'MINERADOSAMIGOS',
    'CANDELARIA': 'MINERALACANDELARIA',
    'VENTANAS': 'CODELCOVENTANAS1',

    # 3. CONEXIONES EN T Y SECCIONADORAS (TAP / SECC)
    'TAPRCOLORADO': 'RIOCOLORADO',
    'TAPPUTAGAN': 'PUTAGAN',
    'TAPELMAITEN': 'PARQUEEOLICOELMAITEN',
    'TAPPALACIOS': 'HIDROELECTRICAPALACIOS',
    'TAPPULELFU': 'PULELFU',
    'TAPTALINAY': 'TALINAY',
    'CSANANDRES': 'SECCIONADORASANANDRES',
    'LLANOLLAMPOS': 'SECCIONADORALLANODELLAMPOS',
    'LOAGUIRRE': 'SECCIONADORALOAGUIRRE',
    'RIOMALLECO': 'SECCIONADORARIOMALLECO',
    'CONVENTOVIEJO': 'SECCIONADORACONVENTOVIEJO',
    
    # 4. REDUCCIONES Y SIGLAS DE CIUDADES / SUBESTACIONES
    'CNAVIA': 'CERRONAVIA',
    'PAZUCAR': 'PANDEAZUCAR',
    'AJAHUEL': 'ALTOJAHUELAUX',
    'MOLLES': 'LOSMOLLES',
    'MELIPILLA': 'BAJOMELIPILLA',
    'CONSTIT': 'CONSTITUCION',
    'JUNCAL': 'JUNCALPORTILLO',
    'PINATAS': 'LASPIATAS',
    'LCOLORADAS': 'LOSCOLORADOS',
    'METRO': 'METROBARRA',
    'QTILCOCO': 'BATAPTILCOCO',
    'PPEUCO': 'PUNTAPEUCOFBP',
    'YBUENAS': 'YERBASBUENAS',
    'CARENA': 'CARENBAJO',
    'PICHIL': 'PICHILBPR1',
    'CARENAICO': 'ALTORENAICO',
    'LALACKAMA': 'BATAPOFFLALACKAMA',
    'CARDONES': 'CARDONESSOLARI',
    'LAHUAYCA2': 'SOLARLAHUAYCA2',
    'LOA': 'ELLOA',
    'ANTUCOYA': 'ENLACEANTUCOYA',
    'MELENA': 'MARIAELENA',
    'DOMEYKO': 'SVCDOMEYKO',
    'ESCUADRON': 'RECTIFICADORAESCUADRON',
    'ELPEUMO': 'LOSPEUMOS',
    'ALTOMAIPO': 'ALTOMAIPOBP1A',
    'PICHIRROPULLI': 'NUEVAPICHIRROPULLI',
    'LORDCOCHRANE': 'GISCOCHRANEBESS',
    'LLAJA': 'LASLAJAS',
    'DEGAN': 'DEGA2',
    'PHURTADO': 'PADREHURTADO',
    'AGBLANCAS': 'DIESELAGUASBLANCAS',
    'CURANILAHUE': 'CURANILAHUENORTE',
    'SGORDA': 'SGO',
    'SAUZAL1': 'SAUZAL60HZ',
    'CHAGUAL': 'CHAGUALB11',
    'CACHAPOAL': 'ALTOCACHAPOAL',
    'ALMEYDA': 'ALMEYDABP1',
    'PALMONTE': 'NUEVAPOZOALMONTE',
    'DALMAGRO': 'SOLARDIEGODEALMAGRO',
    'TOLPAN': 'TOLPANSUR',
    'SANTONIO': 'DONANTONIO',
    'CENTINELA': 'CENTINELABP2EXT1',
    'CONDORES': 'LOSCONDORES',
    'SFRUTILLARN': 'FRUTILLARNORTE',
    'ACONCAGUA1': 'RIOACONCAGUA',
    'LANGELES': 'LOSANGELESSUR',
    'VALLEESC': 'VALLEESCONDIDO',
    'NVICTORIA': 'SANVICTOR'
}

df_barras_iny = obtener_barras_recientes_iny(resultados_iny_folder)
df_barras_iny = df_barras_iny.rename(columns={'nombre_barra':'nombre_barra_iny'})
df_barras_iny['Barra_cruce'] = df_barras_iny['nombre_barra_iny'].apply(limpiar_nombre_oficial)
df_barras_iny = df_barras_iny.drop_duplicates()

umbral = 85

diccionario_iny={}
barras_se = df_final['nombre_barra'].dropna().unique()
barras_iny_unicas = df_barras_iny['Barra_cruce'].dropna().unique()

for barra_sucia, barra_oficial in mapeo_manual.items():
    if barra_sucia in barras_iny_unicas and barra_oficial in barras_se:
        diccionario_iny[barra_oficial] = barra_sucia

for barra_oficial in barras_se:
    if barra_oficial in diccionario_iny:
        continue
        
    mejor_match, puntaje = process.extractOne(
        barra_oficial, 
        barras_iny_unicas,
        scorer=fuzz.ratio 
    )
    
    if puntaje >= umbral:
        diccionario_iny[barra_oficial] = mejor_match
    else:
        logging.info(f"Omitido en Inyecciones: '{barra_oficial}' vs '{mejor_match}' ({puntaje}%)")

df_final['Llave_Final_Iny'] = df_final['nombre_barra'].map(diccionario_iny)

df_final_iny = pd.merge(
    df_final, 
    df_barras_iny,
    left_on='Llave_Final_Iny',
    right_on='Barra_cruce',
    how='left'
)

df_final_iny = df_final_iny.drop(columns=['Llave_Final', 'Barra_cruce_x', 'Barra_cruce_y', 'nombre_barra', 'Llave_Final_Iny'])
df_final_iny = df_final_iny.drop_duplicates()
df_final_iny.to_parquet(os.path.join(mapa_folder,"Barra_Y_SUBESTACION.parquet"), compression='snappy')

funciones.subir_barras_a_sql(mapa_folder)