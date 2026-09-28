# 01 · Funciones y tests: la regla de bloques horarios (RN-01)

> **Hito:** H1.4 · **Archivos:** `src/ppa_pipeline/domain/bloques.py` y `tests/domain/test_bloques.py`
> **Conceptos:** función, *type hints*, `Literal`, docstring, cláusula de guarda, excepciones, pytest, decoradores, `parametrize`, `assert`, `pytest.raises`, TDD.

> ⚠️ **Aclaración:** este código **no es orientado a objetos**. No hay ninguna `class`. Son **funciones**, que es el estilo correcto para una regla de negocio simple. La programación orientada a objetos se explica al final (§4).

---

## 1. `bloques.py`: la regla de negocio

```python
 1  """Reglas de bloques horarios (RN-01) para licitación pública."""
 2
 3  from typing import Literal
 4
 5  Bloque = Literal["A", "B", "C"]
 6
 7
 8  def asignar_bloque(hora: int) -> Bloque:
 9      """Asigna el bloque horario de licitación pública a una hora de inicio (0-23).
10
11      RN-01:
12      A: 00:00 - 07:59 y 23:00 - 23:59
13      B: 08:00 - 17:59
14      C: 18:00 - 22:59
15
16      Raises:
17          ValueError: si la hora no está en el rango 0-23.
18      """
19      if not (0 <= hora <= 23):
20          raise ValueError(f"La hora {hora} no está en el rango 0-23.")
21
22      if 0 <= hora < 8 or hora == 23:
23          return "A"
24      elif 8 <= hora < 18:
25          return "B"
26      else:  # 18 <= hora < 23
27          return "C"
```

### Línea 1: docstring del módulo
- Un texto entre **tres comillas** (`"""`) al comienzo de un archivo es el **docstring de módulo**: describe para qué sirve el archivo.
- No se ejecuta como lógica. Lo leen VS Code (al pasar el mouse), `help()` y los generadores de documentación.
- Un archivo `.py` se llama **módulo**. Su nombre sale de la ruta de carpetas: `src/ppa_pipeline/domain/bloques.py` → `ppa_pipeline.domain.bloques`.

### Línea 3: importar
- `typing` es parte de la **biblioteca estándar** de Python; no hay que instalarlo.
- `from X import Y` significa "del módulo X, trae solo Y".
- `Literal` sirve para decir "este valor solo puede ser uno de estos valores exactos".

### Línea 5: alias de tipo (*type alias*)
- `Bloque = Literal["A", "B", "C"]` se lee: *"un Bloque es un texto que solo puede valer A, B o C"*.
- **No cambia la ejecución.** Python no bloquea un `"D"` al correr. Sirve para:
  1. documentar qué devuelve la función;
  2. que **mypy** detecte, sin ejecutar nada, si se devuelve un valor no permitido;
  3. que VS Code autocomplete los valores posibles.
- Convención: los tipos van con **mayúscula inicial** (`Bloque`) y las funciones y variables en minúscula (`asignar_bloque`).

### Líneas 6-7: dos líneas en blanco
Es la convención de estilo PEP 8 antes de un `def` de primer nivel. `ruff format` las pone automáticamente.

### Línea 8: definición de la función

```python
def asignar_bloque(hora: int) -> Bloque:
```

| Pieza | Significado |
|---|---|
| `def` | "Voy a **definir** una función" |
| `asignar_bloque` | El **nombre**. Es un verbo, porque la función *hace* algo |
| `hora` | El **parámetro**: el dato que la función recibe |
| `: int` | **Anotación de tipo** (*type hint*): se espera un entero |
| `-> Bloque` | **Tipo de retorno**: la función devuelve A, B o C |
| `:` | Aquí empieza el **cuerpo**. Todo lo **indentado** debajo pertenece a la función |

🧠 **Indentación:** en Python, los espacios al inicio de la línea definen qué está **dentro** de la función, del `if`, etc. El estándar son 4 espacios.

### Líneas 9-18: docstring de la función (estilo Google)
- **Primera línea:** qué hace, en una frase.
- **Cuerpo:** detalles. Aquí va la regla y su ID `RN-01`, que da la **trazabilidad** entre requerimiento y código.
- **`Raises:`:** qué errores puede lanzar y cuándo.

### Líneas 19-20: cláusula de guarda (*guard clause*)

```python
if not (0 <= hora <= 23):
    raise ValueError(f"La hora {hora} no está en el rango 0-23.")
```

- `0 <= hora <= 23` es una **comparación encadenada**. Equivale a `0 <= hora and hora <= 23`.
- `not (...)` invierte el resultado: el `if` entra cuando la hora **no** es válida.
- `raise` lanza una **excepción**. La función **se detiene ahí**: no devuelve nada y no sigue a las líneas de abajo.
- `ValueError` es el error estándar para "el tipo del dato es correcto, pero su **valor** no sirve".
- `f"...{hora}..."` es un **f-string**: la `f` permite insertar variables entre `{}`.

🧠 **¿Por qué validar primero?** Descartar los casos inválidos al inicio permite que el resto de la función **suponga** datos válidos. El legado hacía lo contrario: devolvía `'Desconocido'` y el dato malo llegaba al reporte sin que nadie lo notara.

### Líneas 22-27: la lógica de negocio
- **`if`**: si la condición es verdadera, ejecuta el bloque indentado.
  - `0 <= hora < 8` → horas 0 a 7 (00:00–07:59).
  - `or hora == 23` → **o** la hora 23. `==` **compara**; un solo `=` **asigna**.
- **`return "A"`**: la función termina y entrega `"A"` a quien la llamó.
- **`elif`** ("else if"): solo se evalúa si lo anterior fue falso. `8 <= hora < 18` son las horas 8 a 17.
- **`else`**: "en cualquier otro caso". Solo quedan las horas 18 a 22, el bloque C.
- **`# ...`**: un **comentario**. Python lo ignora.

🧠 **Rango semiabierto (`8 <= hora < 18`):** incluye el inicio y excluye el final. Así los bloques no se solapan ni dejan huecos.

---

## 2. `test_bloques.py`: la verificación

```python
 1  import pytest
 2
 3  from ppa_pipeline.domain.bloques import asignar_bloque
 4
 5
 6  @pytest.mark.parametrize(
 7      ("hora", "bloque_esperado"),
 8      [
 9          (0, "A"),
10          (7, "A"),
11          (8, "B"),
12          (17, "B"),
13          (18, "C"),
14          (22, "C"),
15          (23, "A"),
16      ],
17  )
18  def test_asignar_bloque(hora, bloque_esperado):
19      """RN-01: cada hora del día pertenece a un bloque horario de licitación publica."""
20      assert asignar_bloque(hora) == bloque_esperado
21
22
23  @pytest.mark.parametrize("hora_invalida", [-1, 24])
24  def test_asignar_bloque_hora_invalida(hora_invalida):
25      """Una hora fuera de 0-23 es un error de datos: debe fallar fuerte, no devolver un bloque."""
26      with pytest.raises(ValueError):
27          asignar_bloque(hora_invalida)
```

### Cómo encuentra pytest los tests (convención)
1. Busca en la carpeta `tests/` (configurado en `testpaths` del `pyproject.toml`).
2. Busca archivos que empiezan con **`test_`**.
3. Busca funciones que empiezan con **`test_`**.

Una función llamada `probar_bloque` sería **ignorada**.

### Línea 1: `import pytest`
Trae la librería completa. Se usa como `pytest.mark`, `pytest.raises`, etc.

### Línea 3: importar tu función
- La ruta con puntos corresponde a las carpetas: `ppa_pipeline` → `domain` → `bloques.py`.
- Funciona porque `uv sync` **instaló** tu paquete en `.venv` (*src layout*). No depende de desde qué carpeta ejecutes el comando.
- Hay una línea en blanco entre `pytest` (librería de terceros) y `ppa_pipeline` (tu código, *first-party*). Es la convención de agrupación de imports (regla `I` de ruff).

### Líneas 6-17: el decorador `parametrize`
- **`@algo` sobre un `def` es un decorador**: modifica o amplía la función de abajo sin cambiar su código. Aquí le dice a pytest: *"ejecuta esta función una vez por cada fila de datos"*.
- **`("hora", "bloque_esperado")`**: una **tupla** (colección entre `()` que no se puede modificar) con los **nombres** de los parámetros.
- **`[ ... ]`**: una **lista** con una **tupla por caso**. Los valores se asignan en el mismo orden que los nombres:
  - `(0, "A")` → `hora = 0`, `bloque_esperado = "A"`.
- **La coma final** en el último elemento hace que, al agregar un caso nuevo, git muestre solo una línea modificada.

**Resultado:** a partir de una función se generan **7 tests**: `test_asignar_bloque[0-A]`, `[7-A]`, etc. Si falla uno, sabes exactamente cuál.

🧠 **Valores límite (*Boundary Value Testing*):** los casos elegidos son los **bordes** (7|8, 17|18, 22|23). Los errores casi siempre aparecen ahí. Probar la hora 12 no descubre nada.

### Línea 18: la función de test
- Empieza con `test_`, así que pytest la encuentra.
- Sus parámetros tienen **los mismos nombres** que en `parametrize`: pytest los rellena en cada vuelta. Tú nunca llamas a esta función.

### Línea 19: docstring
Indica **qué regla verifica** el test. Completa la trazabilidad RN-01 ↔ código ↔ test.

### Línea 20: `assert`
1. Se ejecuta `asignar_bloque(hora)`. Por ejemplo, `asignar_bloque(23)` devuelve `"A"`.
2. Se compara con `bloque_esperado`: `"A" == "A"` da `True`.
3. **`assert`** afirma que algo es verdadero:
   - `True` → el test **pasa** ✅.
   - `False` → lanza un `AssertionError` y el test **falla** ❌; pytest muestra qué se obtuvo y qué se esperaba.

🧠 **Patrón Arrange / Act / Assert:** preparar los datos (`parametrize`) → ejecutar (llamar a la función) → verificar (`assert`).

### Línea 23: `parametrize` con un solo parámetro
Con un solo nombre, se escribe como texto simple y los valores como lista simple. Genera **2 tests** (`-1` y `24`), que son los valores **justo fuera** del rango válido.

### Líneas 24-27: verificar que **sí** falle
- **`with ...:`** abre un **bloque de contexto** (*context manager*): lo indentado se ejecuta "bajo vigilancia".
- **`pytest.raises(ValueError)`** significa: *"espero que aquí dentro ocurra un ValueError"*.
  - Si ocurre, el test **pasa** ✅ (la función falló como debía).
  - Si **no** ocurre, el test **falla** ❌.

**Total: 7 + 2 = 9 tests.**

---

## 3. Qué pasa al ejecutar `uv run pytest`

```
1. uv activa el entorno .venv
2. pytest lee pyproject.toml → busca en tests/
3. encuentra test_bloques.py → lo importa
       └─ eso importa asignar_bloque desde tu paquete instalado
4. encuentra 2 funciones test_*, con parametrize → las expande a 9 casos
5. ejecuta cada caso:
       asignar_bloque(23) → "A" → assert "A" == "A"                 → ✅
       asignar_bloque(24) → ValueError → pytest.raises lo esperaba  → ✅
6. imprime el resumen: 9 passed
```

### Comandos útiles

| Comando | Qué hace |
|---|---|
| `uv run pytest` | Ejecuta todos los tests |
| `uv run pytest -v` | Muestra cada caso por separado (*verbose*) |
| `uv run pytest tests/domain/test_bloques.py` | Solo ese archivo |
| `uv run pytest -k invalida` | Solo los tests cuyo nombre contiene "invalida" |
| `uv run pytest -x` | Se detiene en el primer fallo |

En VS Code también puedes usar el panel **Testing** (ícono del matraz 🧪).

### TDD: el orden en que se construyó esto
1. 🔴 **Rojo:** se escribió el test primero. Falló con `ModuleNotFoundError` porque `bloques.py` no existía.
2. 🟢 **Verde:** se escribió el código mínimo para que pasara.
3. 🔵 **Refactor:** se mejoró el formato (`ruff format`) sin cambiar el comportamiento.

**Lección real de esta sesión:** el test tenía `(23, "C")`, que es incorrecto según RN-01. **Un test incorrecto es peor que no tener test**, porque certifica el error en verde. Los casos se derivan de la regla escrita, no de la memoria.

---

## 4. Funciones vs. programación orientada a objetos (POO)

| | Funciones (este archivo) | Programación orientada a objetos |
|---|---|---|
| **Idea** | Entra un dato, sale un resultado | Un **objeto** agrupa **datos** (atributos) y **comportamiento** (métodos) |
| **Palabra clave** | `def` | `class` |
| **Cuándo conviene** | Reglas sin estado: "hora → bloque" | Cuando algo **recuerda cosas** entre llamadas: una conexión, una configuración, un cliente de API |

Un avance de cómo se ve (se verá en H2 y H3):

```python
class ClienteCEN:  # "molde" para crear objetos
    def __init__(self, api_key: str):  # se ejecuta al crear el objeto
        self.api_key = api_key  # el objeto GUARDA su clave (estado)

    def obtener_cmg(self, fecha: str):  # método: función que pertenece al objeto
        ...  # usa self.api_key sin pedirla de nuevo


cliente = ClienteCEN(api_key="...")  # crear un objeto (una instancia)
cliente.obtener_cmg("2026-08-01")  # usar su método
```

**Dónde aparece POO en el proyecto:**
- **H2:** configuración con `pydantic-settings`, una clase que guarda y valida las variables de entorno.
- **H3:** clientes para la API del CEN y para Plabacom, que guardan la clave, la sesión y los reintentos.
- **H6:** esquemas de calidad con `pandera`, una clase que describe cómo debe verse una tabla.

🧠 La regla de bloques **debe seguir siendo una función**. Usar una clase donde no hace falta es *over-engineering*. Saber cuándo **no** usar POO también es criterio de ingeniero.

---

## 5. Ejercicios de comprobación

Hazlos y luego **deshaz los cambios**:

1. **Rompe el código:** en `bloques.py`, cambia `hora == 23` por `hora == 22`. Ejecuta `uv run pytest -v`. ¿Qué tests fallan y qué dice el mensaje?
2. **Predice:** ¿qué devuelve `asignar_bloque(12)`? Compruébalo con:
   ```powershell
   uv run python -c "from ppa_pipeline.domain.bloques import asignar_bloque; print(asignar_bloque(12))"
   ```
3. **Agrega un caso** `(12, "B")` al `parametrize`. ¿Cuántos tests aparecen?
4. **Piensa:** si borras la cláusula de guarda (líneas 19-20), ¿qué devuelve `asignar_bloque(30)`? ¿Qué test falla? Revisa el `else`.

---

## 6. Glosario de esta lección

| Término | Definición breve |
|---|---|
| Módulo | Un archivo `.py`; se importa por su ruta con puntos |
| Paquete | Una carpeta con `__init__.py` que agrupa módulos |
| Función (`def`) | Bloque de código con nombre que recibe parámetros y devuelve un resultado |
| Parámetro | Variable que la función recibe (`hora`) |
| *Type hint* | Anotación del tipo esperado (`: int`, `-> Bloque`); no cambia la ejecución |
| `Literal` | Tipo que restringe a valores exactos (`"A"`, `"B"`, `"C"`) |
| Docstring | Documentación entre `"""` al inicio de un módulo o función |
| Excepción (`raise`) | Error que detiene la ejecución y avisa qué falló |
| `ValueError` | Excepción estándar para un valor inválido de tipo correcto |
| f-string | Texto con variables insertadas: `f"hora {hora}"` |
| Cláusula de guarda | Validación al inicio de la función que falla temprano |
| Decorador (`@`) | Modifica la función de abajo sin cambiar su código |
| Tupla / lista | `( )` no se puede modificar / `[ ]` sí se puede modificar |
| `assert` | Afirma que algo es verdadero; si no lo es, el test falla |
| *Context manager* (`with`) | Ejecuta un bloque bajo una condición o vigilancia |
| TDD | Test primero (rojo) → código (verde) → mejora (refactor) |
