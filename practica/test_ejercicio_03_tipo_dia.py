"""Tests del ejercicio 03. Ejecuta: uv run pytest practica/test_ejercicio_03_tipo_dia.py -v"""

import pytest
from ejercicio_03_tipo_dia import TipoDia, tipo_dia


@pytest.mark.parametrize(
    ("dia_semana", "esperado"),
    [
        (0, "HABIL"),  # lunes
        (6, "NO_HABIL"),  # domingo
        # TODO 1: agrega los dos casos LÍMITE entre hábil y no hábil.
        #   Pregúntate: ¿cuál es el último día hábil y cuál el primer día no hábil?
        #   Copia los valores esperados de la REGLA escrita en el ejercicio, no de memoria.
    ],
)
def test_tipo_dia(dia_semana: int, esperado: TipoDia) -> None:
    """Patrón 2 con dos parámetros: (entrada, resultado esperado)."""
    assert tipo_dia(dia_semana) == esperado


# TODO 2: escribe test_dia_invalido_falla con parametrize de -1 y 7 y pytest.raises(ValueError).
