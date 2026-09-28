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
