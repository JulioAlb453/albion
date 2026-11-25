"""Las fechas se guardan como texto ISO en UTC y con ancho fijo: así ordenar o comparar el texto
equivale a ordenar o comparar el tiempo."""

from datetime import datetime

from src.core.application.fechas import a_utc


def a_texto(fecha: datetime) -> str:
    return a_utc(fecha).isoformat(timespec="microseconds")


def a_texto_o_none(fecha: datetime | None) -> str | None:
    return None if fecha is None else a_texto(fecha)


def desde_texto(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def desde_texto_o_none(texto: str | None) -> datetime | None:
    return None if texto is None else desde_texto(texto)
