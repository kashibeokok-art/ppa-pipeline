"""Tests del ejercicio 05. Ejecuta: uv run pytest practica/test_ejercicio_05_archivos.py -v"""

from pathlib import Path

import pytest
from ejercicio_05_archivos import leer_horas


@pytest.fixture
def archivo_horas(tmp_path: Path) -> Path:
    """Patrón 6: fixture propia. Prepara un archivo y lo ENTREGA al test que la pida.

    tmp_path es una fixture de pytest: una carpeta temporal vacía, distinta para cada test.
    """
    ruta = tmp_path / "horas.txt"
    ruta.write_text("0\n7\n23\n", encoding="utf-8")
    return ruta


def test_lee_horas(archivo_horas: Path) -> None:
    """El test PIDE la fixture escribiendo su nombre como parámetro; pytest se la entrega."""
    assert leer_horas(archivo_horas) == [0, 7, 23]


def test_archivo_vacio(tmp_path: Path) -> None:
    """Patrón 5: archivos temporales. Se crea el archivo dentro del test."""
    ruta = tmp_path / "vacio.txt"
    ruta.write_text("", encoding="utf-8")

    assert leer_horas(ruta) == []


def test_archivo_con_lineas_vacias(tmp_path: Path) -> Path:
    """Crea un archivo con líneas vacías y devuelve su ruta."""
    ruta = tmp_path / "lineas_vacias.txt"
    ruta.write_text("8\n\n17\n\n", encoding="utf-8")

    assert leer_horas(ruta) == [8, 17]


# TODO 1: escribe una fixture llamada archivo_con_lineas_vacias que cree un archivo con
#   el contenido "8\n\n17\n\n" (con líneas vacías entre medio) y devuelva su ruta.

# TODO 2: escribe test_ignora_lineas_vacias que PIDA esa fixture y verifique que el
#   resultado es [8, 17].
