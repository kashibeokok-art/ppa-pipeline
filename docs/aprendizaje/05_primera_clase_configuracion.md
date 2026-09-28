# 05 · Tu primera clase: configuración con `pydantic-settings`

> **Hito:** H2.1 · **Archivos:** `src/ppa_pipeline/config.py`, `tests/test_config.py`, `.env.example`, `.env`
> **Conceptos:** Twelve-Factor (config), variables de entorno, `.env`; **POO: clase, instancia, atributo, herencia**; validación de configuración; `SecretStr`; fixtures de pytest (`monkeypatch`, `tmp_path`).

---

## 1. El problema: configuración escrita en el código

En el legado, la configuración estaba **dentro del código**:

- [rutas_config.py](../../OLD/rutas_config.py): rutas absolutas de un usuario (`/mnt/c/Users/adm_tipy/...`), y además crea carpetas **al importarse**.
- [funciones.py:1540](../../OLD/funciones.py): servidor, usuario y **contraseña** escritos en el código.

Para cambiar una ruta o una clave había que **editar el código**. Y el secreto quedó guardado en cada copia del archivo.

### Twelve-Factor App, factor III: *Config*

> *"Guarda la configuración en el entorno."*

La **configuración** (lo que cambia entre tu PC, el CI y producción: rutas, claves, nivel de log) va **fuera del código**, en **variables de entorno**. El código es el mismo en todas partes; solo cambia el entorno.

---

## 2. Variables de entorno y el archivo `.env`

- Una **variable de entorno** es un par `NOMBRE=valor` que el sistema operativo entrega a cada programa al iniciarse. Ya conoces una: `PATH`.
- Un archivo **`.env`** es una forma cómoda de declararlas en desarrollo:
  ```dotenv
  PPA_LOG_LEVEL=DEBUG
  PPA_CEN_API_KEY=mi-clave-real
  ```
- **`.env` NUNCA va a git** (tiene secretos; ya está en tu `.gitignore`).
- **`.env.example` SÍ va a git**: tiene los **mismos nombres sin valores reales**. Documenta qué variables necesita el proyecto.

🧠 **Prefijo `PPA_`:** todas las variables del proyecto empiezan igual, para no chocar con variables de otros programas (por ejemplo, `LOG_LEVEL` a secas podría usarla otra aplicación).

---

## 3. Programación orientada a objetos (POO), desde cero

Hasta ahora escribiste **funciones**: entra un dato, sale un resultado, y la función no recuerda nada. La configuración es distinta: es un **conjunto de datos que viajan juntos** (ruta de datos, nivel de log, clave) y que se **validan**. Para eso sirve una **clase**.

### 3.1 Clase e instancia

| Concepto                     | Qué es                                                          | Analogía               |
| ---------------------------- | ---------------------------------------------------------------- | ----------------------- |
| **Clase** (`class`)  | El**molde**: define qué datos tiene y qué reglas cumplen | El formulario en blanco |
| **Instancia** (objeto) | Un ejemplar**concreto** creado a partir del molde          | Un formulario ya lleno  |
| **Atributo**           | Un dato que guarda el objeto                                     | Un campo del formulario |


```python
class Settings(BaseSettings):      # ← la CLASE (el molde)
    log_level: NivelLog = "INFO"   # ← un ATRIBUTO, con su tipo y valor por defecto

config = Settings()                # ← una INSTANCIA (el formulario lleno)
config.log_level                   # ← leer un atributo con punto: "INFO"
```

- Se escribe `Settings()` **con paréntesis** para **crear** una instancia (se dice *instanciar*).
- Se accede a los atributos con **punto**: `config.log_level`.
- Por convención, las clases van en **CamelCase** (`Settings`) y las instancias en minúscula (`config`).

### 3.2 Herencia

```python
class Settings(BaseSettings):
#             ^^^^^^^^^^^^^^
#             la clase "padre"
```

Lo que va entre paréntesis después del nombre es la **clase padre**. `Settings` **hereda** todo el comportamiento de `BaseSettings` (de la librería `pydantic-settings`) sin que tengas que programarlo:

- leer variables de entorno y el archivo `.env`;
- convertir textos al tipo declarado (`"DEBUG"` → `NivelLog`, `"data"` → `Path`);
- **validar** y lanzar un error si un valor no cumple el tipo.

Tú solo **declaras** los atributos; la herencia pone el trabajo pesado.

🧠 **Herencia (*inheritance*):** una clase hija reutiliza y extiende el comportamiento de una clase padre. Es uno de los pilares de la POO.

### 3.3 ¿Por qué aquí una clase y en RN-01 una función?

| RN-01`asignar_bloque`     | `Settings`                                                 |
| --------------------------- | ------------------------------------------------------------ |
| Un cálculo: hora → bloque | Un**conjunto de datos** que viajan juntos y se validan |
| No guarda nada              | Guarda valores (atributos)                                   |
| **Función**          | **Clase**                                              |

---

## 4. El código explicado

```python
"""Configuración del pipeline, leída desde variables de entorno y .env (Twelve-Factor)."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

NivelLog = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """Configuración del pipeline. Cada atributo se lee de la variable PPA_<NOMBRE>."""

    model_config = SettingsConfigDict(
        env_prefix="PPA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    data_dir: Path = Path("data")
    log_level: NivelLog = "INFO"
    cen_api_key: SecretStr | None = None
```

| Línea                                     | Significado                                                                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `from pathlib import Path`               | `Path` representa rutas de archivos y funciona igual en Windows y Linux (reemplaza a `os.path.join`) |
| `from pydantic import SecretStr`         | Tipo especial para secretos:**se oculta** al imprimirlo (`**********`)                           |
| `NivelLog = Literal[...]`                | Alias de tipo, igual que`Bloque`: solo esos 4 textos son válidos                                      |
| `class Settings(BaseSettings):`          | Declara la clase`Settings`, que **hereda** de `BaseSettings`                                   |
| `model_config = SettingsConfigDict(...)` | Configuración**de la clase** misma: cómo debe leer los valores                                   |
| `env_prefix="PPA_"`                      | El atributo`log_level` se lee de la variable `PPA_LOG_LEVEL`                                         |
| `env_file=".env"`                        | Además, lee el archivo`.env` si existe                                                                |
| `data_dir: Path = Path("data")`          | Atributo: nombre, tipo y**valor por defecto** (si no hay variable, usa `data`)                   |
| `log_level: NivelLog = "INFO"`           | Si`PPA_LOG_LEVEL=VERBOSO`, **falla al crear** `Settings()`: *fail fast*                      |
| `cen_api_key: SecretStr \| None = None`   | La clave de la API.`\| None` = "puede no existir" (aún no te registras en el CEN)                      |

### Orden de prioridad de los valores

1. Variable de entorno real (`PPA_LOG_LEVEL` en el sistema) → **gana**.
2. Archivo `.env`.
3. Valor por defecto en la clase.

### `SecretStr`: el secreto no se filtra en los logs

```python
config = Settings()
print(config)                                # cen_api_key=SecretStr('**********')
config.cen_api_key.get_secret_value()        # el valor real, solo cuando lo pides explícitamente
```

Si algún día haces `logging.info(config)`, la clave **no** queda escrita en el log. Es la lección de H0 aplicada en el código.

### Error real: `Field required` + `Extra inputs are not permitted`

El primer intento tenía este atributo:
```python
secret_key: SecretStr   # sin valor por defecto
```
Y al crear `Settings()` salieron dos errores:
```
secret_key       Field required               [type=missing]
ppa_cen_api_key  Extra inputs are not permitted [type=extra_forbidden]
```

**1. Obligatorio vs. opcional:**

| Cómo se escribe | Qué significa |
|---|---|
| `log_level: NivelLog = "INFO"` | Opcional: si falta la variable, usa `"INFO"` |
| `secret_key: SecretStr` | **Obligatorio**: si falta la variable → `Field required` |
| `cen_api_key: SecretStr \| None = None` | Opcional y puede no existir: si falta → `None` |

**2. El nombre del atributo decide qué variable se lee** (`env_prefix` + nombre en mayúsculas):
```
secret_key   →  PPA_SECRET_KEY    (no existe en .env → Field required)
cen_api_key  →  PPA_CEN_API_KEY   (sí existe en .env)
```

**3. Variables sobrantes en `.env` son un error:** `.env` tenía `PPA_CEN_API_KEY`, pero ningún atributo se llamaba `cen_api_key`, así que pydantic-settings la rechazó. Es una protección: un error de tipeo (`PPA_LOG_LEVL`) no se ignora en silencio.

**Corrección:** `cen_api_key: SecretStr | None = None`. El nombre además describe el propósito real (la clave de la API del CEN), no uno genérico.

🧠 **Lecciones:**
- El *fail fast* funcionó: la configuración falló **al iniciar**, con un mensaje que dice exactamente qué atributo y por qué.
- Los nombres deben describir **el propósito** (`cen_api_key`), no algo genérico (`secret_key`).
- `.env.example` es una **plantilla**: los secretos van **vacíos** (`PPA_CEN_API_KEY=`), sin valores de ejemplo.

💡 **Detalle:** una línea vacía `PPA_CEN_API_KEY=` se lee como texto vacío `""`, no como `None`. Si se quiere que "vacío" signifique "no configurado", se agrega `env_ignore_empty=True` en `SettingsConfigDict(...)`.

---

## 5. Los tests explicados

```python
@pytest.fixture(autouse=True)
def sin_archivo_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PPA_LOG_LEVEL", raising=False)
    monkeypatch.delenv("PPA_CEN_API_KEY", raising=False)
```

| Pieza                                            | Significado                                                                                                       |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **Fixture** (`@pytest.fixture`)          | Función de**preparación** que pytest ejecuta antes de cada test                                           |
| `autouse=True`                                 | Se aplica**automáticamente** a todos los tests del archivo                                                 |
| `tmp_path`                                     | Fixture de pytest: una**carpeta temporal vacía** y distinta para cada test                                 |
| `monkeypatch`                                  | Fixture de pytest para**modificar el entorno solo durante el test**; al terminar, todo vuelve a como estaba |
| `monkeypatch.chdir(tmp_path)`                  | Cambia la carpeta de trabajo a la temporal. Así**tu `.env` real no interfiere** con los tests            |
| `monkeypatch.delenv(...)`                      | Borra la variable si existe;`raising=False` = no falla si no existía                                           |
| `monkeypatch.setenv("PPA_LOG_LEVEL", "DEBUG")` | Crea la variable solo para ese test                                                                               |

🧠 **Aislamiento de tests (*test isolation*):** un test no debe depender de tu PC (tu `.env`, tus variables). Si dependiera, pasaría en tu PC y fallaría en el CI: otra vez "en mi máquina funciona".

⚠️ **Lección real:** la primera versión de estos tests usaba `Settings(_env_file=None)`. Funcionaba en pytest, pero **`mypy --strict` la rechazaba** (`Unexpected keyword argument "_env_file"`). Se reemplazó por `monkeypatch.chdir(tmp_path)`, que aísla el test sin pelear con los tipos.

---

### Errores reales al escribir los tests (y cómo leerlos)

**1. `Failed: DID NOT RAISE ValidationError`**
```python
@pytest.mark.parametrize("log_invalido", ["DEBUG", "INFO", "WARNING", "ERROR"])   # ❌ son VÁLIDOS
```
"DID NOT RAISE" significa: *esperabas un error y el código funcionó bien*. El test estaba bien planteado, pero los **datos** eran los valores permitidos. Para probar el rechazo se usan valores **fuera** de `NivelLog`: `"VERBOSO"`, `"TRACE"`, `""` y `"debug"` (`Literal` distingue mayúsculas).

**2. `assert Settings().log_level == "DEBUG"` fallaba**
El valor por defecto definido en `config.py` es `"INFO"`. Es la misma lección que `(23, "C")`: **el valor esperado se copia de la definición, no de la memoria.**

**3. mypy: `Argument "log_level" to "Settings" has incompatible type "str"`**
`Settings(log_level=log_invalido)` pasa a propósito un texto cualquiera a un campo `Literal`, y mypy lo rechaza con razón. Se prueba por **la entrada real**, la variable de entorno:
```python
@pytest.mark.parametrize("log_invalido", ["VERBOSO", "debug", "TRACE", ""])
def test_rechaza_nivel_invalido(monkeypatch: pytest.MonkeyPatch, log_invalido: str) -> None:
    monkeypatch.setenv("PPA_LOG_LEVEL", log_invalido)
    with pytest.raises(ValidationError):
        Settings()
```
🧠 **Testear por la entrada real:** en producción, `log_level` llega desde el entorno. El test recorre el mismo camino que usará el pipeline.

**4. Ubicación:** los tests reflejan la estructura de `src/`:
```
src/ppa_pipeline/config.py          →  tests/test_config.py
src/ppa_pipeline/domain/bloques.py  →  tests/domain/test_bloques.py
```
La configuración no es una regla de negocio, así que no va en `tests/domain/`.

---

## 6. Dependencia del pipeline vs. de desarrollo

```powershell
uv add pydantic-settings        # SIN --dev
```

|              | `uv add`                                      | `uv add --dev`                                              |
| ------------ | ----------------------------------------------- | ------------------------------------------------------------- |
| Para qué    | Lo necesita el**pipeline para funcionar** | Solo para**programar** (ruff, mypy, pytest, pre-commit) |
| Dónde queda | `[project] dependencies`                      | `[dependency-groups] dev`                                   |
| Ejemplo      | `pydantic-settings`, más adelante `pandas` | `pytest`                                                    |

---

## 7. Para la entrevista

> *"Externalicé la configuración según el factor III de Twelve-Factor: una clase de pydantic-settings lee variables de entorno con prefijo, valida tipos al iniciar para fallar rápido, y guarda las claves como `SecretStr` para que nunca aparezcan en los logs. Los tests se aíslan del entorno local con `monkeypatch` y `tmp_path`."*

---

## 8. Glosario

| Término                       | Definición breve                                                                 |
| ------------------------------ | --------------------------------------------------------------------------------- |
| Twelve-Factor App              | Principios para aplicaciones portables; factor III: configuración en el entorno  |
| Variable de entorno            | Par`NOMBRE=valor` que el sistema entrega a cada programa                        |
| `.env` / `.env.example`    | Variables locales (fuera de git) / plantilla sin valores (en git)                 |
| Clase                          | Molde que define datos y comportamiento                                           |
| Instancia (objeto)             | Ejemplar concreto creado desde una clase:`Settings()`                           |
| Atributo                       | Dato que guarda un objeto:`config.log_level`                                    |
| Herencia                       | Una clase hija reutiliza el comportamiento de la padre:`Settings(BaseSettings)` |
| `Path`                       | Tipo para rutas de archivos, portable entre sistemas operativos                   |
| `SecretStr`                  | Texto que se oculta al imprimirse                                                 |
| Fixture                        | Preparación reutilizable para tests                                              |
| `monkeypatch` / `tmp_path` | Modificar el entorno solo durante un test / carpeta temporal vacía               |
| Test isolation                 | Un test no depende del entorno de la máquina donde corre                         |
| Campo obligatorio / opcional   | Sin valor por defecto = obligatorio; con `= valor` = opcional                     |
| `extra_forbidden`              | Error de pydantic cuando llega una variable que ningún atributo espera           |

---

## 9. Preguntas de comprobación

1. ¿Qué diferencia hay entre la clase `Settings` y `Settings()`?
2. ¿Qué hace `BaseSettings` por ti gracias a la herencia?
3. Si existe `PPA_LOG_LEVEL=ERROR` en el sistema y `PPA_LOG_LEVEL=DEBUG` en `.env`, ¿qué valor toma `log_level`?
4. ¿Por qué los tests cambian la carpeta de trabajo con `monkeypatch.chdir(tmp_path)`?
5. ¿Por qué `pydantic-settings` se instala sin `--dev`?
