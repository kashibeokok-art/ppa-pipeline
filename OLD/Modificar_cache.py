##################################
#Guardar el caché .json a csv
#################################

'''
En caso de querer modificar cache_ruts_empresas.json, se debe correr este script para actualizar el archivo .csv
'''

#.csv = CompiladoEmpresasConRUT
import json
import csv
import os
import rutas_config
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cache_dir = rutas_config.DIRECTORIO_CACHE
resultados_dir = rutas_config.DIRECTORIO_RESULTADOS

with open(os.path.join(cache_dir, "cache_ruts_empresas.json"), 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Crear el archivo CSV
with open(os.path.join(resultados_dir, "CompiladoEmpresasConRUT.csv"), 'w', encoding='utf-8', newline='') as csv_file:
    writer = csv.writer(csv_file)
    
    # Escribir encabezados
    writer.writerow(["Subdivision", "Empresa", "RUT"])

    # Iterar sobre las empresas en el JSON y escribir en el CSV
    for key, value in data.items():
        empresa = value.get("Empresa", "")
        nombre_mas_probable = value.get("nombre_mas_probable", "")
        rut_mas_probable = value.get("rut_mas_probable", "")
        # Escribir la fila, incluso si contiene elementos vacíos
        writer.writerow([empresa, nombre_mas_probable, rut_mas_probable])

print("Archivo CSV generado exitosamente como 'CompiladoEmpresasConRUT.csv'")
