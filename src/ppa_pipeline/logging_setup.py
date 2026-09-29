"""Logging estructurado (JSON) con run_id (Correlation ID).

Cada línea de log es un JSON con el run_id de la ejecución, así se puede filtrar y rastrear
una ejecución completa de punta a punta. Explicación: docs/aprendizaje/07_logging_estructurado.md
"""

import json  # noqa: F401
import logging
import uuid  # noqa: F401
from datetime import UTC, datetime  # noqa: F401


def nuevo_run_id() -> str:
    """Genera un identificador único y corto (12 caracteres) para una ejecución del pipeline."""
    # TODO paso 1: usa uuid.uuid4().hex (32 caracteres) y quédate con los primeros 12.
    #   Pista: para "los primeros 12 caracteres" de un texto se usa  texto[:12]
    return uuid.uuid4().hex[:12]


class FormateadorJson(logging.Formatter):
    """Convierte cada registro de log en una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Sobrescribe el método format() de logging.Formatter para devolver JSON."""
        datos = {
            "momento": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "run_id": getattr(record, "run_id", None),
        }
        if record.exc_info:
            datos["error"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False)


class FiltroRunId(logging.Filter):
    """Agrega el run_id de la ejecución a cada registro de log."""

    def __init__(self, run_id: str) -> None:
        """Se ejecuta al crear el filtro: FiltroRunId("abc123")."""
        super().__init__()  # primero se inicializa la clase padre (logging.Filter)
        # TODO paso 3a: guarda run_id como atributo del objeto:  self.run_id = run_id
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Se ejecuta con cada registro. Devuelve True para dejarlo pasar."""
        # TODO paso 3b: copia el run_id guardado al registro:  record.run_id = self.run_id
        #   y devuelve True (el filtro no descarta nada: solo agrega información).
        record.run_id = self.run_id
        return True


def configurar_logging(nivel: str, run_id: str) -> None:
    """Configura el logging de toda la aplicación: JSON, con run_id y con el nivel indicado."""
    manejador = logging.StreamHandler()
    manejador.setFormatter(FormateadorJson())
    manejador.addFilter(FiltroRunId(run_id))
    raiz = logging.getLogger()
    raiz.handlers.clear()
    raiz.addHandler(manejador)
    raiz.setLevel(nivel)
