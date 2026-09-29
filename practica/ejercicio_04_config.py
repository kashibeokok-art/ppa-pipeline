"""Ejercicio 04: tu primera clase propia (configuración con pydantic-settings).

Objetivo: crear una clase de configuración que lea variables con prefijo PRAC_.

Atributos que debes agregar (formato  nombre: tipo = valor_por_defecto):

    | Atributo        | Tipo | Valor por defecto   | Variable de entorno   |
    |-----------------|------|---------------------|-----------------------|
    | zona_horaria    | str  | "America/Santiago"  | PRAC_ZONA_HORARIA     |
    | max_reintentos  | int  | 3                   | PRAC_MAX_REINTENTOS   |

Pistas:
    - Mira src/ppa_pipeline/config.py: es la misma estructura.
    - Las variables de entorno siempre son TEXTO. Si pones PRAC_MAX_REINTENTOS=5, pydantic
      lo convierte a int 5 porque declaraste el tipo int. Si pones "tres", falla (ValidationError).
    - Borra la línea `pass` cuando agregues los atributos.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigPractica(BaseSettings):
    """Configuración de práctica. Cada atributo se lee de PRAC_<NOMBRE>."""

    model_config = SettingsConfigDict(env_prefix="PRAC_")

    zona_horaria: str = "America/Santiago"
    """Zona horaria para la práctica."""

    max_reintentos: int = 3
    """Número máximo de reintentos permitidos."""
