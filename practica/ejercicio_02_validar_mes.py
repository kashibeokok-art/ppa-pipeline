"""Ejercicio 02: cláusula de guarda y errores.

Objetivo: validar que un mes esté entre 1 y 12. Si es válido, devolverlo; si no, fallar fuerte.

Ejemplos:
    validar_mes(1)  -> 1
    validar_mes(12) -> 12
    validar_mes(0)  -> ValueError
    validar_mes(13) -> ValueError

Pistas:
    - Es igual a la validación de hora en src/ppa_pipeline/domain/bloques.py (líneas 19-20).
    - raise ValueError(f"Mes fuera de rango: {mes}")
"""


def validar_mes(mes: int) -> int:
    """Devuelve el mes si está entre 1 y 12; si no, lanza ValueError."""
    if not (1 <= mes <= 12):
        raise ValueError(f"Mes fuera de rango: {mes}")
    return mes
