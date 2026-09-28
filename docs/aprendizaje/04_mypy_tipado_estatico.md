# 04 · Verificación de tipos con mypy

> **Hito:** H1.7 · **Archivos:** `pyproject.toml` (`[tool.mypy]`), `.pre-commit-config.yaml` (hook local), `.github/workflows/ci.yml`, `tests/domain/test_bloques.py`
> **Conceptos:** tipado dinámico vs. estático, *type hints*, tipado gradual, `Any`, modo `strict`, `None` como valor, hook local, límites de las herramientas.

---

## 1. Tipado dinámico vs. estático

| | Tipado **dinámico** (Python por defecto) | Tipado **estático** (con mypy) |
|---|---|---|
| ¿Cuándo se detecta un error de tipo? | Al **ejecutar** esa línea | **Antes** de ejecutar, al revisar el código |
| Ejemplo | `logging.warninr(...)` falla recién cuando un archivo llega sin fecha, quizás meses después | mypy lo marca al instante: `Module has no attribute "warninr"` |

Python **no revisa tipos** hasta que el código corre. mypy lee tus **anotaciones de tipo** (*type hints*) y verifica, sin ejecutar nada, que todo sea coherente.

---

## 2. Anotaciones de tipo (*type hints*)

```python
def asignar_bloque(hora: int) -> Bloque:
#                       ^^^^^    ^^^^^^^^^
#                  tipo del      tipo del
#                  parámetro     retorno
```

Aplicado a los tests:

```python
def test_asignar_bloque(hora: int, bloque_esperado: str) -> None:
def test_asignar_bloque_hora_invalida(hora_invalida: int) -> None:
```

- `hora: int`: los valores de `parametrize` son enteros (0, 7, 8…).
- `bloque_esperado: str`: son textos ("A", "B"…). **Más preciso:** `Bloque` (importado desde `bloques.py`), que solo admite "A", "B" o "C".
- `-> None`: la función no devuelve un resultado útil.

### ¿Por qué `-> None` y no "nada"?
En Python, **`None` es un valor real**. Toda función devuelve algo; si no tiene `return`, devuelve `None` implícitamente:

```python
def f():
    x = 1


print(f())  # None
```

Declarar `-> None` le dice a mypy "no uses el resultado de esta función". Si alguien escribe `valor = test_asignar_bloque(1, "A") + 1`, mypy lo marca como error.

---

## 3. Tipado gradual y por qué mypy "se salta" código

**Tipado gradual (*Gradual Typing*):** Python permite anotar **solo una parte** del código. Por defecto, mypy:
- revisa las funciones **con** anotaciones;
- **se salta el cuerpo** de las funciones **sin** anotaciones.

**¿Por qué?** En `def procesar(df):` mypy no sabe qué es `df`, así que lo trata como **`Any`** ("cualquier cosa"). Revisar ese cuerpo daría mucho ruido y poca información útil.

**Ventaja: adopción gradual.** Un proyecto antiguo puede activar mypy sin recibir miles de errores de golpe, y agregar tipos módulo por módulo.

### Evidencia real sobre el legado (verificado el 2026-09-27)

| Comando | ¿Detecta `logging.warninr`? |
|---|---|
| `mypy OLD/funciones.py --ignore-missing-imports` | ❌ **No.** Encuentra 1 error sin relación, porque ninguna función del legado tiene anotaciones |
| `mypy OLD/funciones.py --ignore-missing-imports --check-untyped-defs` | ✅ **Sí**, en las **líneas 1601 y 2034** |

`--check-untyped-defs` obliga a revisar también las funciones sin anotaciones.

---

## 4. Modo `strict` en el proyecto nuevo

```toml
[tool.mypy]
python_version = "3.13"
strict = true
files = ["src", "tests"]
```

| Línea | Significado |
|---|---|
| `python_version` | Verifica con las reglas de Python 3.13 (igual que `requires-python` y el `target-version` de ruff) |
| `strict = true` | Activa todas las revisiones estrictas. Entre otras, **exige anotar todas las funciones** (`no-untyped-def`) y revisar su cuerpo |
| `files` | Qué revisa `uv run mypy` cuando no le pasas argumentos. `OLD/` queda fuera |

**¿Por qué `strict` desde el día uno?** El proyecto es nuevo y no tiene deuda que migrar. Exigir tipos ahora cuesta poco; agregarlos después a miles de líneas cuesta mucho.

**Así se veía el primer error** (antes de anotar los tests):
```
tests\domain\test_bloques.py:18: error: Function is missing a type annotation  [no-untyped-def]
```
El código entre corchetes (`no-untyped-def`) es el **nombre de la regla**. Sirve para buscarla en la documentación.

---

## 5. mypy en pre-commit: ¿por qué un hook **local**?

```yaml
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false
```

| Línea | Significado |
|---|---|
| `repo: local` | El hook no se descarga de GitHub: ejecuta un comando de **tu** entorno |
| `entry: uv run mypy` | El comando que se ejecuta |
| `language: system` | Usa lo que ya está instalado (uv), sin crear un entorno aparte |
| `types: [python]` | Solo corre si en el commit hay archivos Python |
| `pass_filenames: false` | Corre sobre todo lo definido en `files`, no solo sobre los archivos modificados |

🧠 **¿Por qué no usar un hook descargado, como con ruff?** Los hooks descargados corren en un **entorno aislado**, sin las librerías de tu proyecto. Cuando agregues pandas (H4), un mypy aislado no sabría qué es un `DataFrame` y daría **errores falsos**. `uv run mypy` usa tu entorno, con todas tus dependencias.

### Problema real: `Executable 'uv' not found`

El primer commit con el hook falló así:
```
mypy.....................................................................Failed
Executable `uv` not found
```

**Diagnóstico:**
- `uv.exe` existe y su carpeta (`C:\Users\Claud\.local\bin`) **sí está** en el PATH del usuario (en el registro de Windows).
- Pero **VS Code se abrió antes de instalar uv**. Un programa **copia las variables de entorno al iniciarse** y no se entera de los cambios posteriores. El terminal de VS Code, git y el hook heredan esa copia antigua, sin uv.

🧠 **Concepto: herencia de variables de entorno.** Cada proceso recibe una **foto** de las variables de entorno (como `PATH`) de su proceso padre, en el momento en que arranca. Cambiar el PATH no afecta a los procesos que ya están corriendo.

**Solución:** cerrar **todas** las ventanas de VS Code y volver a abrirlo. Después, verificar:
```powershell
where.exe uv                      # debe mostrar C:\Users\Claud\.local\bin\uv.exe
uv run pre-commit run --all-files # mypy debe decir Passed
```

**Lección:** "funciona en una terminal y no en otra" suele ser un problema de **entorno** (PATH, variables, versión), no de código.

---

## 6. mypy en el CI

```yaml
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy           # ← nuevo
      - run: uv run pytest -v
```

El orden va de lo más rápido y barato a lo más lento: si falla el formato, no tiene sentido correr los tests.

---

## 6.1 Error real: `Bloque.A` (tipo vs. valor)

Al cambiar la anotación de `str` a `Bloque`, se escribieron también los datos como `Bloque.A`:

```python
((0, Bloque.A),)  # ❌
```

mypy lo detectó en el pre-commit:
```
tests\domain\test_bloques.py:9: error: "<typing special form>" has no attribute "A"  [attr-defined]
```
Y pytest, al ejecutar, **ni siquiera cargó el archivo** (`AttributeError: A`). **mypy atrapó antes de ejecutar un error que habría roto el CI.**

**Causa:** `Bloque = Literal["A", "B", "C"]` es un **tipo**, no un contenedor de valores. No tiene atributos `A`, `B` ni `C`.

| | Qué es | Dónde va |
|---|---|---|
| `Bloque` | **Tipo**: describe qué valores son válidos | En las **anotaciones**: `bloque_esperado: Bloque` |
| `"A"` | **Valor** concreto | En los **datos**: `(0, "A")` |

**Corrección:** anotación `bloque_esperado: Bloque` ✅, datos `(0, "A")` ✅. mypy acepta `"A"` como `Bloque`; `"D"` no.

### La sintaxis `Bloque.A` existe: es un `Enum`
```python
from enum import StrEnum


class Bloque(StrEnum):  # una CLASE (POO, H2)
    A = "A"
    B = "B"
    C = "C"
```

| | `Literal` (usado en el proyecto) | `Enum` |
|---|---|---|
| Valores | Textos normales: `"A"` | Objetos: `Bloque.A` |
| Ventaja | Simple, funciona directo con pandas y SQL | Autocompletado; se puede recorrer |
| Cuándo | Valores fijos que viajan como texto | Valores con comportamiento o muy reutilizados |

Se eligió `Literal` porque los bloques viajan como texto en DataFrames y SQL.

---

## 7. Límite de las herramientas: la revisión humana sigue siendo necesaria

La función `subir_barras_a_sql`, definida **dos veces** en `funciones.py` (la segunda pisa a la primera), **no la detectó ni ruff ni mypy**.

| Herramienta | Atrapa | No atrapa |
|---|---|---|
| ruff | Nombres inexistentes, imports, patrones peligrosos, estilo | Atributos inexistentes de un módulo (`warninr`) |
| mypy | Tipos incorrectos, atributos inexistentes (en código revisado) | Todo lo que está en funciones sin anotar (por defecto); la redefinición de este caso |
| pytest | Lógica de negocio incorrecta | Lo que no tiene test |
| **Revisión humana** | Diseño, lógica duplicada, reglas de negocio mal entendidas | — |

🧠 **Defensa en capas:** cada capa reduce errores, pero ninguna los elimina todos.

---

## 8. Comandos de esta lección

```powershell
uv add --dev mypy                                                        # instalar
uv run mypy                                                              # revisar src y tests
uv run --with mypy mypy OLD/funciones.py --ignore-missing-imports        # experimento sin instalar
uv run --with mypy mypy OLD/funciones.py --ignore-missing-imports --check-untyped-defs
```

---

## 9. Para la entrevista

> *"Agregué verificación de tipos con mypy en modo estricto, en pre-commit y en CI. Al probarlo sobre el sistema legado comprobé que, sin anotaciones, mypy no revisa las funciones; al activar esa revisión detectó llamadas a métodos inexistentes que habrían fallado en producción. En el proyecto nuevo exijo tipos desde el día uno."*

---

## 10. Glosario

| Término | Definición breve |
|---|---|
| Tipado dinámico | Los tipos se revisan al ejecutar |
| Tipado estático | Los tipos se revisan antes de ejecutar (mypy) |
| *Type hint* | Anotación del tipo esperado (`: int`, `-> None`) |
| Tipado gradual | Se puede anotar solo una parte del código |
| `Any` | "Cualquier tipo"; mypy no puede verificarlo |
| `strict` | Modo que exige anotar todo y activa todas las revisiones |
| `None` | Valor real que representa "sin resultado"; lo devuelve toda función sin `return` |
| `--check-untyped-defs` | Revisa también las funciones sin anotaciones |
| Hook local | Hook de pre-commit que usa el entorno del proyecto |
| Tipo vs. valor | `Bloque` describe valores válidos; `"A"` es un valor concreto |
| `Literal` | Tipo que restringe a valores exactos; los valores siguen siendo textos |
| `Enum` / `StrEnum` | Clase cuyos miembros son valores con nombre (`Bloque.A`) |

---

## 11. Preguntas de comprobación

1. ¿Por qué mypy no detectó `warninr` en el legado con la configuración por defecto?
2. ¿Qué ventaja tiene el tipado gradual para un proyecto antiguo, y por qué en uno nuevo conviene `strict`?
3. ¿Por qué el hook de mypy es `local` y el de ruff no?
4. ¿Qué error de este proyecto no detectó ninguna herramienta, y qué lo habría detectado?
