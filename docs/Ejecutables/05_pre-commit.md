# pre-commit: controles automáticos antes de cada commit

Explicación completa: [../aprendizaje/02_pre_commit_hooks.md](../aprendizaje/02_pre_commit_hooks.md)

## Instalar la herramienta
```powershell
uv add --dev pre-commit
```

## Configuración: `.pre-commit-config.yaml` (en la raíz)
```yaml
# Controles automáticos que corren en cada `git commit`.
# Instalar: uv run pre-commit install
default_install_hook_types: [pre-commit, commit-msg]
default_stages: [pre-commit]   # cada hook corre solo antes del commit, salvo que declare otra etapa

repos:
  # 1. Higiene general de archivos
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key

  # 2. Ruff: lint + formato
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.9
    hooks:
      - id: ruff-check
        args: ["--fix"]
      - id: ruff-format

  # 3. Mensajes de commit con formato Conventional Commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```
> ⚠️ En YAML la indentación importa: usa espacios, nunca tabulaciones. Copia el bloque tal cual, respetando los espacios al inicio de cada línea.

## Comandos
```powershell
uv run pre-commit autoupdate                      # actualiza los rev a las últimas versiones
uv run pre-commit install                         # instala los hooks (una vez por computador)
uv run pre-commit run --all-files                 # ejecuta todo sobre todo el proyecto
uv run pre-commit run ruff-check --all-files      # ejecuta un solo hook
uv run pre-commit uninstall                       # desinstala los hooks
```

## Si un hook modifica archivos y cancela el commit
```powershell
git add .                 # agrega la versión ya corregida al staging
git commit -m "..."       # repite el commit
```

> ⛔ Evita `git commit --no-verify`: salta todos los controles.

## Si los hooks aparecen repetidos al hacer commit
Algunos hooks no declaran su etapa y corren en `pre-commit` **y** en `commit-msg`. Se corrige con esta línea en el YAML:
```yaml
default_stages: [pre-commit]
```
