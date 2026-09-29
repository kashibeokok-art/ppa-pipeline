# ruff: linter y formateador

## Instalar
```powershell
uv add --dev ruff
```

## Revisar el código
```powershell
uv run ruff check .                 # busca errores
uv run ruff check . --fix           # busca y corrige lo que puede solo
uv run ruff check tests/            # solo una carpeta
uv run ruff check . --show-files    # lista qué archivos analiza
```

## Formatear
```powershell
uv run ruff format .                # aplica el formato
uv run ruff format --check .        # solo revisa, no cambia nada
uv run ruff format --check --diff . # muestra qué cambiaría
```

## Qué corrige ruff solo y qué no
| Error | ¿Lo arregla `ruff format` o `--fix`? |
|---|---|
| Espacios, líneas en blanco, comillas, comas finales | ✅ `ruff format` |
| Imports desordenados (`I001`), imports sin uso (`F401`) | ✅ `ruff check --fix` |
| **Línea demasiado larga en un texto** (`E501`) | ❌ Hay que acortarla a mano (bloquea el commit) |
| Nombre inexistente (`F821`) | ❌ Hay que corregir el código |
| Variable asignada y nunca usada (`F841`) | ❌ Hay que quitar la asignación a mano (ej. `config = X()` dentro de `pytest.raises` → solo `X()`) |
| Expresión inútil (`B018`), ej. `1 / 0` sola en una línea | ❌ A mano. Si es a propósito, asígnala a `_`: `_ = 1 / 0` (`_` = "variable que no voy a usar") |
| Import que se agregó en el archivo equivocado (`F401`) | ✅ `--fix` lo borra, pero conviene entender **dónde** se usa: cada archivo importa solo lo suyo |

## Revisar y corregir solo la carpeta de práctica
```powershell
uv run ruff check practica --fix
uv run ruff format practica
```

## Experimento: estadísticas sobre el legado
```powershell
uv run ruff check OLD/ --select F --statistics
uv run ruff check OLD/ --select E,B,UP,PD,I --statistics
```

## Configuración (en `pyproject.toml`)
```toml
[tool.ruff]
line-length = 100
target-version = "py313"   # igual a requires-python: solo sugiere sintaxis que exista en esa versión
extend-exclude = ["OLD"]   # el legado no se toca

[tool.ruff.lint]
select = [
    "E", "F",   # E = estilo PEP 8 · F = errores lógicos (nombres inexistentes, imports sin uso)
    "I",        # isort: ordena y agrupa imports (estándar / terceros / propio)
    "B",        # bugbear: patrones que causan bugs sutiles o pérdida de datos
    "UP",       # pyupgrade: moderniza la sintaxis a la versión de Python
    "PD",       # pandas-vet: patrones de pandas propensos a errores
]

[tool.ruff.format]
exclude = ["*.md"]   # no reformatear los bloques de código de la documentación

[tool.ruff.lint.isort]
known-first-party = ["ppa_pipeline"]   # tu paquete va en su propio bloque de imports
```
