# CI: GitHub Actions

## Archivo: `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  calidad:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4          # descarga el código del repositorio
      - uses: astral-sh/setup-uv@v6        # instala uv
        with:
          enable-cache: true
      - run: uv sync --locked              # crea el entorno EXACTO de uv.lock (falla si el lock está desactualizado)
      - run: uv run ruff check .           # lint
      - run: uv run ruff format --check .  # formato
      - run: uv run pytest -v              # tests
```

## Crear la carpeta del workflow (PowerShell)
```powershell
New-Item -ItemType Directory -Force .github/workflows
```
Crea `.github/workflows/`, que es donde GitHub busca los workflows. ⚠️ Ejecútalo desde la **raíz del proyecto**. Si lo ejecutas dentro de otra carpeta, se crea una ruta duplicada (`.github/workflows/.github/workflows/`) y GitHub **ignora el workflow sin dar ningún error**.

## Verificar que el workflow está en el lugar correcto
```powershell
Get-ChildItem -Recurse .github
```
Debe mostrar solo `.github\workflows\ci.yml`.

## Verificar localmente lo mismo que hará el CI
```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest -v
```
Si esto pasa en tu PC, lo más probable es que también pase en el CI.

## Ver el resultado
En GitHub: pestaña **Actions** del repositorio. ✅ verde = pasó · ❌ rojo = falló (haz clic para ver el paso y el error).
