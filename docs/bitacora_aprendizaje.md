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

## H1: Proyecto Reproducible (en curso)

### Paso 9: Gestor de proyecto y dependencias (H1.1) ✅
- **Qué:** `uv init --package`, que generó `pyproject.toml`, `uv.lock`, `.python-version` y la estructura `src/ppa_pipeline/`.
- **Por qué:** cualquier persona o servidor debe poder reconstruir **exactamente** el mismo entorno con `uv sync`. El legado no tenía archivo de dependencias: si ese computador se perdía, reconstruirlo era a prueba y error.
- **Regla:** se versiona **la receta** (`pyproject.toml`, `uv.lock`), **no el resultado** (`.venv/`, `__pycache__`, datos). El `.venv` además depende de la plataforma (binarios y rutas de Windows).
- **Qué agrega `--package`:**
  1. **Estructura `src/`** (*src layout*): el código solo se puede importar si **está instalado**, no por la carpeta desde donde se ejecuta. El legado fallaba en esto (`import funciones`, `os.getcwd()`).
  2. **Proyecto instalable:** `uv sync` instala tu propio código en el `.venv`.
  3. **Punto de entrada** (*entry point*): `[project.scripts]` crea el comando `ppa-pipeline`.
- 🧠 **Conceptos:** *Packaging*, *Lockfile*, *src layout*, *Entry Point*, *Reproducibility*.

### Próximas tareas
- **H1.2:** estructura de módulos `extract/`, `bronze/`, `silver/`, `domain/`, `quality/`, `load/` (*Separation of Concerns*).
- **H1.3 a H1.6:** `ruff`, `pytest`, `pre-commit` y CI en GitHub.

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
