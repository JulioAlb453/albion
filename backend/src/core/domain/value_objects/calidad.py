from enum import IntEnum


class Calidad(IntEnum):
    """El valor coincide con el parámetro `qualities` de la API de Albion."""

    NORMAL = 1
    BUENA = 2
    NOTABLE = 3
    SOBRESALIENTE = 4
    OBRA_MAESTRA = 5
