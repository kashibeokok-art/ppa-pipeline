# Ejecutables: comandos del proyecto

Referencia rápida de los comandos aprendidos, agrupados por herramienta.
Todos se ejecutan en **PowerShell**, desde la **raíz del proyecto** (donde está `pyproject.toml`), salvo que se indique otra cosa.

| Archivo | Herramienta | Para qué |
|---|---|---|
| [01_uv.md](01_uv.md) | uv | Entorno, dependencias y ejecución de Python |
| [02_git.md](02_git.md) | git | Control de versiones, commits, `.gitignore`, `.gitattributes` |
| [03_ruff.md](03_ruff.md) | ruff | Linter y formateador |
| [04_pytest.md](04_pytest.md) | pytest | Tests |
| [05_pre-commit.md](05_pre-commit.md) | pre-commit | Controles automáticos antes de cada commit |
| [06_powershell.md](06_powershell.md) | PowerShell | Atajos del sistema (crear carpetas, etc.) |
| [07_ci_github_actions.md](07_ci_github_actions.md) | GitHub Actions | Integración continua: lint + tests en cada push |
| [08_mypy.md](08_mypy.md) | mypy | Verificación de tipos (tipado estático) |

## Rutina diaria (el orden típico)

```powershell
uv sync                              # 1. entorno al día
# ... programar ...
uv run ruff check . --fix            # 2. lint (corrige lo que puede)
uv run ruff format .                 # 3. formato
uv run mypy                          #    tipos
uv run pytest -v                     # 4. tests
git add .                            # 5. preparar
git status                           #    revisar ANTES de commitear
git commit -m "feat: ..."            # 6. commit (pre-commit revisa todo solo)
```
