from enum import StrEnum


class Ciudad(StrEnum):
    """Mercados del servidor Americas. El valor es el nombre que usa la API de Albion."""

    BRIDGEWATCH = "Bridgewatch"
    FORT_STERLING = "Fort Sterling"
    LYMHURST = "Lymhurst"
    MARTLOCK = "Martlock"
    THETFORD = "Thetford"
    CAERLEON = "Caerleon"
    BRECILIEN = "Brecilien"
    BLACK_MARKET = "Black Market"

    @property
    def es_del_gremio(self) -> bool:
        return self in CIUDADES_GREMIO


# Ciudades donde el gremio tiene isla. Fort Sterling es la principal.
CIUDAD_PRINCIPAL = Ciudad.FORT_STERLING
CIUDADES_GREMIO = frozenset({Ciudad.FORT_STERLING, Ciudad.LYMHURST, Ciudad.CAERLEON})
