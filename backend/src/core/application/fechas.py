from datetime import UTC, datetime


def a_utc(fecha: datetime) -> datetime:
    """Una fecha sin zona se toma como UTC, la hora del servidor de Albion."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=UTC)
    return fecha.astimezone(UTC)


def a_utc_o_none(fecha: datetime | None) -> datetime | None:
    return None if fecha is None else a_utc(fecha)
