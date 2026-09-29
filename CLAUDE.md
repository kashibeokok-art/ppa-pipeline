# CLAUDE.md — Modernización Pipeline "Reporte PPA" (Mercado Eléctrico Chileno)

> Este archivo es la **memoria del proyecto** y la **guía de estudio**. Claude lo lee automáticamente al iniciar cada sesión.
> Contiene: reglas de trabajo, contexto, diagnóstico del legado, arquitectura objetivo, **hitos** con los mecanismos
> que se aplican, un glosario para estudiar, backlog, decisiones y bitácora.
> **Regla de oro:** al terminar cada sesión, Claude actualiza §9 (Backlog), §10 (Decisiones) y §11 (Bitácora).

---

## 1. Objetivo

Construir **desde cero (greenfield rewrite)**, **escrito por el usuario y guiado por Claude**, un pipeline de datos nuevo
de nivel profesional que aplique **todo** lo que pide el perfil "Ingeniero/a de Datos — industria Energía" (Michael Page).
Cada cosa construida debe tener **nombre técnico**, para que el usuario pueda estudiarla y defenderla en una entrevista.

### 1.0 Rol de `OLD/` (decisión ADR-001)
**No se reutiliza código de `OLD/`**: ni funciones, ni copiar y pegar, ni "adaptar" scripts. `OLD/` solo sirve como:
1. **Especificación funcional (Functional Spec):** de ahí se extraen las fuentes, las reglas de negocio y las salidas que el negocio necesita. Se documentan en `docs/requerimientos.md` **antes** de programar.
2. **Oráculo de pruebas (Test Oracle):** sus resultados numéricos sirven para verificar que el programa nuevo calcula bien la lógica de negocio.
3. **Catálogo de anti-patrones:** §5 lista lo que **no** se debe repetir.

El diseño nuevo (nombres, estructura, tablas, modelo) parte del requerimiento, no del código antiguo.

### 1.1 Matriz de trazabilidad: oferta laboral → hitos

| Requisito de la oferta | Hitos donde se aplica |
|---|---|
| Desarrollar y mantener procesos **ETL/ELT** | H3, H4, H5, H8 |
| Arquitectura **Medallion** (capas Silver y Gold) | H3 (Bronze), H4–H5 (Silver), H8 (Gold) |
| **Automatizar** captura, procesamiento y **validación** | H3, H6, H9 |
| Consolidar y **estandarizar** datos corporativos | H4, H7 |
| **Microsoft Fabric** y **OneLake** | H12 (y diseño portable desde H3) |
| Controles de **calidad**, **trazabilidad** y **gobierno** | H0, H2, H6, H11 |
| Facilitar acceso, análisis y **visualización** | H8, H10 |
| **Documentar** procesos, flujos y **diccionarios** de datos | H11 (y un poco en cada hito) |
| Transformar requerimientos de negocio en soluciones | H0 (contrato con consumidor), H10 |
| **SQL** | H8 (fuerte), H6, H10 |
| **Python** para procesamiento de datos | H1–H7 |
| Arquitecturas y plataformas de datos | §6, H8, H12 |
| Inglés técnico (lectura de documentación) | Cada hito tiene "📖 Leer (EN)" |
| Deseable: Power BI | H10 |
| Deseable: calidad y gobierno | H6, H7, H11 |
| Deseable: negocio energético/regulado | Todo el proyecto (datos del CEN, SII) |
| Deseable: Databricks | H12 (Delta Lake y Spark se transfieren directo) |

---

## 2. Reglas de trabajo para Claude (modo mentor, NO modo "hazlo tú")

> **El usuario escribe el código. Claude guía, explica, revisa y corrige.** El objetivo es que el usuario
> pueda defender cada línea en una entrevista técnica. El proyecto debe ser *suyo*.

### 2.1 Reparto de roles

| Claude hace | El usuario hace |
|---|---|
| Explicar el concepto y la buena práctica antes de cada tarea | Escribir el código de la tarea |
| Mostrar el problema en el código de `OLD/` (con `archivo:línea`) | Decidir entre las alternativas (con la recomendación de Claude) |
| Dar el enunciado de la tarea: objetivo, criterios de aceptación y pistas | Ejecutar, probar y mostrar el resultado |
| Dar **esqueletos** (firmas de funciones, estructura, TODOs), no soluciones completas | Completar la implementación |
| Revisar el código del usuario como en un *code review* real (qué está bien, qué mejorar, por qué) | Aplicar las correcciones |
| Configuración repetitiva (`pyproject`, `.gitignore`, CI) **solo si el usuario lo pide** y explicando cada línea | — |
| Actualizar §9, §10 y §11 al cerrar la sesión | Validar lo que se registra |

**Excepciones:** si el usuario dice "muéstrame la solución" o "hazlo tú", Claude lo hace, pero explica línea por línea.
Si el usuario se traba, Claude escala la ayuda de a poco: **pista → pista más concreta → fragmento → solución**.

### 2.2 Cómo enseñar (formato fijo de cada tarea)

```
🎯 Tarea Hx.y — <nombre>
🧠 Concepto: <mecanismo con su nombre técnico> — qué es, por qué importa, qué rompe en OLD/ no tenerlo
🔍 En el legado: <archivo:línea> y qué hace mal
🛠️ Tu turno: <enunciado + esqueleto/pistas>
✅ Criterios de aceptación: <cómo sabemos que está bien>
🎤 Cómo decirlo en entrevista: <1–2 frases>
📖 Leer (EN): <documentación oficial breve>
```

- **Idioma:** español. Los términos técnicos van en inglés entre paréntesis la primera vez: *idempotencia (idempotency)*.
- Hacer **preguntas de verificación** ("¿qué pasa si este paso falla a la mitad?") antes de dar respuestas.
- Al cerrar un hito: **mini-quiz** de 3–5 preguntas sobre sus mecanismos.
- Al cerrar cada hito (o paso relevante): actualizar **`docs/bitacora_aprendizaje.md`** (notas de estudio del usuario: qué se hizo, por qué y cómo se llama, más las respuestas modelo del quiz).
- Cuando el usuario pida explicar código línea por línea: guardarlo en **`docs/aprendizaje/NN_tema.md`** y agregarlo al índice `docs/aprendizaje/README.md`.
- **SIEMPRE, al cerrar cada paso, sin esperar a que el usuario lo pida:** actualizar `docs/aprendizaje/` (lección nueva `NN_tema.md` + índice), `docs/bitacora_aprendizaje.md` y `docs/Ejecutables/`.
- **Cada comando que Claude le entregue al usuario** debe agregarse también a **`docs/Ejecutables/`**, en el archivo de su herramienta (01_uv, 02_git, 03_ruff, 04_pytest, 05_pre-commit, 06_powershell; crear `NN_herramienta.md` nuevo si no existe y sumarlo al `README.md` de esa carpeta). Formato: título corto + bloque ```powershell + una línea de explicación.
- **Perfil del usuario:** fuerte en el dominio del negocio eléctrico; en formación en Python. **Aún no conoce POO**: enseñarla paso a paso cuando aparezca (H2 pydantic-settings, H3 clientes de API, H6 pandera) y no usar clases donde bastan funciones.

### 2.3 Reglas técnicas
1. **Por partes.** Una tarea por vez. Cada parte termina funcionando y probada.
2. **Greenfield.** Nunca copiar ni importar código de `OLD/`. Claude puede citar `OLD/` para explicar *qué* regla de negocio existe o *qué* error evitar, pero la implementación nace del requerimiento documentado.
3. **Validación contra el oráculo.** Cuando una regla de negocio esté implementada, se compara el resultado con el de `OLD/`. Si difiere, se investiga: o es un bug nuevo, o es un bug del legado que se corrigió. En ambos casos se registra en §10.
4. **No tocar `OLD/`.** Es la referencia de solo lectura.
5. **Nunca escribir credenciales** en código, en este archivo ni en commits.
6. **Operaciones destructivas en SQL** (DROP, TRUNCATE, DELETE masivo) → confirmar con el usuario antes.
7. **Convivencia con producción:** el sistema nuevo escribe en **esquemas nuevos** (`stg`, `gold`, `ops`), nunca en las tablas `dbo.*` del legado, hasta el corte oficial (*cutover*).
8. Al final de cada sesión: actualizar §9, §10, §11 y proponer la siguiente tarea.

---

## 3. Dominio de negocio (glosario del negocio)

| Término | Significado |
|---|---|
| **CEN / Coordinador** | Coordinador Eléctrico Nacional. Publica balances de energía del sistema. |
| **Plabacom** | Plataforma de balances del CEN (plabacom.coordinador.cl). Fuente de los ZIP mensuales. |
| **Retiro** | Energía que sale del sistema hacia un cliente en una barra. Tipos: **R** (regulado), **L** (libre en transmisión, `LeT`), **LD** (libre en distribución, `LeD`). |
| **Inyección** | Energía que una central entrega al sistema. Archivos `nortetrans`, `nortedist`, `surtrans`, `surdist`, `compraventas`. Tipos `G`, `C_FIN`, `C_FIS`, `L`, `L_D`, `R`. |
| **Barra** | Nodo eléctrico donde se mide inyección/retiro. Se homologa contra subestaciones (API Infotécnica). |
| **CMg** | Costo Marginal [USD/MWh] por barra y hora. Se usa para valorizar energía. |
| **Bloques horarios** | A: horas 1–8 y 24 · B: 9–18 · C: 19–23 (`funciones.calcular_perfil_por_bloque`). |
| **Día hábil / no hábil** | Lunes a viernes no feriado vs. fin de semana/feriado (Chile, librería `holidays`). |
| **Suministrador** | Empresa generadora que vende energía a un cliente bajo contrato. |
| **PPA** | *Power Purchase Agreement*, contrato de compra de energía. |
| **RUT** | Identificador tributario chileno. Se usa para homologar nombres de empresas (base SII). |

---

## 4. Inventario del sistema legado (`OLD/`)

### 4.1 Scripts y flujo actual

```
main_diario.py ─────────► Contratos (API Plataforma Mercado CEN → Excel → Parquet → SQL: Contratos)

main_mensual.py
  ├─ por cada mes faltante:
  │   ├─ Selenium → Plabacom → link ZIP → descarga
  │   ├─ procesar_ZIP (extrae, renombra, ZIPs internos, copia útiles)
  │   ├─ ACCESS (.mdb → Parquet retiros R / LeT / LeD vía pyodbc)
  │   ├─ Dia_mensual_representativo (perfiles horarios, bloques, hábil/no hábil)
  │   ├─ subir_sql → EstadisticasRetirosV2, RetiroBloques, RetiroHistoricoMensual
  │   └─ subprocess → main_mensual_iny.py
  │         ├─ CMg + inyecciones + retiros → valorización → Fin_iny*.parquet
  │         ├─ subir_iny_a_sql → BalanceGenerador
  │         └─ Procesar_barras (fuzzy match) → MaestroSubestaciones
  ├─ subprocess → Hom_Retiros.py (homologación empresas ↔ RUT: SII + scraping buscadores)
  └─ finally: borra descargas + DELETE en SQL de meses fuera de ventana (36 / 24 meses)

Auxiliares/manuales: Homologar_barras.py, Hom_barras.py, Homologar_Retiro.py, Actualizar_Suministradores.py,
Diccionario_generadores.py (→ DiccionarioSuministradores), iny.py, revisarColumnas.py,
separar_retiros_L_LD_x_Cliente.py, Modificar_cache.py
```

### 4.2 Fuentes de datos

| Fuente | Método actual | Frecuencia | Formato |
|---|---|---|---|
| Plataforma Mercado CEN (contratos) | `requests` a API Gateway AWS | Diaria | Excel |
| Plabacom CEN (balances) | **Selenium** + descarga ZIP | Mensual | ZIP → `.mdb` Access + CSV |
| CMg | dentro del ZIP de Plabacom | Mensual | CSV `cmgAAMM.csv` |
| API Infotécnica CEN | `requests` REST | Ad-hoc | JSON |
| SII nómina personas jurídicas | descarga ZIP | Ad-hoc | TXT |
| Buscadores (Google/Bing/…) | scraping con user-agents rotativos | Ad-hoc | HTML |
| Diccionario suministradores | Excel manual | Manual | XLSX |

### 4.2.1 Fuentes vía API del CEN (investigado 2026-09-27)

Portal: `https://portal.api.coordinador.cl` (Red Hat 3scale). Autenticación con `user_key` **propia**; se obtiene al registrarse y suscribirse al plan gratuito "Consulta de Datos" de cada unidad de negocio. Las APIs tienen **paginación** (`page`/`limit`) y **rate limit** (headers `X-Rate-Limit`).

| Necesidad | ¿Hay API oficial documentada? | Endpoint | Reemplaza a |
|---|---|---|---|
| CMg real por barra y hora | ✅ Sí | SIP `GET /costo-marginal-real/v4/findByDate` (`startDate`, `endDate`, `bar_transf`) | `cmgAAMM.csv` del ZIP |
| Contratos de suministro | ✅ Sí (validar cobertura vs. Excel) | SIP `GET /api/v2/recursos/contratos_de_suministro_vigentes/` | Excel de Plataforma Mercado |
| Barras / subestaciones | ✅ Sí | Planificación `GET /activos/barras/v2`, `/activos/secciones/v2/barras` | API Infotécnica v1 del legado |
| Retiros por barra/cliente/hora (`.mdb`) | ❌ No en APIs públicas | — | — |
| Inyecciones por central/hora (`nortetrans`…) | ❌ No en APIs públicas | — | — |
| Descargas de Plabacom (ZIP del balance) | ⚠️ API **interna no documentada** | `https://plabacom.api.coordinador.cl/bff/api/presigned-urls?tipo=Energia&clasificacion=…&version=…&ultima=…` → lista de **URLs prefirmadas de S3** | Selenium |

- Sin clave, el endpoint de Plabacom responde `403 Authentication parameters missing`. El frontend usa una clave incrustada en su JS: **no se usa**, porque no es nuestra. Hay que pedir acceso propio a la mesa de ayuda del CEN (`soporte.sip@coordinador.cl`).
- La API "Medidas" (`/medidas-v2/measurement`) entrega medidas por punto de medida del **propio coordinado**. No reemplaza el balance de mercado completo.
- `transferencia-economica-nacional/zonal` son **peajes de transmisión** (VATT, IT). No son energía retirada ni inyectada.

### 4.3 Tablas SQL destino (Azure SQL, BD `dw_ppa`, schema `dbo`)

`Contratos`, `EstadisticasRetirosV2`, `RetiroBloques`, `RetiroHistoricoMensual`, `BalanceGenerador`,
`MaestroSubestaciones`, `EmpresaSubdivision`, `DiccionarioSuministradores`.
Consumidas por: `Reporte PPA V2.pbix`, `Reporte Balance generadores.pbix`.

---

## 5. Diagnóstico del legado = anti-patrones a NO repetir

> Como el proyecto es greenfield, esta sección no es una lista de cosas que arreglar en `OLD/`. Es la lista de
> **anti-patrones** que el diseño nuevo debe evitar desde el primer día. Los bugs de lógica de negocio (§5.2)
> sirven además para no heredar errores al leer `OLD/` como especificación.

Severidad: 🔴 crítico · 🟠 alto · 🟡 medio · 🔵 estilo/mantenibilidad. Entre corchetes, el hito donde se diseña la solución correcta.

### 5.1 Seguridad
- 🔴 **Credenciales de Azure SQL escritas en el código** (`funciones.py:1540-1544`, `Diccionario_generadores.py:9-13`). Hay que **rotar la contraseña**. Cualquier copia en OneDrive, correo o git sigue expuesta. [H0]
- 🟠 Scraping de Google/Bing/Yahoo con user-agents rotativos (`Hom_Retiros.py`, `Homologar_Retiro.py`): es frágil, viola los términos de servicio y no se puede auditar. [H7]

### 5.2 Bugs confirmados o probables
- 🔴 **Reintentos sin `break`** (`main_mensual.py:249-288`): cada paso exitoso se ejecuta 3 veces. Si falla, el error se registra y el pipeline **sigue** con datos incompletos. [H3, H9]
- 🔴 **Carga no atómica** (`funciones.subir_carpeta_a_sql`): `to_sql(append)` archivo por archivo, sin transacción. Si falla a la mitad, el mes queda cargado a medias y la verificación "¿existe (Anio, Mes)?" lo **salta para siempre**. [H8]
- 🟠 `logging.warninr` en **dos lugares** (`funciones.py:1601` y `:2034`): el error de tipeo lanza `AttributeError`. [H1.7: lo detecta **mypy solo con `--check-untyped-defs` o `strict`**. Por defecto mypy **no revisa funciones sin anotaciones** y no lo ve. ruff tampoco. Verificado 2026-09-27]
- 🟠 `subir_barras_a_sql` está **definida dos veces** en `funciones.py` (líneas 2081 y 2321). La segunda pisa a la primera. [Verificado 2026-09-27: **ni ruff F811 ni mypy (`--check-untyped-defs`) lo marcaron**. Lección: ninguna herramienta atrapa todo; la revisión de código humana sigue siendo necesaria]
- 🔴 `Homologar_Retiro.py` llama 42 veces a `safe_prent`, que no existe (F821): el script se cae con `NameError`. Detectado por ruff (2026-09-27).
- Ruff sobre `OLD/` (2026-09-27): 64 errores `F` (45 F821, 15 F401, 3 F841, 1 F811) y 246 de `E/B/UP/PD/I` (183 E501, 14 I001, 11 B007, 9 PD015, 8 B905, 3 PD002, 1 B006, 2 B008…).
- 🟠 En `main_mensual_iny.py:195` el `try` está a nivel de módulo, fuera del `if __name__`, y `subir_iny_a_sql` corre aunque el procesamiento haya fallado. [H9]
- 🟡 Feriados: `df['ParsedDate'].isin(holidays.CL(...))` funciona en pandas 2.3.3 pero está **deprecado** (`FutureWarning`). En una versión futura todos los feriados pasarán a contarse como hábiles **sin lanzar error** (verificado 2026-09-27). [H4]
- 🟡 `pivot_table` usa métricas float como **índice** (`funciones.py:1486`): frágil y puede duplicar filas. [H4]
- 🟡 `completar_horas_faltantes` rellena con `0.0`: un dato faltante queda igual a un consumo real cero y sesga los promedios. [H4, H6]

### 5.3 Arquitectura / ingeniería de datos
- 🟠 **No existe capa Bronze.** El `finally` borra las descargas crudas: no se puede reprocesar ni auditar. [H3]
- 🟠 **Retención destructiva:** se hace `DELETE` de los meses fuera de la ventana de 36/24 meses y se pierde historia. [H9, H11]
- 🟠 La orquestación se hace con `subprocess` entre scripts, sin dependencias explícitas, `run_id` ni reanudación. [H2, H9]
- 🟠 **Idempotencia débil:** append más verificación de existencia, en vez de *staging* + `MERGE`. [H8]
- 🟠 Dependencia de Windows: driver ODBC de Access y rutas `C:\Users\...`. [H2, H3]
- 🟡 Hechos "pre-pivoteados" (`PROMEDIO_DiaHabil`/`PROMEDIO_DiaNoHabil`) y sin modelo estrella. [H8, H10]
- 🟡 Columnas con espacios y tildes (`Hora Mensual`, `Categoría Día`) y tablas versionadas por nombre (`...V2`). [H4, H8]

### 5.4 Código
- 🔵 `funciones.py` es un *god module*: unas 2.400 líneas, 39 imports y dominios mezclados. [H1]
- 🔵 Código duplicado: `Hom_barras` vs. `Homologar_barras`, `Hom_Retiros` vs. `Homologar_Retiro`, `ACTUALIZAR_SII` ×2, `obtener_engine_sql` ×2. [H1, H7]
- 🔵 Mezcla de `print` y `logging`, excepciones genéricas tragadas. [H2]
- 🔵 No hay tests, *type hints*, archivo de dependencias, git, README ni linter. [H0, H1]
- 🔵 Rutas personales hardcodeadas. `rutas_config` crea carpetas al importarse (efecto secundario). [H2]

---

## 6. Arquitectura objetivo

### 6.1 Medallion

```
 FUENTES                 BRONZE (raw, inmutable)      SILVER (limpio, conformado)       GOLD (modelo de negocio)        CONSUMO
 ─────────               ──────────────────────       ───────────────────────────       ────────────────────────        ───────
 Plabacom ZIP  ─┐        data/bronze/<fuente>/        data/silver/<entidad>/            SQL: esquema gold                Power BI
 API Contratos ─┤ ingest   ingest_date=YYYY-MM-DD/     periodo=YYYYMM/*.parquet          fct_retiro_horario               (modelo
 API Infotécn. ─┤ ─────►   archivo original + meta   ─► tipos, snake_case,          ─►  fct_inyeccion_valorizada   ─►   semántico
 SII           ─┤          (hash, url, run_id)         dedupe, homologación,            fct_contrato_energia             estrella)
 Excel manual  ─┘                                      checks de calidad               dim_fecha, dim_hora, dim_barra,
                                                                                         dim_empresa, dim_bloque, ...
                                          ▲ cuarentena: data/quarantine/ (filas que fallan checks)
                                          ▲ auditoría:  ops.pipeline_run, ops.load_log, ops.dq_result
```

### 6.2 Principios no negociables
1. **Idempotencia**: reejecutar el mismo periodo da el mismo resultado, sin duplicados.
2. **Atomicidad**: el periodo se carga completo o no se carga.
3. **Trazabilidad / linaje**: cada fila en Gold se rastrea a un `run_id` y a un archivo Bronze.
4. **Fail fast / fail loud**: un error detiene el pipeline con código de salida ≠ 0.
5. **Configuración externa**: secretos en variables de entorno o Key Vault, nunca en el código.
6. **Funciones puras** en las transformaciones (DataFrame entra → DataFrame sale, sin I/O).
7. **Contratos de datos**: el esquema esperado se valida en cada frontera de capa.

### 6.3 Stack propuesto (se confirma en §10)

| Área | Herramienta |
|---|---|
| Entorno/deps | `uv` + `pyproject.toml` |
| Calidad de código | `ruff`, `mypy`, `pre-commit` |
| Tests | `pytest` |
| DataFrames | `pandas` 2.x + `pyarrow` (evaluar `polars`) |
| Validación | `pandera` |
| Config | `pydantic-settings` |
| Reintentos HTTP | `tenacity` |
| SQL | Azure SQL: esquemas `stg`, `gold`, `ops` + migraciones versionadas; opcional **dbt** |
| Orquestación | CLI (`typer`) → Task Scheduler / GitHub Actions → Fabric Data Pipeline |
| CI | GitHub Actions |
| BI | Power BI (`.pbip` versionado en git) |
| Nube | Microsoft Fabric (Lakehouse + Delta + Direct Lake) |

### 6.4 Estructura de repo objetivo

```
GM ACTUALIZACION/
├─ CLAUDE.md  README.md  pyproject.toml  uv.lock  .env.example  .gitignore  .pre-commit-config.yaml
├─ OLD/                       ← legado, solo lectura (fuera de git mientras tenga secretos)
├─ src/ppa_pipeline/
│  ├─ config.py  logging_setup.py  cli.py
│  ├─ extract/   bronze/   silver/   quality/   load/   domain/
├─ sql/  migrations/  gold/  ops/
├─ tests/  unit/  integration/  fixtures/oracle/
├─ docs/  arquitectura.md  diccionario_datos.md  linaje.md  runbook.md  adr/
├─ powerbi/                   ← .pbip
├─ fabric/                    ← notebooks y definiciones (H12)
└─ data/                      ← local, ignorado: bronze/ silver/ quarantine/
```

---

## 7. Hitos del proyecto

**Ciclo de cada tarea:** Entender → Diagnosticar → Diseñar → Implementar (usuario) → Probar → Revisar (Claude) → Documentar → Registrar.
**Definition of Done (DoD) de cada hito:** pasa `ruff` + `pytest` · sin secretos · logging con `run_id` · reejecutable · documentado · mini-quiz aprobado · bitácora actualizada.

Las fases H0–H2 son prerequisito. Luego se recomienda avanzar **por dominio de punta a punta** (retiros H3→H4→H6→H8→H10), y después sumar inyecciones y contratos. Esto se llama entregar un **vertical slice** (corte vertical).

---

### 🏁 H0 — "Cimientos Seguros y Requerimientos"
**Oferta:** transformar requerimientos de negocio en soluciones, gobierno de datos, documentación.
**Mecanismos que aprendes:**
- **Gestión de secretos (Secrets Management)** y **rotación de credenciales (Credential Rotation)**
- **Principio de mínimo privilegio (Least Privilege)**: usuario SQL solo con los permisos necesarios
- **Levantamiento de requerimientos (Requirements Gathering)** e **ingeniería inversa (Reverse Engineering)** del legado
- **Requerimientos funcionales vs. no funcionales (Functional / Non-Functional Requirements)**: qué calcula vs. cada cuánto, cuán rápido, cuán confiable
- **Catálogo de reglas de negocio (Business Rules Catalog)**
- **Inventario de fuentes (Source System Inventory)**
- **Contrato con el consumidor (Consumer Contract)**: qué necesitan los reportes Power BI
- **Oráculo de pruebas (Test Oracle)** y **Golden Dataset**: resultados del legado congelados para comparar
- **Control de versiones (Version Control)** con Git y **.gitignore**
**Tú construyes:** repo git nuevo · `.gitignore` · `docs/requerimientos.md` (fuentes, reglas de negocio numeradas `RN-01…`, salidas, frecuencias, requerimientos no funcionales) · `docs/consumidores.md` · `tests/fixtures/oracle/` (un mes de salidas del legado).
**Aceptación:** contraseña rotada · `git status` sin secretos · cada regla de negocio escrita en lenguaje de negocio (sin código), con su fuente en `OLD/` como referencia.
**Entrevista:** *"Antes de escribir código hice ingeniería inversa del sistema legado para levantar las reglas de negocio y los requerimientos. Eso me dio una especificación y un oráculo de pruebas para construir la versión nueva desde cero."*
**📖** GitHub Docs "Removing sensitive data from a repository"; Wikipedia "Test oracle".

### 🏁 H1 — "Proyecto Reproducible"
**Oferta:** Python orientado a datos, mantenibilidad.
**Mecanismos:** **Empaquetado (Packaging)** con `pyproject.toml` y **src layout** · **Gestión de dependencias** con **lockfile** (`uv`) · **Linting** y **Formatting** (`ruff`) · **Tipado estático (Static Typing)** con `mypy` · **Pre-commit hooks** · **Integración Continua (CI)** con GitHub Actions · **Separación de responsabilidades (Separation of Concerns)**: romper el *god module* · **Conventional Commits** · **Feature branches**.
**Tú construyes:** esqueleto `src/ppa_pipeline/` · `pyproject.toml` · CI que corre lint + tests · primer test "hola mundo".
**Aceptación:** `uv sync && uv run pytest` funciona en una carpeta limpia · CI en verde · ruff detecta `warninr` y la función duplicada del legado.
**Entrevista:** *"Estandaricé el proyecto con packaging moderno, lockfile, linters y CI, para que cualquiera lo reproduzca y cada cambio se valide automáticamente."*
**📖** Python Packaging User Guide; docs de Ruff.

### 🏁 H2 — "Configuración y Observabilidad"
**Oferta:** trazabilidad, automatización.
**Mecanismos:** **Twelve-Factor App (config)** · **Validación de configuración** con `pydantic-settings` · **Variables de entorno** y `.env.example` · **Logging estructurado (Structured Logging, JSON)** · **Correlation ID / `run_id`** · **Niveles de log** · **Códigos de salida (Exit Codes)** · **Fail Fast** · **Inyección de dependencias** simple (pasar config en vez de variables globales).
**Tú construyes:** `config.py` · `logging_setup.py` · CLI con `typer`: `ppa --help`.
**Aceptación:** sin rutas absolutas en el código · cada línea de log trae `run_id` · un error termina con exit code 1.
**Entrevista:** *"Externalicé la configuración según 12-factor y agregué logging estructurado con correlation ID, así cualquier ejecución se puede rastrear de punta a punta."*
**📖** 12factor.net (III. Config, XI. Logs).

### 🏁 H3 — "Ingesta Automatizada → Capa Bronze"
**Oferta:** ETL/ELT, Medallion, automatizar la captura, integración de fuentes.
**Mecanismos:** **Patrón Conector/Extractor (Connector Pattern)**, uno por fuente · **Landing Zone** · **Capa Bronze inmutable (Immutable Raw Layer)** · **Metadatos de ingesta / columnas de linaje** (`_run_id`, `_source`, `_ingested_at`) · **Manifiesto** y **Checksum SHA-256** (detectar archivos repetidos o cambiados) · **Reintentos con backoff exponencial (Exponential Backoff)** con `tenacity` · **Descarga idempotente** · **Extracción incremental** con **Watermark** (último periodo cargado) · **Backfill** (recargar historia) · **Particionamiento estilo Hive** (`periodo=YYYYMM/`) · **API-first vs. scraping** (eliminar Selenium si existe un endpoint) · **Formato columnar Parquet**.
**Tú construyes:** `extract/plabacom.py`, `extract/contratos.py` · `bronze/landing.py` con manifiesto · lectura portable de `.mdb`.
**Aceptación:** correr dos veces el mismo mes no duplica nada · se puede borrar Silver y reconstruirlo desde Bronze · un fallo de red reintenta y luego falla fuerte.
**Entrevista:** *"Implementé ingesta incremental con watermarks hacia una capa Bronze inmutable, con checksums y metadatos de linaje, lo que permite reprocesar y auditar contra la fuente."*
**📖** Databricks "What is the medallion lakehouse architecture?"; docs de `tenacity`.

### 🏁 H4 — "Silver: Retiros Conformados"
**Oferta:** ETL, capa Silver, estandarizar datos.
**Mecanismos:** **Schema Enforcement** (tipos explícitos) · **Convención de nombres (Naming Convention)** `snake_case` · **Normalización de unidades** (kWh→MWh) · **Definición de granularidad (Grain)**: 1 fila = barra × retiro × hora · **Formato largo / Tidy Data** (no pivotear en Silver) · **Funciones puras** · **Densificación / relleno de brechas (Gap Filling)** con marca de imputación · **Lógica de calendario** (hábil/no hábil, feriados) · **Tests unitarios** (`pytest`) · **Test de paridad** contra el golden dataset · **Deduplicación**.
**Tú construyes:** `silver/retiros.py` · `domain/calendario.py` · `domain/bloques.py` · tests.
**Aceptación:** paridad numérica con `OLD/` (tolerancia definida) · bug de feriados resuelto sin deprecación · horas imputadas marcadas (`es_imputado`).
**Entrevista:** *"En Silver definí una granularidad explícita y transformaciones puras testeadas unitariamente, validando los resultados contra un oráculo de pruebas obtenido del sistema legado."*
**📖** Hadley Wickham, "Tidy Data" (paper).

### 🏁 H5 — "Silver: CMg, Inyecciones y Valorización"
**Oferta:** integración de fuentes, ETL.
**Mecanismos:** **Joins con alineación de granularidad** (evitar *fan-out*, la multiplicación de filas) · **Enriquecimiento (Enrichment)** · **Capa de reglas de negocio (Business Rules Layer)** en `domain/` · **Datos de referencia (Reference Data)** · **Vectorización** (no usar `apply` fila por fila) · **Tests parametrizados** · **Chequeo de cardinalidad del join** (`validate="many_to_one"`).
**Tú construyes:** `silver/cmg.py`, `silver/inyecciones.py`, `domain/valorizacion.py`.
**Aceptación:** filas antes = filas después del join (sin fan-out) · paridad de `Valorizado[USD]` con el legado.
**Entrevista:** *"Integré costos marginales con inyecciones controlando la cardinalidad de los joins para evitar duplicación silenciosa."*
**📖** pandas docs "merge — validate parameter".

### 🏁 H6 — "Calidad de Datos (Data Quality)"
**Oferta:** controles de calidad, validación automatizada.
**Mecanismos:** **Contratos de datos (Data Contracts)** con `pandera` · **Dimensiones de calidad**: completitud (*completeness*), unicidad (*uniqueness*), validez (*validity*), consistencia (*consistency*), oportunidad (*timeliness*), exactitud (*accuracy*) · **Cuarentena / Dead-Letter** · **Umbral de tolerancia / Circuit Breaker** (si más del X% falla, se detiene) · **Reconciliación (Reconciliation)**: sumas de control Bronze = Silver = Gold · **Tabla de resultados DQ** (`ops.dq_result`) · **Data Observability** (volumen, frescura, esquema).
**Tú construyes:** `quality/schemas.py` · `quality/checks.py` · reconciliación de energía total por mes.
**Aceptación:** un archivo corrupto de prueba termina en cuarentena y no llega a Gold · los resultados DQ quedan en SQL.
**Entrevista:** *"Implementé contratos de datos y reconciliación entre capas; los registros inválidos se aíslan en cuarentena y las métricas de calidad quedan auditadas."*
**📖** pandera docs; DAMA-DMBOK (capítulo Data Quality, resumen).

### 🏁 H7 — "Datos Maestros y Homologación"
**Oferta:** consolidar y estandarizar datos corporativos, gobierno.
**Mecanismos:** **Master Data Management (MDM)** · **Resolución de entidades (Entity Resolution)** · **Fuzzy Matching** con **umbral de confianza** · **Human-in-the-loop** (cola de revisión manual) · **Tabla de equivalencias (Crosswalk / Mapping Table)** · **Clave natural vs. clave sustituta (Natural Key vs. Surrogate Key)** · **Slowly Changing Dimension tipo 2 (SCD2)** · **Golden Record** · Uso de **fuente autoritativa** (SII, API Infotécnica) en vez de scraping.
**Tú construyes:** `dim_empresa` y `dim_barra` con claves sustitutas · crosswalk versionado · reporte de "pendientes de revisión".
**Aceptación:** sin scraping de buscadores · cada match guarda su score y su método (exacto/fuzzy/manual) · el historial de cambios se conserva (SCD2).
**Entrevista:** *"Construí dimensiones maestras con resolución de entidades contra fuentes autoritativas, matching difuso con umbral y revisión humana, e historial SCD tipo 2."*
**📖** Kimball Group "Slowly Changing Dimension Techniques".

### 🏁 H8 — "Gold: Data Warehouse en SQL"
**Oferta:** SQL, capa Gold, ELT, facilitar el análisis.
**Mecanismos:** **Modelado dimensional (Kimball)** · **Esquema estrella (Star Schema)** · **Tablas de hechos y dimensiones** · **Granularidad declarada** · **Dimensiones conformadas (Conformed Dimensions)** · **Staging Tables** · **Upsert con `MERGE`** · **Reemplazo de partición transaccional** (DELETE+INSERT en una transacción) · **Transacciones ACID** · **Migraciones versionadas (Schema Migrations)** · **Índices columnstore** · **Vistas como capa semántica** · **Stored Procedures** · **Tabla de auditoría de cargas** (`ops.load_log`) · opcional **dbt**: modelos, tests, docs y linaje automático.
**Tú construyes:** `sql/migrations/V001__schemas.sql`… · `fct_retiro_horario`, `dim_fecha`, `dim_hora`, `dim_bloque`, `dim_barra`, `dim_empresa` · `load/sql_loader.py`.
**Aceptación:** matar el proceso a mitad de la carga no deja datos parciales · recargar un mes no duplica · el DDL vive en git.
**Entrevista:** *"Diseñé un modelo estrella en SQL con cargas idempotentes vía staging y MERGE transaccional, con migraciones versionadas y auditoría de cada carga."*
**📖** Microsoft Learn "MERGE (Transact-SQL)"; Kimball "The Data Warehouse Toolkit" (cap. 1–3).

### 🏁 H9 — "Orquestación y Operación"
**Oferta:** automatización, mantener procesos.
**Mecanismos:** **DAG (Directed Acyclic Graph)** de tareas · **Dependencias entre tareas** · **Orquestador** · **Reanudación / Checkpointing** · **Reejecución idempotente (Rerun)** · **Programación (Scheduling / cron)** · **SLA** · **Alertas** · **Tabla de ejecuciones** (`ops.pipeline_run`) · **Runbook** (qué hacer cuando falla) · **Política de retención (Data Lifecycle / Retention Policy)**.
**Tú construyes:** `ppa run --period 2026-08 --steps all` · reanudar desde el paso fallido · tarea programada · runbook.
**Aceptación:** un fallo detiene los pasos dependientes · queda registrado · se retoma sin repetir lo que ya se hizo.
**Entrevista:** *"Orquesté el pipeline como un DAG con reanudación, auditoría de ejecuciones y alertas, reemplazando scripts encadenados por subprocess."*
**📖** Conceptos de Apache Airflow (DAGs, tasks, idempotency) aunque no uses Airflow.

### 🏁 H10 — "Power BI: Modelo Semántico"
**Oferta:** visualización, acceso a la información, negocio.
**Mecanismos:** **Modelo semántico (Semantic Model)** · **Esquema estrella en Power BI** · **Tabla de fechas marcada (Date Table)** · **Medidas DAX vs. columnas calculadas** · **Contexto de filtro (Filter Context)** · **Relaciones 1:* y dirección de filtro** · **Query Folding** · **Actualización incremental (Incremental Refresh)** · **Row-Level Security (RLS)** · **Formato PBIP + Git** · **Direct Lake** (en H12).
**Tú construyes:** reporte nuevo sobre Gold · catálogo de medidas documentado · RLS de ejemplo.
**Aceptación:** sin columnas pre-pivoteadas · medidas en DAX · el `.pbip` versionado en git.
**Entrevista:** *"Construí el modelo semántico sobre un esquema estrella, con medidas DAX reutilizables, actualización incremental y seguridad a nivel de fila."*
**📖** Microsoft Learn "Understand star schema and the importance for Power BI".

### 🏁 H11 — "Documentación y Gobierno"
**Oferta:** documentar procesos, flujos y diccionarios; gobierno y trazabilidad.
**Mecanismos:** **Diccionario de datos (Data Dictionary)** · **Linaje de datos (Data Lineage)** · **Catálogo de datos (Data Catalog; ej. Microsoft Purview)** · **ADR (Architecture Decision Records)** · **README** y **Runbook** · **Data Owner / Data Steward** · **Clasificación de sensibilidad** (RUT, nombres de empresas) · **Política de retención** documentada · **Diagramas C4 / de flujo**.
**Tú construyes:** `docs/diccionario_datos.md` (tabla, columna, tipo, definición, fuente, regla) · diagrama de linaje · README de portafolio.
**Aceptación:** alguien nuevo entiende y ejecuta el proyecto solo con el README.
**Entrevista:** *"Documenté diccionario, linaje y decisiones de arquitectura, y definí dueños y políticas de retención como parte del gobierno de datos."*
**📖** Microsoft Purview "Data lineage" overview.

### 🏁 H12 — "Migración a Microsoft Fabric / OneLake"
**Oferta:** Microsoft Fabric, OneLake (y Databricks, que es transferible).
**Mecanismos:** **Lakehouse** · **OneLake** (un único data lake lógico) · **Delta Lake** (ACID sobre Parquet, **Time Travel**) · **Shortcuts** · **Notebooks** (PySpark/Python) · **Data Pipelines** · **Fabric Warehouse** · **Medallion en Fabric** (un lakehouse por capa o un esquema por capa) · **Direct Lake** · **Deployment Pipelines** (Dev/Test/Prod) · **Integración Git de Fabric** · **V-Order**.
**Tú construyes:** (con la prueba gratuita de Fabric, si está disponible) Bronze/Silver como tablas Delta · Gold en Warehouse o Lakehouse · reporte en Direct Lake.
**Aceptación:** el mismo código de `silver/` corre en un notebook de Fabric con cambios mínimos.
**Entrevista:** *"Diseñé el pipeline portable y lo desplegué en Microsoft Fabric con arquitectura medallion sobre OneLake y Delta, consumido por Power BI en modo Direct Lake."*
**📖** Microsoft Learn "Implement medallion lakehouse architecture in Microsoft Fabric".

---

## 8. Catálogo de mecanismos (glosario para estudiar)

> Claude marca `✅` cuando el mecanismo ya se aplicó en el proyecto, junto al hito donde se aplicó.

| Mecanismo (EN) | En una línea | Hito | Aplicado |
|---|---|---|---|
| ACID | Atomicidad, Consistencia, Aislamiento, Durabilidad de transacciones | H8, H12 | |
| ADR | Documento corto que registra una decisión técnica y su porqué | H11 | |
| Backfill | Recargar periodos históricos con el pipeline actual | H3 | |
| Baseline / Golden Dataset | Salida de referencia congelada para comparar versiones | H0 | |
| Bronze / Silver / Gold | Capas raw / limpia-conformada / modelo de negocio | H3–H8 | |
| Checksum | Huella (hash) de un archivo para detectar cambios o duplicados | H3 | |
| CI (Continuous Integration) | Validación automática (lint, tests) en cada cambio | H1 | |
| Circuit Breaker | Detener el proceso si los errores superan un umbral | H6 | |
| Conformed Dimension | Dimensión compartida por varios hechos con el mismo significado | H8 | |
| Correlation ID (`run_id`) | Identificador que une todos los logs y datos de una ejecución | H2 | |
| Data Contract | Esquema y reglas acordadas que un dataset debe cumplir | H6 | |
| Data Lineage | Rastro de origen → transformaciones → destino de un dato | H3, H11 | |
| DAG | Grafo de tareas con dependencias y sin ciclos | H9 | |
| Dead-Letter / Quarantine | Lugar donde van los registros inválidos sin detener todo | H6 | |
| Delta Lake | Formato de tabla sobre Parquet con ACID y time travel | H12 | |
| Direct Lake | Modo de Power BI que lee Delta de OneLake sin importar datos | H12 | |
| ELT vs ETL | Transformar después de cargar (en el motor) vs. antes | H3, H8 | |
| Entity Resolution | Determinar qué registros son la misma entidad real | H7 | |
| Exponential Backoff | Reintentos con esperas crecientes (1s, 2s, 4s…) | H3 | |
| Fail Fast | Fallar temprano y visible en vez de seguir con datos malos | H2 | |
| Fan-out (join) | Multiplicación indeseada de filas en un join | H5 | |
| Grain | Qué representa exactamente una fila de una tabla | H4, H8 | |
| Additive / Non-Additive Measures | Energía se suma; precios (CMg) se promedian; saldos son semi-aditivos | H0, H8 | ✅ |
| Aggregation Bias | Error al agregar antes de calcular; se calcula en el grano más fino (P×Q quinceminutal) | H0, H5 | ✅ |
| Natural Key / Composite Key | Clave de negocio de un registro; a menudo compuesta por varias columnas | H4, H8 | |
| Requirements Traceability | Vincular regla (RN-xx) ↔ código ↔ test ↔ commit | H0 | ✅ |
| Accepted Risk | Riesgo conocido que se decide asumir y queda documentado | H0 | ✅ |
| Question-Driven Design / Data Minimization | Seleccionar solo las columnas que responden preguntas de negocio | H0 | ✅ |
| Join Key vs. Descriptive Attribute | Unir por IDs estables; los nombres solo se muestran | H0, H7 | |
| Untrusted Source Key | Si la fuente no garantiza su clave, se construye una propia (normalizar + clave sustituta) | H0, H7 | ✅ |
| Long Format | Una fila por combinación (contrato × barra) en vez de listas dentro de una celda | H0, H4 | ✅ |
| Double Counting | Una medida repetida en varias filas por mezclar granularidades se suma de más | H8, H10 | |
| Requirements Consistency Check | Cada regla sirve a una pregunta y cada pregunta tiene sus reglas | H0 | ✅ |
| YAGNI | *You Aren't Gonna Need It*: no construir lo que nadie pidió | H0 | ✅ |
| Static Analysis / Linting | Revisar el código sin ejecutarlo (ruff: F = errores lógicos, E = estilo PEP 8, I = imports, B = bugs sutiles, UP = sintaxis moderna, PD = pandas) | H1 | ✅ |
| Defense in Depth | Varias herramientas complementarias: ruff (sintaxis/patrones), mypy (tipos/atributos), pytest (lógica) | H1 | |
| Mutable Default Argument | Un `[]`/`{}` por defecto se comparte entre llamadas (B006) | H1 | ✅ |
| TDD (Red → Green → Refactor) | Escribir el test antes que el código; el test es especificación ejecutable | H1 | ✅ |
| Boundary Value Testing | Probar los bordes (7|8, 17|18, 22|23), donde nacen los bugs | H1 | ✅ |
| Guard Clause | Validar la entrada al inicio de la función y fallar con un mensaje claro | H1 | ✅ |
| Line Ending Normalization | `.gitattributes` con `eol=lf` para repos multiplataforma | H1 | ✅ |
| Vectorization | Operar sobre columnas completas (`.map` con lookup) en vez de fila por fila (`.apply`) | H4 | |
| Conformed Dimension | Dimensión compartida (empresa, fecha, bloque) que permite cruzar dominios | H0, H8 | ✅ (diseño) |
| Silent Nulls | Un cruce que falla sin error y deja valores nulos (ej. retiro sin CMg) | H6 | |
| Documented Assumption | Supuesto explícito y vigente hasta que alguien lo corrija | H0 | ✅ |
| Multivalued Attribute / Bridge Table | Relación 1:N o N:M resuelta con una tabla intermedia | H8 | |
| Data Classification / PII | Clasificar datos (público, interno, personal) y proteger los personales | H0, H11 | |
| API Gateway / API Key | Puerta de entrada que autentica, limita y mide el uso de una API | H3 | |
| Rate Limiting | Límite de llamadas por período que impone una API | H3 | |
| Pagination | Recibir resultados grandes en páginas (`page`/`limit`, `offset`) | H3 | |
| Presigned URL (S3) | URL temporal y firmada para descargar un archivo privado sin credenciales | H3 | |
| Undocumented / Internal API | API que usa un frontend pero no está publicada para terceros; puede cambiar sin aviso | H3 | |
| Source Discovery | Investigar qué fuentes y métodos de acceso oficiales existen antes de construir | H0 | ✅ |
| Greenfield Rewrite | Construir un sistema nuevo desde cero en vez de modificar el existente | ADR-001 | ✅ |
| Functional / Non-Functional Req. | Qué debe hacer el sistema vs. con qué calidad (tiempo, confiabilidad) | H0 | |
| Business Rules Catalog | Lista numerada de reglas de negocio en lenguaje no técnico | H0 | |
| Reverse Engineering | Deducir requerimientos leyendo un sistema existente | H0 | |
| Test Oracle | Fuente de verdad para decidir si un resultado es correcto | H0, H4 | |
| Cutover | Momento en que el sistema nuevo reemplaza al antiguo en producción | H9 | |
| Strangler Fig | Reemplazar un legado por partes (alternativa descartada en ADR-001) | ADR-001 | |
| Idempotency | Ejecutar N veces produce el mismo resultado que una vez | H3, H8, H9 | |
| Incremental Load / Watermark | Procesar solo lo nuevo, recordando el último punto cargado | H3 | |
| Incremental Refresh | Power BI refresca solo particiones recientes | H10 | |
| Least Privilege | Dar solo los permisos mínimos necesarios | H0 | |
| Lockfile | Archivo que fija versiones exactas de dependencias | H1 | |
| MDM | Gestión de datos maestros (empresas, barras) como fuente única | H7 | |
| MERGE / Upsert | Insertar o actualizar según exista la clave | H8 | |
| Partitioning (Hive-style) | Organizar archivos por `clave=valor/` para leer solo lo necesario | H3 | |
| Pure Function | Función sin efectos secundarios: misma entrada → misma salida | H4 | |
| Query Folding | Power Query delega la transformación al motor de origen | H10 | |
| Reconciliation | Verificar que los totales cuadren entre capas | H6 | |
| Regression Test | Test que asegura que un cambio no rompió lo que funcionaba | H0, H4 | |
| RLS | Seguridad a nivel de fila en Power BI | H10 | |
| Runbook | Guía operativa: cómo correr, monitorear y recuperarse de fallos | H9 | |
| SCD Type 2 | Dimensión que guarda historial con vigencia desde/hasta | H7 | |
| Schema Enforcement | Rechazar datos que no cumplen el esquema declarado | H4, H6 | |
| Schema Migration | Cambios de DDL versionados y aplicados en orden | H8 | |
| Secrets Management | Guardar credenciales fuera del código (env, Key Vault) | H0, H2 | |
| Semantic Model | Capa de negocio (relaciones, medidas) sobre los datos | H10 | |
| Staging Table | Tabla temporal donde se carga antes de consolidar | H8 | |
| Star Schema | Hechos al centro, dimensiones alrededor | H8, H10 | |
| Structured Logging | Logs en formato máquina (JSON) con campos consultables | H2 | |
| Surrogate Key | Clave técnica sin significado de negocio (entero autoincremental) | H7, H8 | |
| Tidy Data | Cada variable es una columna, cada observación una fila | H4 | |
| Twelve-Factor App | Principios de apps portables (config en el entorno, etc.) | H2 | |
| Vertical Slice | Entregar un dominio completo de punta a punta antes de ampliar | §7 | |

---

## 9. Backlog (estado actual)

Leyenda: `[ ]` pendiente · `[~]` en curso · `[x]` hecho

- [x] **H0 — Cimientos Seguros y Requerimientos** (cerrado 2026-09-27; mini-quiz aprobado 3/5 + 2 parciales. A reforzar en H8/H10: definición formal de medidas aditivas/semi-aditivas, y sobre-conteo resuelto por grano/SUMX en vez de MAX/AVG. H0.6 diferido: la clave API se necesita en H3 y el oráculo en H4)
  - [x] ~~Rotar la contraseña SQL~~ → **No aplica** (el usuario confirma que la credencial está obsoleta y no se porta al proyecto nuevo)
  - [x] Entorno decidido: **A, solo entorno propio** (ADR-003)
  - [~] H0.5 Contrato con el consumidor, un documento por dominio (preguntas → columnas):
    - [x] `docs/contratos.md` cerrado (ver ADR-004)
    - [x] `docs/retiros.md`, `docs/inyecciones.md`, `docs/cmg.md` cerrados (ver ADR-005)
  - [ ] `git init` + `.gitignore` (excluir `OLD/`, `data/`, `.env`)
  - [x] `git init` en la raíz del proyecto + `.gitignore` (OLD/ y Archivos/ ignorados, verificado con `git check-ignore`)
  - [x] `docs/requerimientos.md`: 19 reglas de negocio (cerrado por el usuario 2026-09-27; nivel de detalle elegido por el usuario, que conoce el dominio)
  - [ ] Pendientes opcionales de git: rama `main`, `.env.example`, completar `.gitignore` (data/, caches, *.pbix, logs), salir de OneDrive
  - [ ] `docs/consumidores.md`: qué preguntas de negocio responden los `.pbix`
  - [ ] Congelar el oráculo: un mes de salidas del legado → `tests/fixtures/oracle/`
  - [ ] Registrarse en portal.api.coordinador.cl y suscribirse a "Consulta de Datos" (SIP, Planificación) → `user_key` propia en `.env`
  - [ ] Pedir a la mesa de ayuda del CEN acceso por API a las descargas de Plabacom (`/bff/api/presigned-urls`) o una alternativa oficial
- [x] **H1 — Proyecto Reproducible** (cerrado 2026-09-28; CI ✅ en 3c0d0b3 con ruff + mypy strict + pytest; mini-quiz aprobado: 2 correctas + 3 parciales. **Reforzar:** el concepto de CI (el usuario no lo tenía claro aunque lo configuró) y derivar los casos de test desde la regla escrita)
  - [x] H1.1 Instalar `uv` + `uv init --package` → `pyproject.toml`, `src/`, `.python-version`
  - [x] H1.2 Estructura de paquetes `src/ppa_pipeline/{extract,bronze,silver,quality,load,domain}`
  - [x] H1.3 `ruff` (lint + format) configurado en `pyproject.toml` (pendiente menor: reemplazar los comentarios TODO de I/B/PD)
  - [x] H1.4 `pytest` + primer test: RN-01 `domain/bloques.py` con TDD (entrada = hora de inicio 0–23). 9 tests en verde. El usuario detectó y corrigió un caso de negocio mal escrito en el test (23→A). Nota H4: vectorizar con un dict de 24 horas + `.map()`, no `.apply()`
  - Extras hechos: `.gitattributes` (LF), `known-first-party = ["ppa_pipeline"]` en isort
  - [x] H1.5 `pre-commit` (commit b276aa3). Pendiente menor: agregar `default_stages: [pre-commit]` para que los hooks no corran también en commit-msg
  - [x] H1.6 Repositorio **público** en GitHub: https://github.com/kashibeokok-art/ppa-pipeline. CI ✅ (run 36370506292, commit 40a39e7; los 7 pasos en success). El primer intento quedó en una ruta duplicada y no corrió; se corrigió con `git mv`
  - [x] Pendientes menores resueltos en 3c0d0b3: `default_stages: [pre-commit]` y `.gitignore` limpio
  - [x] H1.7 `mypy` en modo `strict` sobre `src` y `tests`, como hook **local** de pre-commit (`uv run mypy`, no mirrors-mypy, porque el entorno aislado no ve las dependencias del proyecto) + paso en el CI ✅. Tests anotados con `bloque_esperado: Bloque`. Incidencias resueltas: `uv not found` (VS Code con PATH viejo → reiniciar) y `Bloque.A` (Literal ≠ Enum)
  - Carpeta `docs/Ejecutables/` (versionada por decisión del usuario; el `Ejecutables.md` antiguo fue borrado)
- [~] **H2 — Configuración y Observabilidad**
  - [x] H2.1 (cerrado 2026-09-28; **código final escrito por Claude a pedido del usuario**, sin commit todavía; 18 tests ✅, mypy ✅, ruff ✅; se agregó `env_ignore_empty=True` y `[tool.ruff.format] exclude=["*.md"]`, porque ruff formateaba los bloques de los .md y rompía el CI). **El usuario pidió explicación y práctica:** lección 06 + carpeta `practica/` (5 ejercicios + SOLUCIONES.md, verificados 23/23 con las soluciones; el CI no los corre porque `testpaths = ["tests"]`). **Próxima sesión:** revisar los ejercicios del usuario ANTES de H2.2. Detalle original: `config.py`: clase `Settings(BaseSettings)` con `env_prefix="PPA_"`, `.env`, atributos `data_dir: Path`, `log_level: NivelLog`, `cen_api_key: SecretStr | None`; `.env.example`; `tests/test_config.py` con una fixture autouse (`monkeypatch.chdir(tmp_path)` + `delenv`). Esqueleto verificado en el scratchpad: mypy strict ✅, pytest 5/5 ✅, ruff ✅. ⚠️ NO usar `Settings(_env_file=None)`: mypy strict lo rechaza (call-arg). Primera clase del usuario → explicar POO desde cero (lección 05)
  - [x] Práctica `practica/`: los 5 ejercicios hechos por el usuario (23/23). Errores superados: DID NOT RAISE, fail fast vs. valor por defecto, F841 dentro de pytest.raises, fixture sin decorador ignorada en silencio. **Pendientes sin responder:** el experimento de quitar `abs()` (ej. 01) y qué pasa con `abc` en `leer_horas` (ej. 05)
  - Quiz de la lección 07 (antes de implementar): el usuario confundía atributo de instancia vs. de clase, creía que se guardaba "en el archivo", y creía que el run_id indica cuándo/dónde/gravedad. **Reforzar POO (instancia vs. clase, self) al revisar su FiltroRunId.**
  - [~] H2.2 **Los 4 pasos implementados por el usuario, 6/6 ✅.** Pendiente: el test + campo `error` (`record.exc_info` → `self.formatException`); la prueba real con `1/0` mostró que se perdía el traceback. También quitar `# noqa: F401` y los TODO, y hacer commit/push. Detalle original: Logging estructurado con `run_id`. Claude creó `tests/test_logging_setup.py` (6 tests, la especificación) y el esqueleto `src/ppa_pipeline/logging_setup.py` con 4 TODO (paso 1 `nuevo_run_id`, paso 2 `FormateadorJson.format`, paso 3 `FiltroRunId.__init__/filter`, paso 4 `configurar_logging`). La implementación de referencia se verificó en el scratchpad (mypy strict ✅, 6/6 ✅). Los imports llevan `# noqa: F401` para que el `ruff --fix` de pre-commit no los borre; hay que quitarlos al terminar. ⚠️ No hacer push hasta 6/6: el CI fallaría. En los tests se usa `registro.__dict__["run_id"]` porque `getattr(x, "const")` dispara B009
  - [ ] H2.3 CLI `typer` + códigos de salida
- [ ] H3 — Ingesta Automatizada → Bronze
- [ ] H4 — Silver: Retiros Conformados
- [ ] H5 — Silver: CMg, Inyecciones y Valorización
- [ ] H6 — Calidad de Datos
- [ ] H7 — Datos Maestros y Homologación
- [ ] H8 — Gold: Data Warehouse en SQL
- [ ] H9 — Orquestación y Operación
- [ ] H10 — Power BI: Modelo Semántico
- [ ] H11 — Documentación y Gobierno
- [ ] H12 — Migración a Microsoft Fabric / OneLake

---

## 10. Registro de decisiones (ADR resumido)

Formato: `ADR-NNN · fecha · decisión · alternativas · motivo`

- **ADR-001 · 2026-09-27 · Reescritura desde cero (greenfield).** Alternativas: refactor incremental (*Strangler Fig*), reutilizar módulos. Motivo: el legado tiene un *god module*, credenciales expuestas, sin tests ni capas. El usuario quiere aprender construyendo el diseño completo. `OLD/` queda como especificación y oráculo de pruebas.
- **ADR-002 · 2026-09-27 · Reglas de negocio cerradas (`docs/requerimientos.md`).** Decisiones clave del usuario:
  - DST: la hora extra de abril va al bloque A; la hora faltante de septiembre no se considera.
  - Energía en **valor absoluto** (igual que el legado).
  - Medición oficial: `medida_3`.
  - Valorización P×Q **quinceminutal** y luego suma horaria. CMg horario = promedio. Energía horaria = suma.
  - Contratos: solo vigentes, energía máxima anual en GWh, se excluyen años aislados, sin dato = 0.
  - Se guardan los datos quinceminutales procesados en Parquet (Silver) y el reporte es horario (Gold).
  - **Riesgos aceptados:** horas sin medición = 0 (RN-04) sesga el mínimo y el promedio de RN-18; contratos sin energía = 0.
  - **Notas para H4:** RN-19 define la clave natural; la clave real es compuesta (año, mes, cuarto de hora, barra, punto/empresa). No programar abril/septiembre a mano: usar la zona `America/Santiago`. RN-16: la librería `holidays` solo incluye feriados nacionales.
  - Las reglas del documento están numeradas `1..19` → se referencian como RN-01..RN-19.
- **ADR-003 · 2026-09-27 · Entorno propio (opción A).** Alternativas: servidor de la empresa (B), híbrido (C). Motivo: proyecto de portafolio, independiente de la empresa. Consecuencias:
  - Solo **datos públicos** del CEN, sin datos ni tablas corporativas.
  - Servidor SQL propio (SQL Server Developer local o Azure SQL gratuito; se decide en H8).
  - El repositorio puede ser **público** en GitHub.
  - El servidor `dw_ppa` y las tablas `dbo.*` del legado no se usan. §4.3 queda solo como referencia de diseño.
  - La credencial antigua no se porta (H0.1 no aplica).
  - Datos no públicos del legado (p. ej. el Excel `diccionario_suministradores`) deben reemplazarse por fuentes públicas o por datos propios de referencia.
- **ADR-004 · 2026-09-27 · Dominio contratos.** Decisiones:
  - **Fuente:** Excel de Plataforma Mercado (público).
  - **Barras por NOMBRE**, no por ID: el usuario indica que los ID de barra de la fuente no están certificados (*untrusted source key*). En H7 el nombre se normaliza y se genera una clave sustituta propia.
  - **Varias barras por contrato:** una fila por barra con el mismo ID de contrato (formato largo). ⚠️ Energía y potencia son del contrato: en H8 se separa `fct/dim contrato` (una fila por contrato) de `contrato_barra` (puente) para evitar doble conteo.
  - La energía es **contratada**, no consumida. La comparación contratado vs. real con retiros es una pregunta de negocio aceptada.
  - El RUT es la clave natural de empresa.
- **ADR-005 · 2026-09-27 · Dominios retiros, inyecciones y CMg (H0.5 cerrado).**
  - **Decisiones:**
    - Se valoriza en USD (se mantienen RN-13 y RN-14).
    - El perfil quinceminutal **llega al reporte** (Gold con grano de 15 min, además del horario).
    - Los bloques A/B/C y el mes/año son ejes comunes de los 4 dominios.
  - **Supuestos** (vigentes mientras el usuario no los corrija):
    - CMg desde la API SIP `costo-marginal-real/v4`, versión vigente más reciente, en USD/MWh.
    - La clave CEN del medidor identifica al cliente (retiros) y a la central/suministrador (inyecciones).
    - Se conserva toda la historia.
  - **Abiertos:**
    - Regla de cruce barra energía ↔ barra CMg (resolver en H7 con la normalización de nombres; control DQ en H6: 100% de filas de energía con CMg).
    - Confiabilidad de la clave del medidor (verificar en H4).
    - Política de retención.
  - **Notas H8:**
    - `dim_empresa` conformada (RUT), compartida por los dominios, para calcular el balance del suministrador.
    - Evaluar un solo `fct_energia` con tipo inyección/retiro.
    - Volumen: el grano de 15 min multiplica ×4 las filas (evaluar columnstore / incremental refresh).
- _(siguiente: confirmar el stack de §6.3 al iniciar H1)_

---

## 11. Bitácora de sesiones

### 2026-09-27 — Sesión 1: Diagnóstico y plan
- Se revisó `OLD/` completo (17 scripts, unas 4.000 líneas).
- Se creó este `CLAUDE.md`: modo mentor (el usuario programa y Claude guía), diagnóstico (§5), arquitectura (§6), 13 hitos con mecanismos nombrados y trazados a la oferta laboral (§7), y catálogo de estudio (§8).
- Hallazgos principales: credenciales en el código, reintentos sin `break`, carga SQL no atómica, sin capa Bronze, `DELETE` de historia, *god module*.
- Se verificó que la detección de feriados funciona con pandas 2.3.3, pero está deprecada.
- **Decisión ADR-001:** proyecto greenfield. No se reutiliza código de `OLD/`, que queda como especificación y oráculo.
- **Source Discovery (§4.2.1):** hay APIs oficiales del CEN para CMg real, contratos y barras. Retiros e inyecciones solo están en los ZIP de Plabacom. Se encontró una API interna de descargas (URLs prefirmadas de S3) que elimina Selenium, pero requiere una clave propia que hay que pedir al CEN.
- Git iniciado en la raíz; `.gitignore` en la raíz (OLD/ ignorado, verificado).
- `docs/requerimientos.md` cerrado con 19 reglas (ver ADR-002).
- H0.1 no aplica (credencial obsoleta). Entorno: opción A, propio y con datos públicos (ADR-003).
- **Próximo paso:** H0.5 (contrato con el consumidor: qué usan los .pbix) y H0.6 (clave de la API del CEN + oráculo).
