# Práctica: funciones, tests y clases

Ejercicios cortos para practicar lo que se usa en el proyecto. Van de menor a mayor dificultad.
**Antes de empezar, lee** [`docs/aprendizaje/06_como_se_construyo_config_y_tests.md`](../docs/aprendizaje/06_como_se_construyo_config_y_tests.md).

| # | Ejercicio | Qué practicas | Se parece a… |
|---|---|---|---|
| 01 | `ejercicio_01_unidades.py` | Función simple, `assert`, `pytest.approx` | RN-10 (valor absoluto, kWh→MWh) |
| 02 | `ejercicio_02_validar_mes.py` | Cláusula de guarda, `ValueError`, `pytest.raises` | Validación de hora en `bloques.py` |
| 03 | `ejercicio_03_tipo_dia.py` | `Literal`, `parametrize` con 2 valores, **valores límite** | RN-16 (día hábil) |
| 04 | `ejercicio_04_config.py` | **Tu primera clase**, `BaseSettings`, `monkeypatch` | `config.py` |
| 05 | `ejercicio_05_archivos.py` | Leer archivos, **fixture propia**, `tmp_path` | Lectura de archivos en Bronze (H3) |

## Cómo trabajar cada ejercicio (ciclo TDD)

1. **Lee** el archivo `ejercicio_NN_...py`: la regla, los ejemplos y las pistas están en el texto de arriba.
2. **Ejecuta los tests** y míralos fallar 🔴 (es lo esperado: la función todavía no existe):
   ```powershell
   uv run pytest practica/test_ejercicio_01_unidades.py -v
   ```
3. **Implementa** la función reemplazando `raise NotImplementedError(...)`.
4. **Ejecuta de nuevo** hasta ver 🟢.
5. **Escribe los tests marcados con `TODO`** en el archivo `test_ejercicio_NN_...py` y ejecútalos.
6. Compara con [`SOLUCIONES.md`](SOLUCIONES.md) **solo al final**.

## Ejecutar todos los ejercicios a la vez
```powershell
uv run pytest practica -v
```

## Notas
- Esta carpeta **no** la ejecuta el CI (el CI solo corre `tests/`), así que los ejercicios sin terminar no rompen nada.
- ruff sí la revisa en cada commit. Si ruff reclama algo, ejecuta `uv run ruff check practica --fix` y `uv run ruff format practica`.
