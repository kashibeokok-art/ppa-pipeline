# 03 · GitHub e Integración Continua (GitHub Actions)

> **Hito:** H1.6 · **Archivo principal:** `.github/workflows/ci.yml`
> **Conceptos:** repositorio remoto, `origin`, `push`, revisión previa a la publicación, Integración Continua (CI), workflow, runner, `uv sync --locked`, fallo silencioso de configuración.
> **Resultado:** repositorio público `github.com/kashibeokok-art/ppa-pipeline` con el CI en ✅ (ejecución del commit `40a39e7`).

---

## 1. Repositorio local vs. repositorio remoto

Hasta ahora, git solo existía **en tu computador** (repositorio **local**). GitHub guarda una copia **en internet** (repositorio **remoto**):

```
 Tu PC (local)                               GitHub (remoto: "origin")
 ─────────────                               ─────────────────────────
 git commit  → guarda en tu historial
 git push    ─────────────────────────────►  recibe tus commits
                                             └─ dispara el CI automáticamente
```

| Comando | Qué hace |
|---|---|
| `git remote add origin <url>` | Registra la dirección del remoto con el nombre `origin` (una vez) |
| `git push -u origin main` | Primera subida; `-u` vincula tu `main` con el `main` remoto |
| `git push` | Subidas siguientes |
| `git remote -v` | Muestra a qué remoto estás conectado |

🧠 **¿Por qué `origin`?** Es solo un **nombre** (un alias) para la URL; podría llamarse de cualquier forma. `origin` es la convención universal.

---

## 2. Revisión previa a la publicación (*Pre-publication Review*)

Un repositorio **público** no tiene vuelta atrás: aunque lo vuelvas privado, alguien pudo haberlo clonado o un buscador pudo haberlo indexado. Antes de publicar se revisa el **historial completo**, no solo los archivos actuales:

```powershell
git log --all --oneline -- OLD          # ¿OLD/ entró alguna vez al historial?  → nada = bien
git grep -n -i "password" HEAD          # ¿hay texto sensible en lo versionado?
```

**Resultado en este proyecto:** `OLD/` (que contiene la contraseña antigua) nunca entró al historial, gracias al `.gitignore` verificado en H0 con `git check-ignore`. El único dato interno visible es el nombre de la base de datos del legado en `CLAUDE.md`, que es de bajo riesgo.

---

## 3. Integración Continua (CI)

**Integración Continua** significa que **cada vez que subes código**, un servidor **limpio** lo descarga, reconstruye el entorno desde cero y ejecuta todos los controles.

| Pregunta | Respuesta del CI |
|---|---|
| ¿Funciona fuera de mi PC? | Corre en un Linux vacío. Si pasa ahí, el proyecto es **reproducible** |
| ¿Los tests pasan? | Aquí sí corre `pytest` completo, que no está en pre-commit |
| ¿Cómo lo demuestro? | El ✅ en GitHub es **evidencia pública** de calidad |

### Defensa en capas (cómo encaja con lo anterior)

| Capa | Dónde | Qué revisa | Tiempo |
|---|---|---|---|
| pre-commit | Tu PC, en cada `git commit` | Formato, lint, secretos, archivos grandes, mensaje | Segundos |
| **CI** | GitHub, en cada `git push` | Entorno desde cero + lint + formato + **tests** | 1–2 minutos |

---

## 4. El archivo `.github/workflows/ci.yml`, línea por línea

```yaml
 1  name: CI
 2
 3  on:
 4    push:
 5      branches: [main]
 6    pull_request:
 7
 8  jobs:
 9    calidad:
10      runs-on: ubuntu-latest
11      steps:
12        - uses: actions/checkout@v4
13        - uses: astral-sh/setup-uv@v6
14          with:
15            enable-cache: true
16        - run: uv sync --locked
17        - run: uv run ruff check .
18        - run: uv run ruff format --check .
19        - run: uv run pytest -v
```

| Línea | Significado |
|---|---|
| 1 `name:` | Nombre del workflow, como aparece en la pestaña **Actions** |
| 3 `on:` | **Cuándo** se ejecuta (*triggers*) |
| 4-5 `push: branches: [main]` | En cada push a la rama `main` |
| 6 `pull_request:` | En cada *pull request*: propuesta de cambio que se revisa antes de integrarse |
| 8 `jobs:` | Lista de trabajos. Pueden correr en paralelo |
| 9 `calidad:` | Nombre del trabajo (lo eliges tú) |
| 10 `runs-on: ubuntu-latest` | La máquina donde corre (*runner*): un **Linux** nuevo cada vez. Por eso importaba normalizar los finales de línea a LF |
| 11 `steps:` | Los pasos, en orden. Si uno falla, los siguientes no corren |
| 12 `uses: actions/checkout@v4` | `uses` ejecuta una **acción ya hecha**. `checkout` descarga tu código en el runner. `@v4` fija la versión, igual que `rev` en pre-commit |
| 13-15 `setup-uv` + `enable-cache` | Instala uv y guarda en caché las librerías descargadas, para que las próximas ejecuciones sean más rápidas |
| 16 `uv sync --locked` | Crea el entorno **exacto** de `uv.lock`. `--locked` hace que **falle** si `uv.lock` no coincide con `pyproject.toml` (por ejemplo, si agregaste una librería y no actualizaste el lock) |
| 17-19 `run:` | Ejecuta comandos, igual que en tu terminal |

### El resultado real de la primera ejecución

```
1. Set up job                  → success
2. Run actions/checkout@v4     → success
3. Run astral-sh/setup-uv@v6   → success
4. Run uv sync --locked        → success
5. Run uv run ruff check .     → success
6. Run uv run ruff format ...  → success
7. Run uv run pytest -v        → success   (9 tests de RN-01)
```

---

## 5. Lección real: fallo silencioso de configuración

En el primer push, el archivo quedó en:
```
.github/workflows/.github/workflows/ci.yml   ❌
```
GitHub **solo** busca workflows en el primer nivel de `.github/workflows/`. El archivo existía, estaba en git y se subió, **pero no hacía nada**, y **no apareció ningún error**. La API de GitHub mostraba **0 ejecuciones**.

**Corrección:**
```powershell
git mv .github/workflows/.github/workflows/ci.yml .github/workflows/ci.yml
```
`git mv` mueve el archivo y git lo registra como un **movimiento** (`{.github/workflows => }/ci.yml`), no como "borrado + archivo nuevo".

🧠 **Lecciones:**
1. **Verificar el resultado, no la acción.** "Creé el archivo" no es un criterio de aceptación; "vi el ✅ en Actions" sí lo es. En ingeniería de datos es igual: que un pipeline "corrió" no significa que haya cargado los datos correctos.
2. **Los errores de configuración suelen ser silenciosos.** Un archivo en el lugar equivocado no reclama; simplemente se ignora.
3. **El mensaje del commit debe coincidir con su contenido.** El commit `fix(ci): ... y ajusta stages de pre-commit` no incluyó el cambio de `.pre-commit-config.yaml`. Revisa con `git show --stat HEAD` qué archivos entraron realmente.

---

## 6. Comandos de esta lección

```powershell
git remote add origin https://github.com/<usuario>/ppa-pipeline.git   # conectar (una vez)
git push -u origin main                                                # primera subida
git push                                                               # subidas siguientes
git remote -v                                                          # ver el remoto
git mv <origen> <destino>                                              # mover un archivo versionado
git show --stat HEAD                                                   # qué archivos entraron al último commit
Get-ChildItem -Recurse .github                                         # verificar la ruta del workflow
uv sync --locked                                                       # lo mismo que hace el CI: falla si el lock está desactualizado
```

---

## 7. Para la entrevista

> *"Configuré integración continua con GitHub Actions: en cada push se reconstruye el entorno desde el lockfile en un runner Linux limpio y se ejecutan lint, formato y tests. Junto con los hooks de pre-commit forma una defensa en capas: controles rápidos en local y validación completa y reproducible en CI."*

---

## 8. Glosario

| Término | Definición breve |
|---|---|
| Repositorio remoto | Copia del repositorio en un servidor (GitHub) |
| `origin` | Nombre convencional del remoto principal |
| `push` | Subir commits locales al remoto |
| Pre-publication Review | Revisar el historial completo antes de hacer público un repositorio |
| CI (Continuous Integration) | Validación automática en un entorno limpio en cada cambio |
| Workflow | Archivo YAML que define cuándo y qué ejecuta GitHub Actions |
| Job / Step | Trabajo / paso dentro de un workflow |
| Runner | Máquina (Linux) donde corre el workflow; nueva en cada ejecución |
| `uses` / `run` | Usar una acción ya hecha / ejecutar un comando |
| `--locked` | Falla si `uv.lock` no coincide con `pyproject.toml` |
| Fallo silencioso | Error que no produce ningún mensaje; solo se detecta verificando el resultado |

---

## 9. Preguntas de comprobación

1. Tu `pytest` pasa en tu PC. ¿Qué podría hacer que falle en el CI? (Pista: algo instalado en tu PC que no está en `pyproject.toml`.)
2. ¿Por qué `uv sync --locked` es mejor que `uv sync` en el CI?
3. ¿Por qué hacer privado un repositorio que ya fue público no borra el riesgo de una credencial filtrada?
4. ¿Cómo te diste cuenta de que el primer workflow no funcionaba, si no hubo ningún error?
