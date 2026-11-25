"""Lectura tolerante de CSV: lo que guarda Excel en español rara vez es CSV "de manual".

Acepta separador `,`, `;` o tabulador, BOM, codificación UTF-8 o la de Windows, nombres de
columna con mayúsculas, tildes o espacios, y números con separador de miles.
"""

import csv
import io
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

from src.core.application.texto import normalizar_texto
from src.core.domain.errors import ErrorDominio


class ErrorArchivo(ErrorDominio):
    """El archivo entero no sirve (vacío o sin las columnas necesarias)."""


def nombre_de_columna(texto: str) -> str:
    """"Precio unitario" y "precio_unitario" son la misma columna."""
    return "_".join(normalizar_texto(texto).replace("-", " ").split())


def decodificar(contenido: bytes) -> str:
    try:
        return contenido.decode("utf-8-sig")
    except UnicodeDecodeError:  # "CSV (delimitado por comas)" de Excel en Windows
        return contenido.decode("cp1252", errors="replace")


class Fila:
    """Una fila ya separada en columnas, con lectores que dicen qué columna falló."""

    def __init__(self, valores: Mapping[str, str]):
        self._valores = valores

    def _valor(self, columna: str) -> str:
        return self._valores.get(columna, "").strip()

    def texto(self, columna: str, defecto: str | None = None) -> str:
        valor = self._valor(columna)
        if valor:
            return valor
        if defecto is None:
            raise ErrorDominio(f"{columna}: falta el valor")
        return defecto

    def entero(self, columna: str, defecto: int | None = None) -> int:
        valor = self._valor(columna)
        if not valor:
            if defecto is None:
                raise ErrorDominio(f"{columna}: falta el valor")
            return defecto
        try:
            numero = Decimal(valor.replace(",", "").replace(" ", ""))
        except InvalidOperation:
            raise ErrorDominio(f"{columna}: '{valor}' no es un número entero") from None
        if not numero.is_finite() or numero != numero.to_integral_value():
            raise ErrorDominio(f"{columna}: '{valor}' no es un número entero")
        return int(numero)

    def fecha(self, columna: str) -> datetime | None:
        valor = self._valor(columna)
        if not valor:
            return None
        for formato in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):  # como la escribe Excel en México
            try:
                return datetime.strptime(valor, formato)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            raise ErrorDominio(
                f"{columna}: '{valor}' no es una fecha (usa AAAA-MM-DD o AAAA-MM-DD HH:MM)"
            ) from None

    def opcion[E: Enum](
        self,
        columna: str,
        tipo: type[E],
        alias: Mapping[str, E] | None = None,
        defecto: E | None = None,
    ) -> E:
        """Elige un miembro del enum por su valor o su nombre, sin importar mayúsculas ni tildes."""
        valor = self._valor(columna)
        if not valor:
            if defecto is None:
                raise ErrorDominio(f"{columna}: falta el valor")
            return defecto
        claves = (
            {nombre_de_columna(str(m.value)): m for m in tipo}
            | {nombre_de_columna(m.name): m for m in tipo}
            | dict(alias or {})
        )
        miembro = claves.get(nombre_de_columna(valor))
        if miembro is None:
            opciones = ", ".join(str(m.value) for m in tipo)
            raise ErrorDominio(f"{columna}: '{valor}' no es válido (opciones: {opciones})")
        return miembro


def leer_tabla(contenido: bytes, requeridas: Sequence[str]) -> list[Fila]:
    texto = decodificar(contenido)
    if not texto.strip():
        raise ErrorArchivo("El archivo está vacío")
    delimitador = max(",;\t", key=texto.splitlines()[0].count)
    lector = csv.reader(io.StringIO(texto), delimiter=delimitador)
    columnas = [nombre_de_columna(columna) for columna in next(lector)]
    faltantes = [columna for columna in requeridas if columna not in columnas]
    if faltantes:
        raise ErrorArchivo("Faltan las columnas: " + ", ".join(faltantes))
    filas = [dict(zip(columnas, fila)) for fila in lector]
    while filas and not any(valor.strip() for valor in filas[-1].values()):
        filas.pop()  # Excel deja filas vacías al final
    return [Fila(fila) for fila in filas]
