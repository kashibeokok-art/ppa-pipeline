"""Tests del logging estructurado (src/ppa_pipeline/logging_setup.py).

Estos tests son la ESPECIFICACIÓN: describen qué debe hacer tu código. Léelos antes de programar.
"""

import json
import logging
import sys

import pytest

from ppa_pipeline.logging_setup import (
    FiltroRunId,
    FormateadorJson,
    configurar_logging,
    nuevo_run_id,
)


def _registro(mensaje: str = "hola") -> logging.LogRecord:
    """Crea un registro de log a mano, como el que genera logger.info("...")."""
    return logging.LogRecord("ppa.test", logging.INFO, __file__, 1, mensaje, None, None)


# ---------- Paso 1: nuevo_run_id ----------


def test_run_id_tiene_12_caracteres() -> None:
    """Un run_id corto (12 caracteres) es fácil de copiar y buscar en los logs."""
    assert len(nuevo_run_id()) == 12


def test_run_id_es_distinto_en_cada_ejecucion() -> None:
    """Cada ejecución del pipeline debe tener su propio identificador."""
    assert nuevo_run_id() != nuevo_run_id()


# ---------- Paso 2: FormateadorJson ----------


def test_formateador_produce_json_con_los_campos() -> None:
    """Cada línea de log es un JSON válido con momento, nivel, logger, mensaje y run_id."""
    registro = _registro("cargando retiros")
    registro.__dict__["run_id"] = "abc123"

    datos = json.loads(FormateadorJson().format(registro))

    assert datos["mensaje"] == "cargando retiros"
    assert datos["nivel"] == "INFO"
    assert datos["logger"] == "ppa.test"
    assert datos["run_id"] == "abc123"
    assert "momento" in datos


# ---------- Paso 3: FiltroRunId ----------


def test_filtro_agrega_run_id_al_registro() -> None:
    """El filtro le pega el run_id a cada registro que pasa por él."""
    registro = _registro()

    deja_pasar = FiltroRunId("abc123").filter(registro)

    assert deja_pasar is True
    assert registro.__dict__["run_id"] == "abc123"


# ---------- Paso 4: configurar_logging ----------


def test_configurar_logging_emite_json_con_run_id(capsys: pytest.CaptureFixture[str]) -> None:
    """Después de configurar, cualquier logger escribe JSON con el run_id de la ejecución."""
    configurar_logging("INFO", "run-xyz")

    logging.getLogger("ppa.test").info("inicio")

    ultima_linea = capsys.readouterr().err.strip().splitlines()[-1]
    datos = json.loads(ultima_linea)
    assert datos["run_id"] == "run-xyz"
    assert datos["mensaje"] == "inicio"


def test_nivel_filtra_mensajes_menos_importantes(capsys: pytest.CaptureFixture[str]) -> None:
    """Con nivel WARNING, los mensajes INFO no se escriben."""
    configurar_logging("WARNING", "run-xyz")

    logging.getLogger("ppa.test").info("no debe aparecer")

    assert capsys.readouterr().err == ""


def test_formateador_incluye_el_detalle_del_error() -> None:
    """Si el log viene de un error (logger.exception), el JSON incluye el detalle completo."""
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        registro = logging.LogRecord(
            "ppa.test", logging.ERROR, __file__, 1, "falló", None, sys.exc_info()
        )
    datos = json.loads(FormateadorJson().format(registro))

    assert "ZeroDivisionError" in datos["error"]
