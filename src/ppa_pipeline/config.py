"""Configuración del pipeline, leída desde variables de entorno y .env (Twelve-Factor)."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

NivelLog = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """Configuración del pipeline. Cada atributo se lee de la variable PPA_<NOMBRE>.

    Prioridad: variable de entorno > archivo .env > valor por defecto.
    """

    model_config = SettingsConfigDict(
        env_prefix="PPA_",  # log_level se lee de PPA_LOG_LEVEL
        env_file=".env",  # además lee el archivo .env si existe
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # PPA_CEN_API_KEY= (vacío) cuenta como "no configurado"
    )

    data_dir: Path = Path("data")
    """Carpeta raíz de los datos (bronze/, silver/, quarantine/)."""

    log_level: NivelLog = "INFO"
    """Nivel de detalle de los logs."""

    cen_api_key: SecretStr | None = None
    """Clave de la API del Coordinador (portal.api.coordinador.cl). None si aún no se tiene."""
