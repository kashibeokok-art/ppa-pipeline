"""Tests del ejercicio 04. Ejecuta: uv run pytest practica/test_ejercicio_04_config.py -v"""

import pytest
from ejercicio_04_config import ConfigPractica
from pydantic import ValidationError  # noqa: F401  (lo usarás en el TODO 2)


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> None:
    """Se ejecuta antes de CADA test (autouse=True): borra las variables PRAC_ previas."""
    monkeypatch.delenv("PRAC_ZONA_HORARIA", raising=False)
    monkeypatch.delenv("PRAC_MAX_REINTENTOS", raising=False)


def test_valores_por_defecto() -> None:
    """Sin variables de entorno, se usan los valores por defecto de la clase."""
    config = ConfigPractica()  # crear una INSTANCIA de la clase

    assert config.zona_horaria == "America/Santiago"  # leer un ATRIBUTO con punto
    assert config.max_reintentos == 3


def test_lee_variable_de_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patrón 4: entorno. monkeypatch.setenv crea la variable solo durante este test."""
    monkeypatch.setenv("PRAC_MAX_REINTENTOS", "5")  # llega como TEXTO "5"

    config = ConfigPractica()

    assert config.max_reintentos == 5  # pydantic lo convirtió a int 5


# TODO 1: escribe test_zona_horaria_desde_entorno
#   Pon PRAC_ZONA_HORARIA="UTC" y verifica que config.zona_horaria == "UTC".

# TODO 2: escribe test_reintentos_invalidos_fallan
#   Pon PRAC_MAX_REINTENTOS="tres" y verifica que ConfigPractica() lance ValidationError.
#   ¿Por qué falla? Porque "tres" no se puede convertir a int: fail fast.
