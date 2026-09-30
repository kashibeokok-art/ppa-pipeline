# 08 · Línea de comandos (CLI) y códigos de salida

> **Hito:** H2.3 · **Archivos:** `src/ppa_pipeline/cli.py`, `src/ppa_pipeline/domain/periodo.py`, `tests/test_cli.py`, `tests/domain/test_periodo.py`
> **Conceptos:** CLI, punto de entrada (*entry point*), `typer`, decoradores de comando, **códigos de salida** (*exit codes*), *fail loud*, expresiones regulares, **composición** de módulos, `try` / `except`.

---

## 1. El problema: scripts sueltos y errores que no se notan

En el legado el pipeline se ejecutaba así:
- `python main_mensual.py`, que a su vez lanza **otros scripts** con `subprocess` ([main_mensual.py:297](../../OLD/main_mensual.py)).
- Los errores se **registraban y el programa seguía** ([main_mensual.py:249-288](../../OLD/main_mensual.py)).
- Si algo fallaba, el programa **terminaba igual como si todo hubiera salido bien**: un programador de tareas (Task Scheduler, GitHub Actions, Fabric) no tenía forma de saber que falló.

---

## 2. Conceptos

### 2.1 CLI y punto de entrada
Una **CLI** (*Command Line Interface*) es un programa que se usa escribiendo comandos en la terminal:
```powershell
ppa --help
ppa config
ppa run --periodo 2026-08
```
El **punto de entrada** (*entry point*) es la línea de `pyproject.toml` que crea el comando `ppa`:
```toml
[project.scripts]
ppa = "ppa_pipeline.cli:app"
```
Se lee: *"el comando `ppa` ejecuta el objeto `app` del módulo `ppa_pipeline/cli.py`"*.

### 2.2 Códigos de salida (*exit codes*)
Todo programa, al terminar, le entrega al sistema operativo **un número**:

| Código | Significado |
|---|---|
| `0` | Terminó **bien** |
| distinto de `0` (normalmente `1`) | **Falló** |
| `2` | Error de uso: faltó una opción o se escribió mal el comando (lo pone `typer` solo) |

**¿Por qué importa?** Nadie mira la pantalla cuando el pipeline corre a las 3 AM. Quien lo ejecuta (Task Scheduler, GitHub Actions, Fabric Data Pipeline) **solo mira el código de salida** para decidir si reintentar, alertar o seguir con el paso siguiente. Tu CI ya lo usa: si `pytest` termina con código distinto de 0, el paso se marca ❌.

En PowerShell, el código del último programa está en `$LASTEXITCODE`:
```powershell
uv run ppa run --periodo 2026-13
$LASTEXITCODE        # → 1
```

### 2.3 *Fail loud*
Si algo falla, el programa debe:
1. **registrar el error con su detalle** (`logger.exception`, que ahora incluye el *traceback* gracias a H2.2);
2. **terminar con código ≠ 0**.

Lo contrario (registrar y seguir, o terminar con código 0 tras un error) es el anti-patrón del legado.

---

## 3. `parsear_periodo`: expresiones regulares

Una **expresión regular** (*regex*) es un patrón para verificar el formato de un texto:
```python
_FORMATO = re.compile(r"^(\d{4})-(\d{2})$")
```

| Parte | Significado |
|---|---|
| `r"..."` | *Raw string*: las `\` se toman literales (necesario en regex) |
| `^` | Inicio del texto |
| `\d{4}` | Exactamente 4 dígitos |
| `(...)` | **Grupo**: la parte que quieres "capturar" para usarla después |
| `-` | Un guion literal |
| `$` | Fin del texto (nada después) |

```python
coincidencia = _FORMATO.match("2026-08")
coincidencia.group(1)   # "2026"  (texto; hay que convertirlo con int())
coincidencia.group(2)   # "08"

_FORMATO.match("agosto")   # None → no coincide
```

La función sigue el mismo patrón que tu `validar_mes` del ejercicio 02: **guarda del formato → guarda del mes → return**.

`{texto!r}` en un f-string muestra el texto **con comillas** (`'agosto'`). Así en el mensaje de error se distingue un texto vacío `''` de uno que no lo es.

---

## 4. `cli.py`: composición

`cli.py` no tiene lógica de negocio propia: **une las piezas que ya construiste**. Eso se llama **composición**:

```
ppa run --periodo 2026-08
        │
        ├─ Settings()                     ← H2.1  (config.py)
        ├─ nuevo_run_id()                 ← H2.2  (logging_setup.py)
        ├─ configurar_logging(nivel, id)  ← H2.2
        └─ parsear_periodo("2026-08")     ← H2.3  (domain/periodo.py)
                 │
           ¿error? ──sí──► logger.exception(...) + código de salida 1
                 │
                 no ──► logs de inicio/fin + código de salida 0
```

### 4.1 Decoradores de comando
```python
app = typer.Typer(...)

@app.command()
def run(periodo: str = typer.Option(..., help="...")) -> None:
```
- `@app.command()` es un **decorador** (como `@pytest.fixture`): registra la función como un comando llamado `run`.
- `typer` lee la firma de la función para armar la CLI: el parámetro `periodo` se convierte en la opción `--periodo`.
- `typer.Option(...)`: los `...` (*Ellipsis*) significan **obligatorio**. Si no lo escribes, `typer` termina con código 2 y te muestra la ayuda.
- El **docstring** de la función aparece en `ppa --help`.

### 4.2 `try` / `except`: capturar el error sin ocultarlo
```python
    try:
        anio, mes = parsear_periodo(periodo)
        logger.info("Inicio del pipeline para %04d-%02d", anio, mes)
        logger.info("Fin del pipeline")
    except Exception:
        logger.exception("El pipeline falló")
        raise typer.Exit(code=1) from None
```
| Pieza | Qué hace |
|---|---|
| `try:` | "Intenta ejecutar esto…" |
| `except Exception:` | "…y si ocurre **cualquier** error, entra aquí" |
| `logger.exception(...)` | Registra el error **con su detalle completo** (nivel ERROR + traceback) |
| `raise typer.Exit(code=1)` | Termina el programa con **código de salida 1** |
| `from None` | Evita que Python vuelva a imprimir el mismo error como texto plano (ya quedó en el log JSON) |

⚠️ **Tragarse la excepción** (*swallowing*) es escribir `except Exception: pass`, o solo registrarla y seguir. Es el anti-patrón del legado. Aquí se captura **para registrarla y terminar con un código de error**, no para ocultarla.

🧠 **¿Por qué `%04d-%02d` y no un f-string en `logger.info`?** El módulo `logging` arma el texto **solo si el mensaje se va a escribir**. Si el nivel lo filtra, no gasta tiempo formateándolo. Es la convención recomendada para logging.

---

## 5. Los tests con `CliRunner`

```python
from typer.testing import CliRunner
runner = CliRunner()

resultado = runner.invoke(app, ["run", "--periodo", "2026-08"])
resultado.exit_code   # el código de salida
resultado.output      # lo que se imprimió en pantalla
resultado.stderr      # lo que salió por stderr (ahí escriben tus logs)
```
`CliRunner` ejecuta el comando **dentro del test**, como si lo escribieras en la terminal, y captura todo.

---

## 6. Para la entrevista

> *"El pipeline tiene una CLI con typer como único punto de entrada. Compone la configuración validada, el logging estructurado con run_id y la validación de parámetros. Ante cualquier error lo registra con su traceback y termina con código de salida 1, para que el orquestador (Task Scheduler, GitHub Actions o Fabric) detecte la falla y actúe."*

---

## 7. Glosario

| Término | Definición |
|---|---|
| CLI | Programa que se usa escribiendo comandos en la terminal |
| Entry point | Línea de `pyproject.toml` que crea un comando (`ppa`) apuntando a código Python |
| Exit code | Número que devuelve un programa al terminar: 0 = bien, ≠ 0 = falló |
| `$LASTEXITCODE` | Variable de PowerShell con el código de salida del último programa |
| Fail loud | Ante un error: registrarlo con detalle y terminar con código ≠ 0 |
| Swallowing exceptions | Capturar un error y seguir como si nada (anti-patrón) |
| Regex | Patrón para validar o extraer partes de un texto |
| Grupo de regex | Parte entre paréntesis que se puede extraer con `.group(n)` |
| Composición | Construir algo nuevo uniendo piezas ya existentes |
| `CliRunner` | Herramienta para ejecutar una CLI dentro de un test |

---

## 8. Preguntas de comprobación

1. ¿Por qué un orquestador necesita el código de salida si ya hay logs?
2. ¿Qué pasaría si el `except` solo hiciera `logger.exception(...)`, sin `raise typer.Exit(code=1)`?
3. ¿Qué devuelve `_FORMATO.match("2026-8")` y por qué?
4. ¿Por qué `cli.py` no tiene lógica de negocio propia?
