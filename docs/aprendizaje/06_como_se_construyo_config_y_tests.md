# 06 · Cómo se construyó `config.py` y cómo se escribe un test, paso a paso

> **Hito:** H2.1 · **Para quién:** si leíste la lección 05 y todavía no ves **cómo se llega** al código final.
> Aquí se construye todo **de a un paso**, ejecutando después de cada cambio para ver qué pasa.
> **Práctica:** carpeta [`practica/`](../../practica/README.md), con 5 ejercicios.

---

# Parte A: construir `config.py` en 7 pasos

La idea: **nadie escribe el archivo final de una vez**. Se agrega una cosa, se ejecuta, se mira el resultado y se agrega la siguiente.

Para "mirar", en cada paso se usa este comando:
```powershell
uv run python -c "from ppa_pipeline.config import Settings; print(Settings())"
```
Traducido: *"importa la clase `Settings` desde `config.py`, crea una instancia con `Settings()` e imprímela"*.

---

### Paso 1: la clase vacía

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pass
```

| Línea | Qué significa |
|---|---|
| `from pydantic_settings import BaseSettings` | Traigo la clase `BaseSettings` de la librería que instalé con `uv add pydantic-settings` |
| `class Settings(BaseSettings):` | Creo **mi** clase `Settings`. Lo que va entre paréntesis es la **clase padre**: `Settings` **hereda** todo lo que sabe hacer `BaseSettings` |
| `pass` | "No hay nada más". Python exige que una clase tenga al menos una línea |

**Resultado del comando:** una línea vacía. La clase existe, pero todavía no tiene datos.

---

### Paso 2: el primer atributo

```python
class Settings(BaseSettings):
    log_level: str = "INFO"
```

Un **atributo** tiene tres partes, igual que un parámetro de función:
```
log_level   :   str   =   "INFO"
 nombre         tipo      valor por defecto
```

**Resultado:** `log_level='INFO'`

---

### Paso 3: la magia de la herencia, leer el entorno

Sin cambiar el código, define una variable en la terminal y vuelve a ejecutar:
```powershell
$env:LOG_LEVEL = "DEBUG"
uv run python -c "from ppa_pipeline.config import Settings; print(Settings())"
```
**Resultado:** `log_level='DEBUG'`

**Tú no programaste la lectura de variables.** Lo hace `BaseSettings`, y `Settings` lo **heredó**. Esa es la utilidad de la herencia: reutilizas comportamiento ya escrito y probado.

(Limpia la variable antes de seguir: `Remove-Item Env:LOG_LEVEL`)

---

### Paso 4: el prefijo `PPA_`

`LOG_LEVEL` a secas podría usarlo cualquier otro programa. Se agrega un prefijo propio:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PPA_")

    log_level: str = "INFO"
```
- `model_config` no es un dato del pipeline: es **la configuración de la clase misma**, o sea, cómo debe comportarse.
- Ahora el atributo `log_level` se lee de la variable **`PPA_LOG_LEVEL`**.

**Regla para recordar:** `nombre de la variable = env_prefix + NOMBRE_DEL_ATRIBUTO en mayúsculas`.

---

### Paso 5: leer también el archivo `.env`

```python
    model_config = SettingsConfigDict(
        env_prefix="PPA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
```
Ahora también lee `PPA_LOG_LEVEL=...` desde el archivo `.env`. **Prioridad:** variable de la terminal > `.env` > valor por defecto.

---

### Paso 6: restringir los valores válidos (fail fast)

Con `str`, cualquier texto sirve, incluso `PPA_LOG_LEVEL=VERBOSO`. Se restringe con `Literal`, como hiciste con `Bloque`:
```python
from typing import Literal

NivelLog = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    ...
    log_level: NivelLog = "INFO"
```
**Prueba:** `$env:PPA_LOG_LEVEL = "VERBOSO"` y ejecuta → **`ValidationError`**. El programa se niega a arrancar con un valor inválido. Eso es *fail fast*.

---

### Paso 7: los otros dos atributos

```python
from pathlib import Path

from pydantic import SecretStr

    data_dir: Path = Path("data")
    cen_api_key: SecretStr | None = None
```

| Atributo | Lo nuevo |
|---|---|
| `data_dir: Path` | `Path` es el tipo para rutas; pydantic convierte el texto `"data"` en una ruta |
| `cen_api_key: SecretStr \| None = None` | `SecretStr` se oculta al imprimir (`**********`). `\| None = None` = "puede no existir; por defecto no hay" |

Y un último ajuste en `model_config`:
```python
        env_ignore_empty=True,
```
Con esto, una línea vacía `PPA_CEN_API_KEY=` (como en `.env.example`) cuenta como **"no configurado"** y el atributo queda en `None`, en vez de un texto vacío.

✅ **Llegaste al archivo final.** Ábrelo en [`src/ppa_pipeline/config.py`](../../src/ppa_pipeline/config.py) y reconoce cada paso.

---

# Parte B: cómo se escribe un test

## B.1 La receta: 4 preguntas

Antes de escribir código, responde estas preguntas:

| # | Pregunta | Ejemplo con `log_level` |
|---|---|---|
| 1 | **¿Qué comportamiento quiero asegurar?** (una frase) | "Si la variable tiene un valor inválido, el programa no arranca" |
| 2 | **¿Qué necesito preparar?** (*Arrange*) | Poner `PPA_LOG_LEVEL=VERBOSO` |
| 3 | **¿Qué acción ejecuto?** (*Act*) | Crear `Settings()` |
| 4 | **¿Qué debería pasar?** (*Assert*) | Que lance `ValidationError` |

La frase de la pregunta 1 se convierte en el **nombre** del test: `test_rechaza_nivel_invalido`.

## B.2 La plantilla

```python
def test_<lo_que_aseguro>() -> None:
    """<la frase de la pregunta 1>."""
    # Preparar (Arrange)
    ...
    # Actuar (Act)
    resultado = ...
    # Verificar (Assert)
    assert resultado == <valor_esperado>
```

⚠️ **Regla de oro:** el `<valor_esperado>` se copia de la **regla escrita** o de la **definición** (`requerimientos.md`, `config.py`), **nunca de la memoria**. Los dos errores reales de este proyecto (`23 → "C"` y `== "DEBUG"`) vinieron de escribirlo de memoria.

## B.3 Los 6 patrones de test que usas en el proyecto

| # | Patrón | Cuándo | Herramienta | Ejemplo en el proyecto | Práctica |
|---|---|---|---|---|---|
| 1 | **Valor esperado** | La función devuelve algo | `assert x == y` | `test_valores_por_defecto` | Ejercicio 01 |
| 2 | **Varios casos** | La misma prueba con muchos datos | `@pytest.mark.parametrize` | `test_asignar_bloque` | Ejercicios 02 y 03 |
| 3 | **Error esperado** | La función debe fallar | `with pytest.raises(Error):` | `test_rechaza_nivel_invalido` | Ejercicio 02 |
| 4 | **Entorno** | El código lee variables de entorno | `monkeypatch.setenv(...)` | `test_lee_variable_de_entorno` | Ejercicio 04 |
| 5 | **Archivos temporales** | El código lee o escribe archivos | `tmp_path` | `test_lee_archivo_env` | Ejercicio 05 |
| 6 | **Fixture propia** | Varios tests necesitan la misma preparación | `@pytest.fixture` | `sin_archivo_env` | Ejercicio 05 |

Extra: con decimales se compara con **`pytest.approx`**, porque `0.1 + 0.2` no es exactamente `0.3` en un computador.

## B.4 `test_config.py` analizado con la receta

```python
def test_lee_variable_de_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    """PPA_LOG_LEVEL del entorno reemplaza al valor por defecto."""   # 1. qué aseguro
    monkeypatch.setenv("PPA_LOG_LEVEL", "DEBUG")                       # 2. preparar

    config = Settings()                                                # 3. actuar

    assert config.log_level == "DEBUG"                                 # 4. verificar
```

**¿De dónde sale `monkeypatch`?** Es una **fixture de pytest**. Cuando un test declara un parámetro con ese nombre, **pytest se lo entrega automáticamente**. Tú no llamas al test ni le pasas nada: pytest lee los nombres de los parámetros y busca las fixtures con esos nombres.

**La fixture `sin_archivo_env` con `autouse=True`:**
```python
@pytest.fixture(autouse=True)
def sin_archivo_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)          # me cambio a una carpeta vacía → tu .env real no se lee
    monkeypatch.delenv("PPA_LOG_LEVEL", raising=False)   # borro variables que pudieran existir
```
- `autouse=True` hace que se ejecute **sola antes de cada test** del archivo.
- Así cada test parte **limpio**, sin depender de tu PC (*test isolation*).
- Todo lo que hace `monkeypatch` **se deshace solo** al terminar el test.

## B.5 Cómo leer un fallo

| Ves | Significa | Qué revisar |
|---|---|---|
| `AssertionError: assert 'INFO' == 'DEBUG'` | Obtuviste `'INFO'`, esperabas `'DEBUG'` | ¿El valor esperado es correcto según la regla? |
| `Failed: DID NOT RAISE ValidationError` | Esperabas un error y no ocurrió | ¿Los datos son de verdad inválidos? |
| `NotImplementedError` | La función aún no está escrita | Es normal en TDD (rojo) |
| `ModuleNotFoundError` | No encuentra el archivo importado | Nombre del archivo o de la carpeta |
| `fixture 'x' not found` | Pediste un parámetro que no es fixture | ¿Escribiste bien `monkeypatch` o `tmp_path`? |

---

## Parte C: ahora practica

Ve a [`practica/README.md`](../../practica/README.md). Los ejercicios siguen **este mismo orden**:

1. **Ejercicio 01:** función + patrón 1 (y `approx`).
2. **Ejercicio 02:** cláusula de guarda + patrones 2 y 3.
3. **Ejercicio 03:** `Literal` + valores límite.
4. **Ejercicio 04:** **tu primera clase** + patrón 4.
5. **Ejercicio 05:** archivos + patrones 5 y 6.

Cada uno se hace así: **leer → ver fallar 🔴 → implementar → ver pasar 🟢 → escribir los tests TODO → comparar con `SOLUCIONES.md`**.

---

## Glosario de esta lección

| Término | Definición |
|---|---|
| Construcción incremental | Agregar una cosa, ejecutar, mirar y recién entonces agregar la siguiente |
| `model_config` | Configuración de la clase misma (prefijo, archivo `.env`), no un dato del pipeline |
| Arrange / Act / Assert | Preparar / Actuar / Verificar: las 3 partes de todo test |
| Fixture | Preparación que pytest entrega a un test cuando este la pide por su nombre |
| `autouse=True` | La fixture se aplica sola a todos los tests del archivo |
| `pytest.approx` | Compara decimales tolerando errores mínimos de redondeo |
| `NotImplementedError` | Error que indica "esta función aún no está escrita" |
