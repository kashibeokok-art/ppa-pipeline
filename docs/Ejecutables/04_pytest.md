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

## Ejercicios de práctica (carpeta `practica/`)
```powershell
uv run pytest practica/test_ejercicio_01_unidades.py -v    # un ejercicio
uv run pytest practica -v                                  # todos los ejercicios
```
El CI no ejecuta esta carpeta (solo `tests/`), así que los ejercicios sin terminar no rompen nada.

## Cómo leer los mensajes de fallo más comunes
| Mensaje | Significado |
|---|---|
| `AssertionError` | El `assert` dio falso: el resultado no es el esperado |
| `Failed: DID NOT RAISE <Error>` | Esperabas un error (`pytest.raises`) y el código funcionó bien. Revisa si los datos son de verdad inválidos |
| `ModuleNotFoundError` / `ImportError` | El archivo que importas no existe o el nombre está mal escrito |
| `fixture '<nombre>' not found` | Pediste un parámetro que pytest no conoce como fixture |
| `NotImplementedError` | La función todavía no está escrita (normal al empezar un ejercicio: fase roja de TDD) |

## Convenciones para que pytest encuentre los tests
- Van en la carpeta `tests/`.
- Los archivos empiezan con `test_` (ej. `test_bloques.py`).
- Las funciones empiezan con `test_` (ej. `def test_asignar_bloque(...)`).
- La carpeta `tests/` **refleja** la de `src/`: `src/ppa_pipeline/config.py` → `tests/test_config.py`; `src/ppa_pipeline/domain/bloques.py` → `tests/domain/test_bloques.py`.

## En VS Code
Panel **Testing** (ícono del matraz 🧪) → **Configure Python Tests** → **pytest** → **tests**.
Si no encuentra el intérprete: `Ctrl+Shift+P` → **Python: Select Interpreter** → `.venv`.
