# Bitácora de aprendizaje: Pipeline PPA

> Notas de estudio del proyecto: **qué se hizo, por qué se hace y cómo se llama**.
> Se actualiza al cerrar cada hito. El detalle técnico y las decisiones completas están en `CLAUDE.md` (§10 ADR, §11 bitácora).

---

## 0. La lógica general

Un proyecto de datos profesional **no empieza escribiendo código**. Empieza entendiendo el problema, asegurando lo que existe y definiendo qué se va a construir. Recién entonces se prepara el terreno técnico.

```
1. Diagnóstico → 2. Seguridad → 3. Estrategia → 4. Descubrimiento de fuentes → 5. Requerimientos
→ 6. Diseño por preguntas → 7. Entorno → 8. Repositorio → 9. Proyecto reproducible → (código)
```

---

## H0: Cimientos Seguros y Requerimientos ✅

### Paso 1: Diagnóstico del sistema existente
- **Qué:** se leyeron los 17 scripts del legado y se hizo un inventario de flujos, fuentes y tablas, más una lista de problemas ordenados por severidad.
- **Por qué:** no se puede mejorar lo que no se entiende. El diagnóstico dice **qué evitar** en el sistema nuevo.
- **Anti-patrones encontrados:**
  - Credenciales escritas en el código.
  - Reintentos que no se detienen al tener éxito.
  - Cargas a SQL que pueden quedar a medias y nunca se corrigen.
  - Sin capa de datos crudos: se borran las descargas y no se puede reprocesar.
  - Un archivo de 2.400 líneas que mezcla todo (*god module*).
  - Sin tests, sin git y sin archivo de dependencias.
- 🧠 **Conceptos:** *Legacy Assessment*, *Technical Debt* (deuda técnica), *Anti-pattern*.

### Paso 2: Seguridad primero
- **Qué:** se detectó una contraseña de SQL escrita en el código. La credencial está obsoleta y no se porta al proyecto nuevo.
- **Por qué:** un secreto que estuvo en el código se considera **comprometido**, porque queda en el historial de git, en los respaldos (OneDrive) y en las copias. Borrar la línea no basta: hay que **rotarlo**.
- 🧠 **Conceptos:** *Secrets Management*, *Credential Rotation*, *Least Privilege*.

### Paso 3: Decidir la estrategia
- **Qué:** se decidió **reescribir desde cero** (*greenfield*) en vez de refactorizar. El legado se usa solo como:
  1. **Especificación funcional:** qué necesita el negocio.
  2. **Oráculo de pruebas:** con qué números comparar.
  3. **Catálogo de anti-patrones:** qué no repetir.
- **Por qué:** el legado no tenía estructura rescatable, y construir desde cero obliga a entender y defender cada decisión.
- 🧠 **Conceptos:** *Greenfield Rewrite* vs. *Strangler Fig* (reemplazo gradual), *Test Oracle*, *ADR* (ver §Anexo A).

### Paso 4: Descubrir fuentes (*Source Discovery*)
- **Qué:** antes de decidir cómo extraer los datos, se investigó qué ofrece el Coordinador Eléctrico Nacional (CEN).
- **Hallazgos:**

| Dato | Acceso |
|---|---|
| CMg real, contratos, barras | ✅ API oficial (portal.api.coordinador.cl) |
| Retiros e inyecciones | Solo en los ZIP de Plabacom |
| Descargas de Plabacom | API interna (URLs prefirmadas de S3). Requiere una clave **propia**; no se usa la clave incrustada en su web |

- **Por qué:** el orden de preferencia es **API oficial > descarga de archivos > scraping**. Una API es estable, tiene contrato y se puede auditar. El scraping (Selenium) se rompe cuando cambia la web.
- 🧠 **Conceptos:** *API Key*, *Rate Limiting*, *Pagination*, *Presigned URL*, *Undocumented API*.

### Paso 5: Levantar requerimientos
- **Qué:** `docs/requerimientos.md` con 19 reglas de negocio (RN-01 a RN-19) en lenguaje de negocio, sin código.
- **Por qué:** en una reescritura, el mayor riesgo es **perder reglas que solo existían dentro del código antiguo**, como que la hora 24 pertenece al bloque A. Escribirlas las vuelve visibles, discutibles y verificables.
- **Decisiones clave:**

| Tema | Decisión |
|---|---|
| Horario de verano | La hora extra de abril va al bloque A; la hora faltante de septiembre no se considera |
| Signo | Energía en valor absoluto |
| Medición oficial | `medida_3` |
| Valorización | P×Q cada 15 minutos y después suma a la hora |
| Agregación a la hora | Energía se **suma**, CMg se **promedia** |

- 🧠 **Conceptos:**
  - **Medidas aditivas / semi-aditivas / no aditivas:**
    - **Aditiva:** se puede sumar a lo largo de **todas** las dimensiones (energía).
    - **Semi-aditiva:** se suma entre entidades pero **no en el tiempo** (nivel de un embalse, saldo de una cuenta).
    - **No aditiva:** sumarla no tiene sentido en ninguna dimensión; se promedia o se recalcula (precios como el CMg, porcentajes, ratios).
  - **Sesgo de agregación (*Aggregation Bias*):** calcular después de agregar da un resultado distinto a calcular en el detalle. En valorización:
    ```
    Valor real      = Σ Pᵢ·Qᵢ
    Valor agregado  = promedio(P) · Σ Qᵢ
    Diferencia      = n · Cov(P, Q)
    ```
    El error es la **covarianza entre precio y consumo** dentro de la hora. Por eso se calcula en el grano más fino (15 minutos) y después se agrega.
  - **Trazabilidad de requerimientos (*Requirements Traceability*):** un ID fijo como `RN-13` conecta la regla con el código, el test y el commit. A diferencia de una lista numerada, no cambia si se insertan o reordenan reglas.
  - **Riesgo aceptado (*Accepted Risk*):** rellenar las horas sin medición con cero sesga el mínimo y el promedio. Se decidió asumirlo y quedó documentado.

### Paso 6: Diseño guiado por preguntas (contrato con el consumidor)
- **Qué:** un documento por dominio (`contratos`, `retiros`, `inyecciones`, `cmg`), cada uno con **propósito → preguntas de negocio → columnas**.
- **Por qué:** un pipeline existe para **responder preguntas**. Lo que ninguna pregunta necesita no se construye (**YAGNI**, *You Aren't Gonna Need It*). En contratos se pasó de unas 95 columnas a 14.
- **Decisiones clave:**
  - **Barras por nombre:** el ID de la fuente no es confiable (*untrusted source key*). En H7 se normalizará el nombre y se generará una clave propia.
  - **Contratos en formato largo:** una fila por barra.
    - ⚠️ La energía está a nivel de **contrato**, así que un contrato con 3 barras la repite 3 veces. Un `SUM` en Power BI la triplica (**doble conteo**).
    - ✅ **Solución de modelo:** separar las tablas por granularidad: `contrato` (una fila por contrato, con la energía) y `contrato_barra` (una fila por barra, sin energía).
    - 🩹 **Parche DAX:** agregación en dos pasos, `SUMX(VALUES(Contratos[ID]), MAX(Contratos[Energia]))`. **MAX o AVG solos no sirven** al sumar varios contratos.
  - **El RUT** es la clave natural de las empresas y reemplaza la búsqueda de nombres por scraping.
  - **CMg:** los supuestos quedaron documentados (API SIP, valor real, USD/MWh).
- 🧠 **Conceptos:**
  - *Question-Driven Design*, *Data Minimization*.
  - *Grain* (granularidad): qué representa exactamente una fila.
  - *Double Counting* (doble conteo).
  - *Conformed Dimension*: una misma dimensión, como empresa, compartida por varios dominios para poder cruzarlos.
  - *Silent Nulls*: un cruce que falla sin dar error, por ejemplo un retiro que queda sin CMg.
  - *Documented Assumption*: un supuesto escrito y vigente hasta que alguien lo corrija.
  - *Requirements Consistency Check*: cada regla debe servir a una pregunta y cada pregunta debe tener sus reglas.

### Paso 7: Elegir el entorno
- **Qué:** entorno propio, solo con datos públicos (ADR-003).
- **Por qué:** nunca se desarrolla contra producción. Además, con datos públicos el repositorio puede ser público y servir de portafolio, sin exponer información de la empresa.
- 🧠 **Conceptos:** separación de entornos (*Dev / Test / Prod*), *Data Classification*, datos personales (el RUT de personas naturales es un dato protegido).

### Paso 8: Repositorio y control de versiones
- **Qué:** `git init`, `.gitignore` en la raíz, y verificación con `git check-ignore -v` de que `OLD/` (que contiene la contraseña) no entre al historial.
- **Por qué:** git es el historial de auditoría y la red de seguridad. El `.gitignore` define lo que no entra **nunca**. Se revisa `git status` **antes** del primer commit, porque algo que entra al historial es muy difícil de sacar.
- **Lecciones:**
  - Un `.gitignore` solo aplica a su carpeta y a las subcarpetas.
  - Conviene ignorar **por ubicación** (`data/`) y no por extensión (`*.json`), para no bloquear archivos que sí son código, como los `.json` del formato `.pbip` de Power BI.
  - Nunca hacer `git add .` a ciegas.
- 🧠 **Conceptos:** *Version Control*, *Working Directory / Staging Area / Commit*, *Repository Root*.

---

## H1: Proyecto Reproducible (H1.1–H1.7 ✅)

### Paso 9: Gestor de proyecto y dependencias (H1.1) ✅
- **Qué:** `uv init --package`, que generó `pyproject.toml`, `uv.lock`, `.python-version` y la estructura `src/ppa_pipeline/`.
- **Por qué:** cualquier persona o servidor debe poder reconstruir **exactamente** el mismo entorno con `uv sync`. El legado no tenía archivo de dependencias: si ese computador se perdía, reconstruirlo era a prueba y error.
- **Regla:** se versiona **la receta** (`pyproject.toml`, `uv.lock`), **no el resultado** (`.venv/`, `__pycache__`, datos). El `.venv` además depende de la plataforma (binarios y rutas de Windows).
- **Qué agrega `--package`:**
  1. **Estructura `src/`** (*src layout*): el código solo se puede importar si **está instalado**, no por la carpeta desde donde se ejecuta. El legado fallaba en esto (`import funciones`, `os.getcwd()`).
  2. **Proyecto instalable:** `uv sync` instala tu propio código en el `.venv`.
  3. **Punto de entrada** (*entry point*): `[project.scripts]` crea el comando `ppa-pipeline`.
- 🧠 **Conceptos:** *Packaging*, *Lockfile*, *src layout*, *Entry Point*, *Reproducibility*.

### Paso 10: Estructura por capas (H1.2) ✅
- **Qué:** se crearon los paquetes `extract/`, `bronze/`, `silver/`, `domain/`, `quality/` y `load/`, cada uno con su `__init__.py`.
- **Por qué:** **separación de responsabilidades**. Cada módulo hace una sola cosa. Es lo opuesto al *god module* del legado, donde probar una regla de bloques obligaba a cargar Selenium y SQL.
- **`domain/` separado de `silver/`:** las reglas de negocio son **funciones puras**, sin pandas, archivos ni bases de datos. Eso las hace testeables, reutilizables e independientes de la tecnología (arquitectura hexagonal, *Ports & Adapters*).
- 🧠 **Conceptos:** *Separation of Concerns*, *Domain Layer*, paquete (`__init__.py`).

### Paso 11: Análisis estático con ruff (H1.3) ✅
- **Qué:** ruff configurado en `pyproject.toml` (reglas E, F, I, B, UP y PD, con `OLD/` excluido).
- **Por qué:** detecta errores **sin ejecutar** el código. Sobre el legado encontró 64 errores lógicos, entre ellos **42 llamadas a una función inexistente (`safe_prent`)**, que hacían caer un script completo.
- **Lección:** cada herramienta atrapa cosas distintas (**defensa en capas**). `logging.warninr` y la función duplicada no los detecta ruff; los detecta **mypy**.
- 🧠 **Conceptos:** *Static Analysis*, *Linting*, *Formatting*, *Mutable Default Argument*, *Explicit over Implicit* (`known-first-party`). Lección: [aprendizaje/](aprendizaje/README.md).

### Paso 12: Primera regla de negocio con TDD (H1.4) ✅
- **Qué:** RN-01 (bloques horarios) implementada en `domain/bloques.py`, con 9 tests escritos **antes** que el código.
- **Por qué:** el test es la **especificación ejecutable** de la regla.
- **Lección real:** el test tenía `(23, "C")`, un error de negocio. **Un test incorrecto es peor que no tener test**, porque certifica el error en verde. Los casos se derivan de la regla escrita.
- 🧠 **Conceptos:** TDD (rojo → verde → refactor), *Boundary Value Testing*, *Guard Clause*, `Literal`, *type hints*. Lección: [01_funciones_y_tests_rn01.md](aprendizaje/01_funciones_y_tests_rn01.md).
- **Extra:** `.gitattributes` para normalizar los finales de línea a LF (el proyecto corre en Windows y en Linux).

### Paso 13: Controles antes de cada commit (H1.5) ✅
- **Qué:** `pre-commit` con higiene de archivos, detección de claves privadas, bloqueo de archivos grandes, ruff y validación de Conventional Commits.
- **Por qué:** ***Shift-Left***: detectar errores en segundos en tu PC, no en producción. No depender de la memoria.
- **Lección:** los hooks sin etapa declarada corren en `pre-commit` y también en `commit-msg`; `default_stages: [pre-commit]` lo evita.
- 🧠 **Conceptos:** *Git Hooks*, *Shift-Left*, YAML, `rev` fijado, *staging area*. Lección: [02_pre_commit_hooks.md](aprendizaje/02_pre_commit_hooks.md).

### Paso 14: GitHub + Integración Continua (H1.6) ✅
- **Qué:** repositorio **público** en `github.com/kashibeokok-art/ppa-pipeline` y un workflow de GitHub Actions (`uv sync --locked` → ruff → pytest) en un Linux limpio. Primera ejecución: ✅.
- **Por qué:** demuestra **reproducibilidad real**, corre los tests completos y deja **evidencia pública** de calidad.
- **Antes de publicar:** se revisó el **historial completo** (`git log --all -- OLD`, `git grep`). `OLD/` nunca entró.
- **Lección real:** el workflow quedó en una ruta duplicada y GitHub lo **ignoró sin dar error** (0 ejecuciones). **Verificar el resultado, no la acción.**
- 🧠 **Conceptos:** repositorio remoto, CI, *workflow*, *runner*, `--locked`, fallo silencioso, *Pre-publication Review*. Lección: [03_github_y_ci.md](aprendizaje/03_github_y_ci.md).

### Paso 15: Verificación de tipos con mypy (H1.7) ✅
- **Qué:** mypy en modo `strict` sobre `src` y `tests`, como hook **local** de pre-commit y como paso del CI. Se anotaron los tipos de las funciones de test.
- **Por qué:** Python solo revisa los tipos al ejecutar. mypy los revisa **antes**.
- **Lección real:** sobre el legado, mypy por defecto **no detectó** `logging.warninr`, porque se salta las funciones sin anotaciones (**tipado gradual**). Con `--check-untyped-defs` lo encontró en **dos** lugares (líneas 1601 y 2034). La función `subir_barras_a_sql` duplicada **no la detectó ninguna herramienta**, así que la revisión humana sigue siendo necesaria.
- 🧠 **Conceptos:** *Static Typing*, *Gradual Typing*, `Any`, `strict`, `None` como valor, hook local vs. entorno aislado. Lección: [04_mypy_tipado_estatico.md](aprendizaje/04_mypy_tipado_estatico.md).

- **Incidencias reales resueltas:**
  - `Executable 'uv' not found` en el hook: VS Code se había abierto antes de instalar uv y tenía una copia vieja del PATH (**herencia de variables de entorno**). Se resolvió reiniciando VS Code.
  - `Bloque.A`: `Bloque` es un `Literal` (un **tipo**), no un `Enum`. Los datos van como `"A"` y la anotación como `Bloque`. mypy lo atrapó antes de que rompiera el CI.
  - `(END)` en la terminal: es el **paginador** de git (`less`); se sale con `q`.
- **Resultado:** CI ✅ con `uv sync --locked` → ruff → mypy → pytest.

### ✅ H1 cerrado (2026-09-28)
El proyecto se reconstruye desde cero en cualquier máquina (`uv sync --locked`) y cada cambio pasa por dos capas de control: **pre-commit** en tu PC (segundos) y **CI** en GitHub (minutos).

### Mini-quiz H1: respuestas modelo (resultado: 2 correctas + 3 parciales, aprobado)

1. **`pyproject.toml` vs. `uv.lock` vs. `.venv/`:** `pyproject.toml` declara qué se necesita y en qué **rango** de versiones. `uv.lock` fija la versión **exacta** de todo, incluidas las dependencias indirectas. `.venv/` no va a git porque es pesado y, sobre todo, **depende del sistema operativo**. Regla: se versiona **la receta**, no el resultado.
2. **¿Por qué separar `domain/`?** Las reglas de negocio son funciones puras: se **testean sin nada externo** (pandas, archivos, SQL), se reutilizan y sobreviven a los cambios de tecnología.
3. **Test incorrecto en verde:** es peligroso porque **certifica el error**. Se evita derivando los casos de la **regla escrita** (RN-01 en `requerimientos.md`), citando la regla en el docstring (trazabilidad) y con revisión de alguien del negocio.
4. **mypy y `warninr`:** por defecto mypy **se salta las funciones sin anotaciones** (tipado gradual), y el legado no tenía ninguna. En el proyecto se usa `strict = true`, que **obliga** a anotar todas las funciones, así que no queda código sin revisar.
5. **pre-commit vs. CI:**

| | pre-commit | CI |
|---|---|---|
| Dónde | Tu PC | Computadora nueva de GitHub (Linux) |
| Cuándo | Cada `git commit` | Cada `git push` |
| Qué | Formato, lint, mypy, secretos, archivos grandes, mensaje | Todo lo anterior + **pytest**, desde un entorno limpio |
| Tiempo | Segundos | 1–2 minutos |

   `pytest` va en el CI porque pre-commit debe ser instantáneo. Con cientos de tests, un commit lento hace que la gente se salte los controles.

**A reforzar:** tests derivados de la regla escrita (H4) y qué es el CI (vuelve en H3 y H9).

**Pregunta de verificación: `pip install` sin `uv add`, ¿dónde falla?** No falla en tu PC ni en pre-commit (la librería está en tu `.venv`). **Falla en el CI**, que parte de una máquina vacía e instala solo lo que dice `uv.lock` → `ModuleNotFoundError`. Es el síntoma clásico de *"en mi máquina funciona"*. Regla: agregar librerías siempre con `uv add`.

---

## H2: Configuración y Observabilidad (en curso)

### Paso 16: Configuración fuera del código y primera clase (H2.1) ✅
- **Qué:** `config.py` con una clase `Settings` (pydantic-settings) que lee variables `PPA_*` del entorno y de `.env`, valida tipos y guarda la clave de la API como `SecretStr`.
- **Por qué:** **Twelve-Factor, factor III**: la configuración cambia entre entornos y no debe estar en el código. En el legado, rutas y contraseña estaban escritas en el código.
- **POO:** primera **clase**. Clase = molde, instancia = objeto concreto, atributo = dato, **herencia** = `Settings` reutiliza todo lo de `BaseSettings`.
- **Lección real (verificada antes de entregarla):** `Settings(_env_file=None)` funcionaba en pytest pero fallaba en `mypy --strict`. Se usa `monkeypatch.chdir(tmp_path)` para aislar los tests.
- **Error real del usuario:** el atributo `secret_key: SecretStr` (sin valor por defecto) produjo `Field required`, y `PPA_CEN_API_KEY` en `.env` produjo `Extra inputs are not permitted`. Causa común: el **nombre del atributo decide qué variable se lee** (`PPA_` + nombre), y sin `= valor` el campo es **obligatorio**. Se corrigió con `cen_api_key: SecretStr | None = None`. Ahí se vio el *fail fast* en acción.
- **Errores reales en los tests:** (1) `DID NOT RAISE`: se probaba el rechazo con valores **válidos**. (2) El valor por defecto esperado no coincidía con `config.py` (misma lección que `23→C`). (3) mypy rechazó `Settings(log_level=str)`; se prueba por la entrada real, `monkeypatch.setenv`. (4) El test estaba en `tests/domain/`; los tests reflejan la estructura de `src/`.
- 🧠 **Conceptos:** Twelve-Factor, variables de entorno, clase/instancia/atributo/herencia, `SecretStr`, fixture, *test isolation*, dependencia del pipeline vs. de desarrollo. Lección: [05_primera_clase_configuracion.md](aprendizaje/05_primera_clase_configuracion.md).

- **Cierre:** a pedido del usuario, Claude dejó `config.py` y `test_config.py` en su versión final:
  - `env_ignore_empty=True`, para que un valor vacío cuente como "no configurado";
  - 8 tests de configuración;
  - `.env.example` documentado.
  - Total del proyecto: **18 tests en verde**, mypy y ruff limpios.
- **Ajuste técnico:** `ruff format` reformateaba los bloques de código de los `.md`, lo que habría roto el CI. Se excluyeron con `[tool.ruff.format] exclude = ["*.md"]`.
- **Refuerzo:** el usuario todavía no domina cómo se construye una clase ni cómo se escribe un test. Se agregaron:
  - la lección [06](aprendizaje/06_como_se_construyo_config_y_tests.md): `config.py` construido en 7 pasos incrementales, la receta de 4 preguntas para escribir un test y los 6 patrones de test;
  - la carpeta [`practica/`](../practica/README.md) con **5 ejercicios** (función → guarda → Literal → **clase propia** → fixtures) y `SOLUCIONES.md`, verificados: con las soluciones, 23/23 en verde.

### Práctica: avance
- ✅ **Ejercicio 01 (kWh→MWh, RN-10):** implementación y 2 tests propios en verde (4/4).
  - **Lección:** un docstring de test explica **por qué** importa (la regla de negocio), no repite el `assert`.
  - **Lección:** un buen test **falla cuando rompes la regla que protege**. Se comprueba con el experimento de quitar `abs()`.
- ✅ **Ejercicio 02 (validar mes):** cláusula de guarda correcta y test de meses inválidos con valores límite (`0`, `13`, `-1`); 6/6.
  - **Lección:** probar solo los casos válidos deja la guarda **sin protección**: podría borrarse y todo seguiría en verde.
  - **Lección:** `E501` (línea > 100) **bloquea el commit** y `ruff format` no lo arregla solo. Hay que acortar el texto a mano.
  - **Lección:** se borran los comentarios `TODO` ya resueltos.
- ✅ **Ejercicio 03 (tipo de día, RN-16 simple):** guarda + `Literal` + tests; 6/6.
  - **Logro:** el usuario **eligió solo los valores límite correctos** (4 viernes | 5 sábado).
  - **Lección:** el mensaje de error debe incluir el valor que falló (`f"...: {dia_semana}"`).
  - **Lección:** después de la guarda, las condiciones repetidas (`0 <=`) y el `else` tras un `return` son opcionales.
  - **Pendiente (se repite en los 3 ejercicios):** los docstrings describen el patrón en vez de la regla de negocio, y quedan `TODO` resueltos sin borrar.
- ✅ **Ejercicio 04 (primera clase propia):** `ConfigPractica` **correcta al primer intento**, con los atributos documentados. **4/4 tests** después de corregir el concepto.
  - **Lección:** dentro de `pytest.raises`, **no se asigna el resultado** (`config = ...` → F841), porque el objeto nunca se crea. Se llama solo `ConfigPractica()`.
- 🔄 **Ejercicio 05 (archivos + fixture propia):** `leer_horas` correcta, con comprensión de lista y `encoding="utf-8"`; nombres corregidos (`lines` → `lineas`).
  - **Error:** se escribió una función que mezclaba fixture y test (sin `@pytest.fixture`, sin `return`, con `assert`, y sin el prefijo `test_`). pytest la **ignoró en silencio**: `collected 2 items`, todo en verde, pero sin probar nada.
  - **Lección:** una fixture **prepara y entrega** (`@pytest.fixture` + `return`); un test **verifica** (`test_` + `assert`). Hay que mirar **cuántos tests se recolectaron**, no solo si están en verde.
  - **Error de concepto:** con `PRAC_MAX_REINTENTOS="tres"`, el usuario esperaba que pydantic usara el valor por defecto (3) o guardara el texto. En realidad `ConfigPractica()` **lanza `ValidationError` y no crea el objeto** (*fail fast*). El test debe usar `with pytest.raises(ValidationError):`, no un `assert`.
  - **Lección:** usar el valor por defecto en silencio ante un dato inválido es el anti-patrón del legado; fallar al arrancar es lo correcto.
  - **Lección:** `# noqa: F401` se quita cuando el import pasa a usarse.

- ✅ **Práctica completa: 23/23.** Los 5 ejercicios resueltos, incluido tu primera clase propia (ejercicio 04) y tu primera fixture (ejercicio 05).

### Paso 17: Logging estructurado con `run_id` (H2.2) 🔄
- **Qué:** `logging_setup.py` con 4 piezas: `nuevo_run_id()`, `FormateadorJson` (sobrescribe `format`), `FiltroRunId` (con `__init__` y `filter`) y `configurar_logging()`.
- **Por qué:** los logs en JSON con un **correlation ID** permiten rastrear una ejecución completa y consultarla con herramientas de observabilidad. En el legado había `print` y separadores como `"2222…"`.
- **Cómo:** los tests ya vienen escritos (especificación) y el usuario implementa 4 pasos con TDD. El esqueleto se verificó antes con mypy strict, 6/6 tests y ruff.
- 🧠 **POO nueva:** sobrescribir un método, `self`, `__init__`, `super()`. Lección: [07_logging_estructurado.md](aprendizaje/07_logging_estructurado.md).
- **Preguntas de comprobación de la lección 07** (resultado: 1 correcta, 2 parciales, 2 con confusión de concepto). Respuestas modelo en la sección 9 de la lección. Ideas clave corregidas:
  - El `run_id` es único **por ejecución** (no por línea) y responde **qué ejecución**. Cuándo, dónde y gravedad vienen de otros campos.
  - El nivel es un **umbral**: se escribe ese nivel **y los más graves**.
  - `self.run_id` se guarda **en el objeto** (cada instancia tiene el suyo) y **en memoria**, no en la clase ni en un archivo.
  - Sobrescribir = redefinir un **método** del padre; base del **polimorfismo**.

- ✅ **Los 4 pasos implementados por el usuario: 6/6**, 24 tests en el proyecto, mypy ✅. Probado de verdad: JSON válido, tildes legibles, `run_id` presente y `debug` filtrado con nivel INFO.
- **Lección real:** con `logger.exception(...)` **se perdía el detalle del error** (sin `ZeroDivisionError` ni línea), porque ningún test lo exigía. Se corrige con TDD: primero un test con `sys.exc_info()`, luego `if record.exc_info: datos["error"] = self.formatException(...)`, un método **heredado**. **Hábito:** después de ver verde, probar el código real con casos no cubiertos.

- ✅ **Campo `error` agregado con TDD: 7/7.** El usuario **comprobó él mismo que el test protege**: al comentar las 2 líneas no fallaba nada, porque el test aún no estaba en el archivo (`collected 6`); con el test agregado, falla sin el código y pasa con él. El log de error ahora incluye el *traceback* completo.
- **Errores de ruff al cerrar:**
  - `B018` por `1 / 0` suelto (el snippet de Claude estaba mal) → `_ = 1 / 0`.
  - `import sys` agregado por error también en `src/` (`F401`): cada archivo importa solo lo que usa.
  - `I001`: faltaba una línea en blanco entre los grupos de imports.

- ✅ **H2.2 en commit** (`7702dd7`). Los `noqa` y `TODO` de `logging_setup.py` se mantienen por decisión del usuario, pendientes para más adelante.
- **Auditoría de git** (lo que faltaba):
  - commits sin subir (sin respaldo ni CI);
  - `.gitignore` sin `data/` por ubicación ni `logs/`, `*.pbix` y `desktop.ini`;
  - README vacío en un repositorio público;
  - sin licencia.
  - 🧠 **Lecciones:** ignorar **por ubicación**; `!` crea excepciones (`!.env.example`); un repo público **sin LICENSE** = todos los derechos reservados.

### Próximas tareas
- `git push` de los 3 commits; completar el `.gitignore`; README mínimo; decidir la licencia.
- **H2.3:** CLI con `typer` y códigos de salida.
- **H2.3:** CLI con `typer` y códigos de salida.
- **H2.3:** CLI con `typer` y códigos de salida.
- **H2:** configuración (`.env`, `pydantic-settings`, primera **clase**) y observabilidad (logging con `run_id`).

---

## Pendientes registrados

| Pendiente | Cuándo se necesita |
|---|---|
| Registrarse en la API del CEN (clave propia) | H3, ingesta |
| Pedir al CEN acceso a las descargas de Plabacom | H3 |
| Guardar un mes del legado como oráculo | H4 |
| Regla de cruce barra energía ↔ barra CMg | H6 y H7 |
| Política de retención de historia | H9 y H11 |
| Confirmar que la clave CEN del medidor es confiable | H4 |

---

## Anexo A: ¿Qué es un ADR?

**ADR** (*Architecture Decision Record*, registro de decisión de arquitectura) es un documento corto que deja por escrito **una decisión técnica importante, por qué se tomó y qué alternativas se descartaron**.

El código muestra **qué** se hizo, pero nunca **por qué**. Sin un ADR, una decisión que parece "mala práctica" (como unir barras por nombre) podría ser "arreglada" por alguien que no conoce el motivo.

| Parte | Pregunta que responde |
|---|---|
| **Contexto** | ¿Qué situación obligó a decidir? |
| **Decisión** | ¿Qué se eligió? |
| **Alternativas** | ¿Qué otras opciones había y por qué se descartaron? |
| **Consecuencias** | ¿Qué se gana y qué se pierde? |

Solo se escribe un ADR para decisiones **importantes y difíciles de revertir**: arquitectura, herramientas, fuentes o modelo de datos.

**ADR del proyecto hasta ahora:**

| ID | Decisión |
|---|---|
| ADR-001 | Reescribir desde cero; el legado es solo especificación y oráculo |
| ADR-002 | Reglas de negocio cerradas (horario de verano, valor absoluto, `medida_3`, valorización quinceminutal) |
| ADR-003 | Entorno propio con datos públicos |
| ADR-004 | Contratos: fuente Excel de Plataforma Mercado, barras por nombre, formato largo, RUT como clave |
| ADR-005 | Retiros, inyecciones y CMg: valorización en USD, perfil quinceminutal en el reporte, supuestos de CMg |

---

## Anexo B: Mini-quiz H0, respuestas modelo

1. **¿Por qué no basta con borrar una contraseña del código?**
   Porque queda en el historial de git, en los respaldos y en las copias. Se considera comprometida y hay que **rotarla**, y después moverla a variables de entorno o a un *vault*.
2. **¿Aditiva vs. no aditiva?**
   Una medida aditiva se suma a lo largo de todas las dimensiones (energía). Una no aditiva no tiene sentido sumarla (CMg, precios, %). Una semi-aditiva se suma entre entidades pero no en el tiempo (saldos, stock).
3. **¿Qué error hay al valorizar con promedios horarios?**
   Es el **sesgo de agregación**. La diferencia es n·Cov(P,Q): si el consumo sube cuando sube el precio, el método agregado subestima el costo.
4. **¿Qué pasa al sumar la energía de un contrato que aparece en 3 filas?**
   Se **triplica** (doble conteo). Se evita separando las tablas por granularidad o, en DAX, con agregación en dos pasos (`SUMX` + `VALUES`). MAX o AVG no sirven cuando se agregan varios contratos.
5. **¿Para qué sirve un ID como `RN-13`?**
   Para la **trazabilidad de requerimientos**: conecta la regla con el código, el test y el commit, y sigue siendo el mismo aunque el documento se reordene.

---

## Frase de resumen para entrevista

> *"Antes de escribir código diagnostiqué el sistema legado, cerré los riesgos de seguridad, investigué fuentes oficiales, levanté un catálogo trazable de reglas de negocio y diseñé cada dominio a partir de preguntas de negocio. Después preparé un proyecto reproducible con lockfile y estructura de paquetes, y documenté cada decisión como ADR."*
