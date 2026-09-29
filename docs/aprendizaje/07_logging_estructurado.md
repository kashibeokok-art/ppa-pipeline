# 07 · Logging estructurado con `run_id`

> **Hito:** H2.2 · **Archivos:** `src/ppa_pipeline/logging_setup.py`, `tests/test_logging_setup.py`
> **Conceptos:** logging vs. `print`, niveles de log, logger / handler / formatter / filter, **logging estructurado (JSON)**, **Correlation ID (`run_id`)**; POO: **sobrescribir un método**, `__init__`, `self`, `super()`.

---

## 1. El problema: `print` y logs sueltos

En el legado se mezclaban `print(...)` y `logging.info(...)`:
- [Diccionario_generadores.py:8](../../OLD/Diccionario_generadores.py) usa `print`.
- [main_mensual.py:15](../../OLD/main_mensual.py) registra `"222222222222222222222222"` como separador.

Problemas:
1. **`print` no tiene nivel**: no se puede distinguir un error de un mensaje informativo, ni silenciar los mensajes menos importantes.
2. **Texto libre**: para buscar "todos los errores del mes de agosto" hay que leer a mano.
3. **Sin identificador de ejecución**: si el pipeline corre dos veces el mismo día, sus mensajes se mezclan y no se sabe cuál es cuál.

---

## 2. Conceptos

### 2.1 Niveles de log
| Nivel | Cuándo usarlo | Ejemplo |
|---|---|---|
| `DEBUG` | Detalle para depurar | "Leídas 2.976 filas del archivo X" |
| `INFO` | Hitos normales del proceso | "Inicio de carga de retiros 2026-08" |
| `WARNING` | Algo raro, pero se puede seguir | "3 barras sin CMg asociado" |
| `ERROR` | Algo falló | "No se pudo descargar el ZIP de Plabacom" |

Con el **nivel configurado** (tu `PPA_LOG_LEVEL`) decides desde qué nivel se escribe. Con `WARNING`, los `INFO` y `DEBUG` no aparecen.

### 2.2 Logging estructurado (*Structured Logging*)
En vez de texto libre, **cada línea es un JSON** con campos fijos:
```json
{"momento": "2026-09-28T14:03:11+00:00", "nivel": "INFO", "logger": "ppa.retiros", "mensaje": "Inicio de carga", "run_id": "3f9a1c0b7e2d"}
```
Así una **máquina** puede leerlo: filtrar por nivel, por `run_id`, contar errores, graficar. Es lo que usan Azure Monitor, Datadog, Elastic y el *Monitoring Hub* de Fabric.

### 2.3 Correlation ID (`run_id`)
Un identificador **único por ejecución**, presente en **todas** las líneas de log de esa ejecución (y, en H3, en los datos que carga).
- Pregunta de negocio: *"¿por qué el reporte de agosto tiene números raros?"*
- Respuesta: buscas el `run_id` de la carga de agosto y ves **toda su historia**, de principio a fin.

---

## 3. Las 4 piezas del módulo `logging` de Python

```
logger.info("Inicio de carga")
        │
        ▼
   ┌─────────┐   crea un LogRecord (el "registro": mensaje, nivel, hora, nombre…)
   │ LOGGER  │
   └────┬────┘
        ▼
   ┌─────────┐   decide DÓNDE se escribe (consola, archivo…)
   │ HANDLER │──► FILTER:    ¿lo dejo pasar?  + le agrego el run_id     (tu FiltroRunId)
   └────┬────┘──► FORMATTER: ¿cómo se ve?     → lo convierto en JSON   (tu FormateadorJson)
        ▼
   {"nivel": "INFO", "mensaje": "Inicio de carga", "run_id": "3f9a…"}
```

| Pieza | Qué hace | En tu código |
|---|---|---|
| **Logger** | Recibe los mensajes (`logger.info(...)`) | `logging.getLogger(...)` |
| **Handler** | Decide a dónde van (consola, archivo) | `logging.StreamHandler()` |
| **Filter** | Deja pasar o no, y puede **agregar datos** al registro | `FiltroRunId` |
| **Formatter** | Decide **cómo se ve** el texto final | `FormateadorJson` |

**Logger raíz:** `logging.getLogger()` sin nombre devuelve el logger "padre" de todos. Si lo configuras a él, todos los loggers del proyecto heredan esa configuración.

---

## 4. POO nueva en esta lección

### 4.1 Sobrescribir un método (*method overriding*)
```python
class FormateadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ...
```
- `logging.Formatter` ya tiene un método `format()` que devuelve texto plano.
- Al escribir **tu propio** `format()` en la clase hija, **reemplazas** ese comportamiento. El resto de `Formatter` se sigue heredando.
- `logging` llama a `format()` sin saber que es tuyo: **tú cambias el "cómo", el sistema sigue igual.** Es una de las ideas más poderosas de la POO.

Un **método** es una función que pertenece a una clase y se define **dentro** de ella.

### 4.2 `self`: "este objeto"
```python
class FiltroRunId(logging.Filter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id          # guardo el dato EN el objeto

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self.run_id   # lo leo DESDE el objeto
        return True
```
- **`self`** es el objeto concreto sobre el que se ejecuta el método. Python lo pasa solo: escribes `filtro.filter(registro)` y Python llama `filter(self=filtro, record=registro)`.
- `self.run_id = run_id` guarda un **atributo** en el objeto, para que otros métodos lo usen después.

### 4.3 `__init__`: el constructor
- Es el método que se ejecuta **al crear** el objeto: `FiltroRunId("abc123")` llama `__init__(self, "abc123")`.
- Ahí se **guardan los datos iniciales** del objeto.
- En `Settings` (lección 05) no lo escribiste porque `BaseSettings` ya trae uno. Aquí sí, porque el filtro necesita recordar un `run_id`.

### 4.4 `super()`: llamar a la clase padre
```python
        super().__init__()
```
Antes de agregar lo tuyo, dejas que la clase padre (`logging.Filter`) haga su propia preparación. Si lo olvidas, el objeto queda **a medio construir**.

---

## 5. Cómo trabajar la tarea (TDD con tests ya escritos)

Esta vez los tests **ya están escritos**: son la especificación. Tu trabajo es implementar los 4 pasos hasta ponerlos en verde, **de a uno**:

| Paso | Qué implementas | Test que se pone verde |
|---|---|---|
| 1 | `nuevo_run_id()` | `test_run_id_*` (2) |
| 2 | `FormateadorJson.format()` | `test_formateador_produce_json_con_los_campos` |
| 3 | `FiltroRunId.__init__` y `.filter()` | `test_filtro_agrega_run_id_al_registro` |
| 4 | `configurar_logging()` | `test_configurar_logging_*`, `test_nivel_*` (2) |

Para ejecutar **solo** los tests de un paso:
```powershell
uv run pytest tests/test_logging_setup.py -k run_id -v
```
`-k run_id` ejecuta solo los tests cuyo nombre contiene "run_id".

**Cómo lee el test la salida:** `capsys` es una fixture de pytest que **captura** lo que se escribe en la consola. `StreamHandler` escribe por defecto en `stderr` (la salida de errores), por eso el test lee `capsys.readouterr().err`.

---

## 5.1 Lección real: se perdía el detalle del error

Con los 6 tests en verde, una prueba real con un error mostró esto:
```python
try:
    1 / 0
except ZeroDivisionError:
    logging.getLogger("ppa").exception("fallo")
```
```json
{"nivel": "ERROR", "mensaje": "fallo", "run_id": "r1"}
```
**No aparecía `ZeroDivisionError`, ni el archivo, ni la línea.** En producción, un log de error sin su causa no sirve.

**Causa:** ningún test lo exigía. **Lo que no tiene test no está protegido.**

**Solución con TDD:**
1. 🔴 Un test nuevo que crea un registro con `sys.exc_info()` y exige `"ZeroDivisionError" in datos["error"]`.
2. 🟢 En `format`, antes del `return`:
   ```python
   if record.exc_info:
       datos["error"] = self.formatException(record.exc_info)
   ```
   - `record.exc_info` guarda el error cuando se usa `logger.exception(...)`; si no hubo error, está vacío.
   - `self.formatException(...)` es un método **heredado** de `logging.Formatter`: lo usas sin escribirlo. Es la herencia en acción.

**Resultado:**
```json
{"nivel": "ERROR", "mensaje": "fallo", "run_id": "r1",
 "error": "Traceback (most recent call last):\n  File ..., line 3 ...\nZeroDivisionError: division by zero"}
```

**Cómo se comprobó que el test protege de verdad:** con las 2 líneas nuevas comentadas, el test falla (`KeyError: 'error'`); sin comentar, pasa. Es el mismo experimento de quitar `abs()` en la práctica.

⚠️ **Detalle de ruff en el test:** `1 / 0` sola en una línea dispara `B018` ("expresión inútil"). Cuando se provoca un error a propósito, se asigna a `_`: `_ = 1 / 0`. **`_` es la convención de Python para "variable que no voy a usar".**

### Las 3 piezas explicadas

| Pieza | Qué es | Cómo se lee |
|---|---|---|
| `record.exc_info` | Atributo del registro. `None` en un log normal; con los datos del error si se usó `logger.exception(...)` | `if record.exc_info:` = "si el registro trae un error…" (`None` cuenta como falso) |
| `self.formatException(...)` | Método **heredado** de `logging.Formatter`: convierte el error en el texto del *traceback* | "yo, este formateador, uso el método que heredé" |
| `datos["error"] = ...` | Agregar una clave nueva a un diccionario | `persona = {"nombre": "Ana"}` → `persona["edad"] = 30` → `{"nombre": "Ana", "edad": 30}` |

**Dónde va:** entre el diccionario y el `return`. Si se pone **después** del `return`, nunca se ejecuta, porque `return` termina la función (*código inalcanzable*, *unreachable code*).

```python
        datos = { ... }                                              # 1. armar
        if record.exc_info:                                          # 2. agregar el error si hay
            datos["error"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False)                 # 3. convertir a JSON
```

🧠 **Hábito:** después de poner los tests en verde, **prueba el código de verdad** con casos que los tests no cubren (errores, datos raros). Si algo sale mal, primero escribe el test que lo demuestra y después corrígelo.

## 6. Para la entrevista

> *"Implementé logging estructurado en JSON con un correlation ID por ejecución. Un filtro inyecta el run_id en cada registro y un formatter propio serializa a JSON, así los logs se pueden consultar en cualquier plataforma de observabilidad y rastrear una ejecución de punta a punta."*

---

## 7. Glosario

| Término | Definición |
|---|---|
| Nivel de log | Importancia de un mensaje: DEBUG < INFO < WARNING < ERROR |
| Structured Logging | Logs como datos (JSON) con campos fijos, no texto libre |
| Correlation ID / `run_id` | Identificador único que une todos los logs (y datos) de una ejecución |
| Logger / Handler / Filter / Formatter | Recibe / dirige / filtra-enriquece / da formato |
| Logger raíz | El logger padre de todos; se configura una vez |
| `LogRecord` | El objeto con los datos de un mensaje de log |
| Método | Función definida dentro de una clase |
| Sobrescribir (*override*) | Redefinir en la clase hija un método de la clase padre |
| `self` | El objeto concreto sobre el que se ejecuta un método |
| `__init__` | Constructor: se ejecuta al crear el objeto |
| `super()` | Acceso a la clase padre (por ejemplo, para su `__init__`) |
| `capsys` | Fixture de pytest que captura la salida de consola |

---

## 8. Preguntas de comprobación

1. ¿Qué ventaja tiene un log en JSON frente a un `print`?
2. Si configuras `PPA_LOG_LEVEL=WARNING`, ¿se escribe un `logger.info(...)`? ¿Y un `logger.error(...)`?
3. ¿Qué hace `self.run_id = run_id` y por qué el método `filter` puede leerlo después?
4. ¿Qué significa que `FormateadorJson` **sobrescribe** `format`?
5. ¿Para qué sirve el `run_id` cuando algo sale mal en producción?

---

## 9. Respuestas modelo (y los errores de concepto más comunes)

**1. JSON vs. `print`**
`print` no tiene nivel, no se puede silenciar y es texto libre. Un log JSON tiene campos fijos (`momento`, `nivel`, `logger`, `mensaje`, `run_id`), así que se puede **filtrar, contar y cruzar** automáticamente con herramientas como Azure Monitor o Fabric.
⚠️ Confusión común: "un id único por línea". El `run_id` es único **por ejecución** y lo **comparten** todas las líneas de esa ejecución. Por eso sirve para agruparlas.

**2. Nivel = umbral mínimo**
```
DEBUG  <  INFO  <  WARNING  <  ERROR  <  CRITICAL
   ❌        ❌   │     ✅          ✅          ✅
```
Con `WARNING`: `info` **no** se escribe; `error` **sí**.
⚠️ Confusión común: "solo se escribe WARNING". Se escribe ese nivel **y todos los más graves**. Si no, un error grave quedaría oculto.

**3. `self.run_id = run_id`**
Guarda el dato **en el objeto** (la instancia), **en memoria**. Cuando `logging` llama `filtro.filter(registro)`, Python pasa **el mismo objeto** como `self`, y por eso `filter` puede leer lo que `__init__` guardó.
```python
filtro_a = FiltroRunId("aaa111")   # su self.run_id = "aaa111"
filtro_b = FiltroRunId("bbb222")   # su self.run_id = "bbb222"  (cada objeto recuerda el suyo)
```
⚠️ Confusiones comunes: "se guarda en la clase" (no: en cada objeto) y "se guarda en un archivo" (no: vive en la RAM mientras el objeto exista).
🧠 Esa es la razón de ser de una clase: un objeto **recuerda cosas entre llamadas**; una función no.

**4. Sobrescribir (*override*)**
La clase padre `logging.Formatter` ya tiene `format()`, que produce texto. La hija `FormateadorJson` define **un método con el mismo nombre** que produce JSON. Cuando `logging` llama `format()`, se ejecuta la versión de la hija. El resto del padre se sigue heredando.
⚠️ Confusión común: "reescribir configuraciones". Se reescribe un **método** (un comportamiento).
🧠 **Polimorfismo:** `logging` llama `format()` sin saber qué formateador recibió. Cambias el "cómo" sin tocar el sistema que lo usa.

**5. Para qué sirve el `run_id`**

| Pregunta | Campo |
|---|---|
| ¿Cuándo? | `momento` |
| ¿Qué gravedad? | `nivel` |
| ¿Dónde en el código? | `logger` |
| ¿Qué pasó? | `mensaje` / `error` |
| **¿En qué ejecución?** | **`run_id`** |

⚠️ Confusión común: "el run_id dice dónde, cuándo y la gravedad". Eso lo dan los otros campos. El `run_id` responde **qué líneas pertenecen a la misma ejecución**.
**Ejemplo:** dos cargas el mismo día escriben logs intercalados. Filtrando por `run_id` ves la historia completa de **una** carga. En H3, cada fila de datos también llevará `_run_id`: así un dato erróneo del reporte lleva a la ejecución que lo cargó (**trazabilidad / lineage**).

| Término nuevo | Definición |
|---|---|
| Umbral (*threshold*) | El nivel mínimo desde el que se escriben los mensajes |
| Instancia | Un objeto concreto creado desde una clase; cada una guarda sus propios atributos |
| Polimorfismo | Llamar al mismo método sin saber qué clase concreta lo implementa |
| `exc_info` | Información del error guardada en el registro cuando se usa `logger.exception` |
| Traceback | Texto del error: tipo, mensaje y archivo/línea donde ocurrió |
| Código inalcanzable | Líneas después de un `return`: nunca se ejecutan |
