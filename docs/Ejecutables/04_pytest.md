# pytest: tests

## Instalar
```powershell
uv add --dev pytest
```

## Configuración (en `pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Ejecutar tests
```powershell
uv run pytest                                  # todos
uv run pytest -v                               # cada caso por separado (verbose)
uv run pytest tests/domain/test_bloques.py     # solo un archivo
uv run pytest -k invalida                      # solo los tests cuyo nombre contiene "invalida"
uv run pytest -x                               # se detiene en el primer fallo
```

## Convenciones para que pytest encuentre los tests
- Van en la carpeta `tests/`.
- Los archivos empiezan con `test_` (ej. `test_bloques.py`).
- Las funciones empiezan con `test_` (ej. `def test_asignar_bloque(...)`).

## En VS Code
Panel **Testing** (ícono del matraz 🧪) → **Configure Python Tests** → **pytest** → **tests**.
Si no encuentra el intérprete: `Ctrl+Shift+P` → **Python: Select Interpreter** → `.venv`.
