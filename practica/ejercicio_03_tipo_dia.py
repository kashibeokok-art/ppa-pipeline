"""Ejercicio 03: Literal, reglas de negocio y valores límite.

Objetivo: clasificar un día de la semana como hábil o no hábil.
(Versión simple de RN-16, todavía sin feriados.)

Convención de Python (datetime.weekday()):
    0 = lunes, 1 = martes, 2 = miércoles, 3 = jueves, 4 = viernes, 5 = sábado, 6 = domingo

Regla:
    lunes a viernes (0 a 4) -> "HABIL"
    sábado y domingo (5, 6) -> "NO_HABIL"
    fuera de 0 a 6          -> ValueError

Pistas:
    - Primero la cláusula de guarda (como en el ejercicio 02).
    - Luego un if que devuelva "HABIL" o "NO_HABIL".
    - Fíjate en el tipo de retorno: TipoDia solo permite esos dos textos.
"""

from typing import Literal

TipoDia = Literal["HABIL", "NO_HABIL"]


def tipo_dia(dia_semana: int) -> TipoDia:
    """Clasifica el día de la semana (0=lunes ... 6=domingo) como hábil o no hábil."""
    raise NotImplementedError("TODO: implementa la clasificación")
