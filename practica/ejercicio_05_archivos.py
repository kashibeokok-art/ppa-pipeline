"""Ejercicio 05: fixtures y archivos temporales (tmp_path).

Objetivo: leer un archivo de texto con una hora por línea y devolver una lista de enteros.

Ejemplo de archivo:
    0
    7
    23

leer_horas(ruta) -> [0, 7, 23]

Reglas:
    - Ignora las líneas vacías.
    - Un archivo vacío devuelve [].

Pistas:
    - ruta.read_text(encoding="utf-8") devuelve todo el contenido como un solo texto.
    - texto.splitlines() lo separa en una lista de líneas.
    - int("7") convierte el texto "7" en el número 7.
    - linea.strip() quita espacios; una línea vacía queda como "" (que es falso en un if).
"""

from pathlib import Path


def leer_horas(ruta: Path) -> list[int]:
    """Lee un archivo con una hora por línea y devuelve la lista de horas como enteros."""
    raise NotImplementedError("TODO: implementa la lectura")
