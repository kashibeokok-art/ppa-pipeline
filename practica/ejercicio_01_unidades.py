"""Ejercicio 01: tu primera función con test.

Objetivo: convertir energía de kWh a MWh, aplicando RN-10 (se trabaja en valor absoluto).

Regla:
    MWh = |kWh| / 1000

Ejemplos:
    kwh_a_mwh(1000)  -> 1.0
    kwh_a_mwh(-2500) -> 2.5    (los retiros pueden venir negativos: RN-10 usa valor absoluto)
    kwh_a_mwh(0)     -> 0.0

Pistas:
    - abs(x) devuelve el valor absoluto.
    - Reemplaza la línea `raise NotImplementedError` por tu implementación (una línea basta).
"""


def kwh_a_mwh(kwh: float) -> float:
    """Convierte kWh a MWh en valor absoluto (RN-10)."""
    return abs(kwh) / 1000
