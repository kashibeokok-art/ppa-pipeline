# Soluciones de la práctica

> ⚠️ **Intenta cada ejercicio primero.** Mira la solución solo después de ejecutar los tests y quedarte trabado, o para comparar.
> Si te trabas: 1) relee las **pistas** del archivo del ejercicio, 2) lee el **mensaje de error** de pytest, 3) recién entonces mira aquí.

---

## Ejercicio 01: `kwh_a_mwh`

```python
def kwh_a_mwh(kwh: float) -> float:
    """Convierte kWh a MWh en valor absoluto (RN-10)."""
    return abs(kwh) / 1000
```

Tests que faltaban:
```python
def test_negativo_se_convierte_en_valor_absoluto() -> None:
    assert kwh_a_mwh(-2500) == 2.5


def test_cero_es_cero() -> None:
    assert kwh_a_mwh(0) == 0.0
```

---

## Ejercicio 02: `validar_mes`

```python
def validar_mes(mes: int) -> int:
    """Devuelve el mes si está entre 1 y 12; si no, lanza ValueError."""
    if not (1 <= mes <= 12):
        raise ValueError(f"Mes fuera de rango: {mes}")
    return mes
```

Test que faltaba:
```python
@pytest.mark.parametrize("mes_invalido", [-1, 0, 13])
def test_meses_invalidos_fallan(mes_invalido: int) -> None:
    with pytest.raises(ValueError):
        validar_mes(mes_invalido)
```

---

## Ejercicio 03: `tipo_dia`

```python
def tipo_dia(dia_semana: int) -> TipoDia:
    """Clasifica el día de la semana (0=lunes ... 6=domingo) como hábil o no hábil."""
    if not (0 <= dia_semana <= 6):
        raise ValueError(f"Día de la semana fuera de rango: {dia_semana}")
    if dia_semana <= 4:
        return "HABIL"
    return "NO_HABIL"
```

Casos límite que faltaban en el `parametrize` (viernes = último hábil, sábado = primer no hábil):
```python
        (4, "HABIL"),  # viernes
        (5, "NO_HABIL"),  # sábado
```

Test que faltaba:
```python
@pytest.mark.parametrize("dia_invalido", [-1, 7])
def test_dia_invalido_falla(dia_invalido: int) -> None:
    with pytest.raises(ValueError):
        tipo_dia(dia_invalido)
```

---

## Ejercicio 04: `ConfigPractica`

```python
class ConfigPractica(BaseSettings):
    """Configuración de práctica. Cada atributo se lee de PRAC_<NOMBRE>."""

    model_config = SettingsConfigDict(env_prefix="PRAC_")

    zona_horaria: str = "America/Santiago"
    max_reintentos: int = 3
```

Tests que faltaban:
```python
def test_zona_horaria_desde_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAC_ZONA_HORARIA", "UTC")
    assert ConfigPractica().zona_horaria == "UTC"


def test_reintentos_invalidos_fallan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAC_MAX_REINTENTOS", "tres")
    with pytest.raises(ValidationError):
        ConfigPractica()
```

---

## Ejercicio 05: `leer_horas`

```python
def leer_horas(ruta: Path) -> list[int]:
    """Lee un archivo con una hora por línea y devuelve la lista de horas como enteros."""
    texto = ruta.read_text(encoding="utf-8")
    return [int(linea) for linea in texto.splitlines() if linea.strip()]
```

La última línea es una **comprensión de lista** (*list comprehension*). Equivale a:
```python
    horas = []
    for linea in texto.splitlines():
        if linea.strip():  # si la línea no está vacía
            horas.append(int(linea))
    return horas
```

Fixture y test que faltaban:
```python
@pytest.fixture
def archivo_con_lineas_vacias(tmp_path: Path) -> Path:
    ruta = tmp_path / "horas_con_vacios.txt"
    ruta.write_text("8\n\n17\n\n", encoding="utf-8")
    return ruta


def test_ignora_lineas_vacias(archivo_con_lineas_vacias: Path) -> None:
    assert leer_horas(archivo_con_lineas_vacias) == [8, 17]
```
