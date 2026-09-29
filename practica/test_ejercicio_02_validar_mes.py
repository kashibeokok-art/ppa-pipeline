"""Tests del ejercicio 02. Ejecuta: uv run pytest practica/test_ejercicio_02_validar_mes.py -v"""

import pytest
from ejercicio_02_validar_mes import validar_mes


@pytest.mark.parametrize("mes", [1, 6, 12])
def test_meses_validos_se_devuelven_igual(mes: int) -> None:
    """Patrón 2: varios casos con parametrize. El test corre una vez por cada valor."""
    assert validar_mes(mes) == mes


@pytest.mark.parametrize("mes_invalido", [0, 13, -1])
def test_meses_invalidos_fallan(mes_invalido: int) -> None:
    """Patrón 3: error esperado, el mes está fuera de rango.
    Se usa parametrize para varios casos."""
    with pytest.raises(ValueError):
        validar_mes(mes_invalido)


# TODO 1: escribe test_meses_invalidos_fallan
#   Usa @pytest.mark.parametrize con los valores LÍMITE justo fuera del rango: 0 y 13.
#   Agrega también -1.
#   Dentro, usa:  with pytest.raises(ValueError):
#                     validar_mes(mes_invalido)
#   (Patrón 3: error esperado. Es el mismo patrón de test_asignar_bloque_hora_invalida.)
