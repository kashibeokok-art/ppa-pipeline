"""Reglas de bloques horarios (RN-01) para licitación pública."""

from typing import Literal

Bloque = Literal["A", "B", "C"]


def asignar_bloque(hora: int) -> Bloque:
    """Asigna el bloque horario de licitación pública a una hora de inicio (0-23).

    RN-01:
    A: 00:00 - 07:59 y 23:00 - 23:59
    B: 08:00 - 17:59
    C: 18:00 - 22:59

    Raises:
        ValueError: si la hora no está en el rango 0-23.
    """
    if not (0 <= hora <= 23):
        raise ValueError(f"La hora {hora} no está en el rango 0-23.")

    if 0 <= hora < 8 or hora == 23:
        return "A"
    elif 8 <= hora < 18:
        return "B"
    else:  # 18 <= hora < 23
        return "C"
