# 02 · Controles automáticos antes de cada commit (`pre-commit`)

> **Hito:** H1.5 · **Archivo principal:** `.pre-commit-config.yaml`
> **Conceptos:** Git Hooks, Shift-Left, pre-commit, YAML, fijar versiones (`rev`), Conventional Commits, staging area.

---

## 1. El problema que resuelve

Hasta ahora, antes de cada commit había que **acordarse** de ejecutar `ruff check`, `ruff format` y `pytest`. En este mismo proyecto ya pasó que:

- se hizo un commit con el mensaje `chore:: Inicializa...` (dos puntos dobles);
- `bloques.py` llegó al commit sin formatear.

Depender de la memoria no escala. Si en un equipo cada persona se acuerda "a veces", el repositorio termina inconsistente. La solución es que **la máquina lo revise sola, siempre**.

---

## 2. Conceptos

### Git Hook
Un **hook** ("gancho") es un script que **git ejecuta automáticamente** en ciertos momentos:

| Momento | Hook | Ejemplo de uso |
|---|---|---|
| Antes de crear el commit | `pre-commit` | Revisar y formatear el código |
| Al escribir el mensaje | `commit-msg` | Validar el formato del mensaje |
| Antes de subir a GitHub | `pre-push` | Correr tests más lentos |

Los hooks viven en la carpeta oculta `.git/hooks/`. Si un hook **falla**, git **cancela** la operación.

### `pre-commit` (la herramienta)
Escribir hooks a mano es tedioso y no se comparte con el equipo, porque `.git/` no entra al repositorio. La herramienta **`pre-commit`** resuelve esto:
- declaras los hooks en un archivo **versionado** (`.pre-commit-config.yaml`);
- la herramienta descarga cada hook en la **versión exacta** indicada;
- todos los que clonan el repositorio ejecutan **los mismos controles**.

### Shift-Left
Significa **mover los controles de calidad lo más temprano posible** (a la "izquierda" en la línea de tiempo del desarrollo):

```
 escribir código → commit → push → CI → producción → reporte Power BI
 ◄──── más barato corregir                      más caro corregir ────►
```

Un error detectado en tu PC en 2 segundos cuesta casi nada. El mismo error descubierto cuando un reporte muestra números malos cuesta horas y confianza.

---

## 3. Qué controles se activan

| Hook | Qué hace | Por qué importa |
|---|---|---|
| `trailing-whitespace` | Borra espacios al final de las líneas | Evita diferencias "invisibles" en git |
| `end-of-file-fixer` | Asegura un salto de línea final en cada archivo | Estándar POSIX; muchas herramientas lo esperan |
| `check-toml` | Verifica que los `.toml` estén bien escritos | Un `pyproject.toml` roto rompe todo el proyecto |
| `check-yaml` | Verifica que los `.yaml` estén bien escritos | Protege la propia configuración de pre-commit y el CI |
| `check-added-large-files` | Bloquea archivos de más de 500 KB | Git es para código, no para datos (Parquet, Excel) |
| `detect-private-key` | Bloquea claves privadas | Seguridad: la lección de H0 automatizada |
| `ruff-check --fix` | Linter; corrige lo que puede solo | Errores lógicos, imports, patrones peligrosos |
| `ruff-format` | Formateador | Estilo uniforme sin pensar en ello |
| `conventional-pre-commit` | Valida el mensaje `tipo: descripción` | Historial legible y consistente |

---

## 4. El archivo `.pre-commit-config.yaml`, línea por línea

```yaml
 1  # Controles automáticos que corren en cada `git commit`.
 2  # Instalar: uv run pre-commit install
 3  default_install_hook_types: [pre-commit, commit-msg]
 4
 5  repos:
 6    # 1. Higiene general de archivos
 7    - repo: https://github.com/pre-commit/pre-commit-hooks
 8      rev: v5.0.0
 9      hooks:
10        - id: trailing-whitespace
11        - id: end-of-file-fixer
12        - id: check-toml
13        - id: check-yaml
14        - id: check-added-large-files
15          args: ["--maxkb=500"]
16        - id: detect-private-key
17
18    # 2. Ruff: lint + formato
19    - repo: https://github.com/astral-sh/ruff-pre-commit
20      rev: v0.16.9
21      hooks:
22        - id: ruff-check
23          args: ["--fix"]
24        - id: ruff-format
25
26    # 3. Mensajes de commit con formato Conventional Commits
27    - repo: https://github.com/compilerla/conventional-pre-commit
28      rev: v4.0.0
29      hooks:
30        - id: conventional-pre-commit
31          stages: [commit-msg]
```

### Primero, cómo se lee YAML
YAML es un formato de configuración pensado para que lo lean personas:
- **La indentación define la estructura**, igual que en Python. Se usan espacios, nunca tabulaciones.
- `clave: valor` define un dato.
- `- ` al inicio de una línea es **un elemento de una lista**.
- `[a, b]` es una lista escrita en una sola línea.
- `#` inicia un comentario.

### Líneas 1-2: comentarios
Explican para qué sirve el archivo y cómo instalarlo. Documentación para el próximo que lo lea.

### Línea 3: `default_install_hook_types`
- Indica **en qué momentos** se instalan los hooks al ejecutar `pre-commit install`.
- `pre-commit` revisa los archivos antes del commit.
- `commit-msg` revisa el texto del mensaje.
- Sin esta línea solo se instalaría `pre-commit` y la validación del mensaje nunca correría.

### Línea 5: `repos:`
Es una **lista** de repositorios (en GitHub) de donde se descargan los hooks. Cada elemento empieza con `- repo:`.

### Líneas 7-8: `repo` y `rev`
- **`repo:`** es la dirección del repositorio que contiene los hooks.
- **`rev:`** es **la versión exacta** (una etiqueta de git) que se va a usar.
  - 🧠 Es el mismo principio del *lockfile* (`uv.lock`): **reproducibilidad**. Hoy y en un año, tú y tu CI ejecutan exactamente el mismo hook.
  - Las versiones **no se escriben de memoria**: `uv run pre-commit autoupdate` las actualiza a las más recientes.

### Líneas 9-16: `hooks:`
- Es la lista de hooks que se activan **de ese repositorio**, identificados por su `id`.
- Un repositorio puede ofrecer decenas de hooks; solo se usan los que declaras.
- **Línea 15, `args:`:** son argumentos extra para el hook. `--maxkb=500` fija el límite en 500 KB.

### Líneas 19-24: ruff
- `ruff-check` con `args: ["--fix"]`: el linter **corrige automáticamente** lo que puede, como ordenar imports o quitar un import sin uso.
- `ruff-format`: aplica el formato.
- 🧠 Hay que mantener el `rev` de ruff alineado con la versión de `pyproject.toml`, para que el hook y `uv run ruff` den los mismos resultados.
- ruff lee la configuración de tu `pyproject.toml` (`line-length`, `select`, `known-first-party`), así que el hook respeta las mismas reglas.

### Líneas 27-31: Conventional Commits
- **`stages: [commit-msg]`**: este hook no revisa archivos, revisa **el mensaje**. Por eso corre en la etapa `commit-msg`.
- Acepta mensajes como:
  - `feat: ...` (funcionalidad nueva)
  - `fix: ...` (corrección de un error)
  - `docs: ...` (documentación)
  - `chore: ...` (mantenimiento o configuración)
  - `test: ...` (tests)
  - `refactor: ...` (mejora sin cambiar el comportamiento)
- También acepta un **ámbito** opcional entre paréntesis: `feat(domain): ...`.
- Rechaza mensajes como `agregue precommit` o `chore:: algo`.

---

## 5. Paso a paso de la instalación

### Paso 1: instalar pre-commit como dependencia de desarrollo
```powershell
uv add --dev pre-commit
```
- `--dev` porque solo se necesita para **programar**, no para ejecutar el pipeline.
- Queda registrado en `pyproject.toml` (sección `[dependency-groups]`) y en `uv.lock`.

### Paso 2: crear `.pre-commit-config.yaml` en la raíz
Con el contenido de la sección 4. Debe estar en la raíz (junto a `.git/`), porque ahí lo busca la herramienta.

### Paso 3: actualizar a las versiones más recientes
```powershell
uv run pre-commit autoupdate
```
Consulta cada repositorio y reemplaza los `rev:` por la última versión publicada. Revisa el archivo después para ver qué cambió.

### Paso 4: instalar los hooks en el repositorio
```powershell
uv run pre-commit install
```
- Crea los scripts en `.git/hooks/pre-commit` y `.git/hooks/commit-msg`.
- ⚠️ Este paso **es por computador**: `.git/` no se sube a GitHub. Quien clone el repositorio debe ejecutar `pre-commit install` una vez. Por eso va escrito en el comentario de la línea 2 y, más adelante, en el README.

### Paso 5: primera ejecución sobre todo el proyecto
```powershell
uv run pre-commit run --all-files
```
- En uso normal, los hooks solo revisan los archivos **que estás commiteando** (los del *staging area*). Por eso son rápidos.
- `--all-files` revisa **todo** una vez, para partir limpio.
- Es normal que algunos hooks digan **`Failed`** y **modifiquen archivos**, por ejemplo `end-of-file-fixer` agregando el salto de línea final. **El hook ya corrigió el problema.** Ejecuta el comando otra vez y todo debería decir `Passed`.

### Paso 6: comprobar que protege

**Prueba A, mensaje incorrecto (debe rechazarse):**
```powershell
git add .
git commit -m "agregue precommit"
```

**Prueba B, mensaje correcto (debe pasar):**
```powershell
git commit -m "chore: configura pre-commit con ruff e higiene de archivos"
```
Verás cada hook con su estado (`Passed`, `Failed` o `Skipped`).

---

## 6. Qué pasa en cada `git commit` desde ahora

```
git commit -m "feat: ..."
  │
  ├─ 1. hook pre-commit (sobre los archivos en staging)
  │     ├─ trailing-whitespace ........ Passed
  │     ├─ end-of-file-fixer .......... Passed
  │     ├─ check-toml / check-yaml .... Passed
  │     ├─ check-added-large-files .... Passed
  │     ├─ detect-private-key ......... Passed
  │     ├─ ruff-check --fix ........... Passed
  │     └─ ruff-format ................ Passed
  │         (si alguno falla o modifica archivos → commit CANCELADO)
  │
  ├─ 2. hook commit-msg (sobre el texto del mensaje)
  │     └─ conventional-pre-commit .... Passed
  │         (si el formato es inválido → commit CANCELADO)
  │
  └─ 3. se crea el commit ✅
```

### ¿Qué hacer si un hook modifica un archivo?
Cuando un hook **corrige** un archivo (por ejemplo, lo formatea), el commit se cancela. La versión corregida quedó en tu **directorio de trabajo**, pero lo que estaba en el ***staging area*** sigue siendo la versión anterior. Solución:

```powershell
git add .          # agrega al staging la versión ya corregida
git commit -m "..."  # repite el commit; ahora los hooks pasan
```

🧠 **Staging area:** es la "zona de preparación" entre tus archivos y el historial. `git add` mueve cambios a esa zona y `git commit` guarda lo que hay en ella. El hook corrige tus archivos, no el staging.

---

## 7. ¿Por qué `pytest` no está en pre-commit?

- pre-commit debe ser **rápido** (segundos). Si cada commit tarda un minuto, la gente empieza a saltarse los hooks con `--no-verify`.
- Con 9 tests es instantáneo, pero con cientos de tests, incluidos tests con datos reales, sería lento.
- **Separación de responsabilidades en los controles:**

| Dónde | Qué corre | Velocidad |
|---|---|---|
| **pre-commit** (tu PC) | Formato, lint, secretos, archivos grandes, mensaje | Segundos |
| **CI** (GitHub Actions, H1.6) | Tests completos, en un entorno limpio (Linux) | Minutos |

Esto se llama **defensa en capas** (*defense in depth*): cada capa atrapa algo distinto y las lentas no bloquean el trabajo diario.

⚠️ **Nunca uses `git commit --no-verify`** para saltarte los hooks, salvo en una emergencia justificada. Saltarse los controles de forma habitual anula su valor.

---

## 8. Comandos útiles

| Comando | Qué hace |
|---|---|
| `uv run pre-commit install` | Instala los hooks en este repositorio (una vez por computador) |
| `uv run pre-commit run --all-files` | Ejecuta todos los hooks sobre todo el proyecto |
| `uv run pre-commit run ruff-check --all-files` | Ejecuta un solo hook |
| `uv run pre-commit autoupdate` | Actualiza los `rev` a las últimas versiones |
| `uv run pre-commit uninstall` | Desinstala los hooks |

---

## 9. Para la entrevista

> *"Apliqué shift-left con hooks de pre-commit: lint, formato, detección de secretos, bloqueo de archivos grandes y validación de Conventional Commits corren antes de cada commit, con las versiones fijadas para que sean reproducibles. Los tests completos corren en CI, para mantener rápido el ciclo local."*

---

## 10. Glosario de esta lección

| Término | Definición breve |
|---|---|
| Git Hook | Script que git ejecuta automáticamente en un momento dado (antes del commit, al escribir el mensaje…) |
| pre-commit (herramienta) | Administra hooks declarados en un archivo versionado y compartido |
| Shift-Left | Mover los controles de calidad lo más temprano posible |
| YAML | Formato de configuración donde la indentación define la estructura |
| `rev` | Versión exacta de un hook; garantiza reproducibilidad |
| `autoupdate` | Actualiza los `rev` a las últimas versiones publicadas |
| Staging area | Zona entre los archivos y el historial; `git add` la llena y `git commit` la guarda |
| Conventional Commits | Formato de mensaje `tipo(ámbito): descripción` |
| `--no-verify` | Salta los hooks; evitarlo salvo en una emergencia |
| Defense in Depth | Varias capas de control complementarias (pre-commit + CI) |

---

## 11. Preguntas de comprobación

1. Si un hook modifica un archivo y el commit se cancela, ¿qué tienes que hacer para completar el commit? ¿Por qué?
2. ¿Por qué `pytest` corre en CI y no en pre-commit?
3. ¿Por qué cada persona que clona el repositorio debe ejecutar `pre-commit install`, si el archivo de configuración ya está en git?
4. ¿Qué pasaría si no fijaras el `rev` de ruff y cada persona usara una versión distinta?
