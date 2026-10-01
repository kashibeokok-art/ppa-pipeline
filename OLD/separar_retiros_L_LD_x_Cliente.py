import pandas as pd
import os
import rutas_config

download_folder = rutas_config.DIRECTORIO_DESCARGA
procesados_iny_folder = rutas_config.DIRECTORIO_PROCESADOS_INY 
resultados_iny_folder = rutas_config.DIRECTORIO_RESULTADOS_INY
resultados_iny_concat_folder = rutas_config.DIRECTORIO_RESULTADOS_INY_CONCAT
procesados_folder = rutas_config.DIRECTORIO_PROCESADOS
procesados_ret_para_iny = rutas_config.DIRECTORIO_RETIROS_PROCESADOS_INY

Cambiar_descripcion = os.listdir(resultados_iny_concat_folder)

for file in Cambiar_descripcion:
    if not file.endswith(".parquet"):
        continue
    print(file)

    path = os.path.join(resultados_iny_concat_folder, file)

    df = pd.read_parquet(path)

    print(df['tipo'].unique())
    df
    condicion = df['tipo'].isin(['C_FIN', 'C_FIS'])
    print(condicion)
    df_filtrado = df[condicion]
    conteos = df_filtrado['descripcion'].value_counts()
    descripciones_con_par = conteos[conteos == 6].index

    filtro_final = condicion & df['descripcion'].isin(descripciones_con_par)

    df.loc[filtro_final, 'descripcion'] = (
    df[filtro_final].groupby('descripcion')['Suministrador']
    .transform(lambda x: x.iloc[::-1].values)
    )

    df.to_parquet(path, index=False)

