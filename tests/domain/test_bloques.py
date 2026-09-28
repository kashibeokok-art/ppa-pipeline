import pytest

from ppa_pipeline.domain.bloques import asignar_bloque


@pytest.mark.parametrize(
    ("hora", "bloque_esperado"),
    [
        (0, "A"),
        (7, "A"),
        (8, "B"),
        (17, "B"),
        (18, "C"),
        (22, "C"),
        (23, "A"),
    ],
)
def test_asignar_bloque(hora: int, bloque_esperado: str) -> None:
    """RN-01: cada hora del día pertenece a un bloque horario de licitación publica."""
    assert asignar_bloque(hora) == bloque_esperado


@pytest.mark.parametrize("hora_invalida", [-1, 24])
def test_asignar_bloque_hora_invalida(hora_invalida: int) -> None:
    """Una hora fuera de 0-23 es un error de datos: debe fallar fuerte, no devolver un bloque."""
    with pytest.raises(ValueError):
        asignar_bloque(hora_invalida)
