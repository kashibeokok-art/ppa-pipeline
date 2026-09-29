"""Tests del ejercicio 01. Ejecuta: uv run pytest practica/test_ejercicio_01_unidades.py -v"""

import pytest
from ejercicio_01_unidades import kwh_a_mwh


def test_mil_kwh_son_un_mwh() -> None:
    """Patrón 1: valor esperado. Preparar → Actuar → Verificar."""
    # Preparar
    energia_kwh = 1000
    # Actuar
    resultado = kwh_a_mwh(energia_kwh)
    # Verificar
    assert resultado == 1.0


def test_decimales_con_approx() -> None:
    """Con decimales se usa pytest.approx, porque los float tienen pequeños errores de redondeo."""
    energia = 1234.5
    resultado = kwh_a_mwh(energia)
    assert resultado == pytest.approx(1.2345)


def test_negativo_se_convierte_en_valor_absoluto() -> None:
    """kwh_a_mwh(-2500) debe ser 2.5 (RN-10)."""
    energia = -2500
    resultado = kwh_a_mwh(energia)
    assert resultado == 2.5


def test_cero_es_cero() -> None:
    """kwh_a_mwh(0) debe ser 0.0."""
    energia = 0
    resultado = kwh_a_mwh(energia)
    assert resultado == 0.0
