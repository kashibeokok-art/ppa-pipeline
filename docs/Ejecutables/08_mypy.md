# mypy: verificación de tipos

## Instalar
```powershell
uv add --dev mypy
```
Queda como dependencia de desarrollo, igual que ruff y pytest.

## Configuración (en `pyproject.toml`)
```toml
[tool.mypy]
python_version = "3.13"
strict = true
files = ["src", "tests"]
```
- `strict = true` activa todas las revisiones estrictas, incluida la obligación de anotar tipos en todas las funciones.
- `files` indica qué revisar cuando ejecutas `mypy` sin argumentos. `OLD/` queda fuera.

## Ejecutar
```powershell
uv run mypy
```
Revisa las carpetas definidas en `files`. Si todo está bien, responde `Success: no issues found`.

## Experimento: mypy sobre el legado (sin instalarlo en el proyecto)
```powershell
uv run --with mypy mypy OLD/funciones.py --ignore-missing-imports
uv run --with mypy mypy OLD/funciones.py --ignore-missing-imports --check-untyped-defs
```
- `--with mypy` lo instala en un entorno **temporal**, sin tocar `pyproject.toml`.
- `--ignore-missing-imports` evita errores por librerías que no están instaladas (selenium, etc.).
- `--check-untyped-defs` revisa **también** las funciones sin anotaciones. Sin esta opción, mypy las **salta**, y por eso no ve `logging.warninr`.

## Hook local en `.pre-commit-config.yaml`
```yaml
  # 4. mypy: tipos (hook local: usa el entorno del proyecto)
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false
```
- `repo: local` significa que el hook no se descarga: ejecuta un comando de **tu** entorno.
- `language: system` usa lo que ya está instalado (uv).
- `pass_filenames: false` hace que corra `mypy` con la configuración de `files`, no solo sobre los archivos modificados.

## Paso en el CI (`.github/workflows/ci.yml`)
```yaml
      - run: uv run mypy
```
Va después de `ruff format --check` y antes de `pytest`.
