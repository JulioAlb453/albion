import csv
import io
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

from fastapi import Response
from openpyxl import Workbook
from openpyxl.styles import Font

Formato = Literal["csv", "xlsx"]
Tabla = tuple[Sequence[str], Iterable[Sequence[object]]]

_TIPOS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
_INICIOS_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def _seguro(valor: object) -> object:
    """Un texto que empieza con `=`, `+`, `-` o `@` lo ejecuta Excel como fórmula: se neutraliza.
    Los números no se tocan (un -5 numérico no es un texto)."""
    if isinstance(valor, str) and valor.startswith(_INICIOS_DE_FORMULA):
        return "'" + valor
    return valor


def a_csv(encabezados: Sequence[str], filas: Iterable[Sequence[object]]) -> bytes:
    """UTF-8 con BOM: así Excel respeta las tildes al abrirlo con doble clic."""
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida)
    escritor.writerow(encabezados)
    escritor.writerows([_seguro(valor) for valor in fila] for fila in filas)
    return ("﻿" + salida.getvalue()).encode("utf-8")


def a_xlsx(hojas: Mapping[str, Tabla]) -> bytes:
    libro = Workbook()
    libro.remove(libro.active)
    for nombre, (encabezados, filas) in hojas.items():
        hoja = libro.create_sheet(nombre)
        hoja.append(list(encabezados))
        for celda in hoja[1]:
            celda.font = Font(bold=True)
        for fila in filas:
            hoja.append([_seguro(valor) for valor in fila])
        hoja.freeze_panes = "A2"
        for columna in hoja.columns:
            ancho = max(len(str(celda.value or "")) for celda in columna)
            hoja.column_dimensions[columna[0].column_letter].width = min(max(ancho + 2, 10), 50)
    memoria = io.BytesIO()
    libro.save(memoria)
    return memoria.getvalue()


def descarga(formato: Formato, nombre: str, hojas: Mapping[str, Tabla]) -> Response:
    """Excel lleva todas las hojas; CSV solo puede llevar una, la primera."""
    if formato == "xlsx":
        contenido = a_xlsx(hojas)
    else:
        encabezados, filas = next(iter(hojas.values()))
        contenido = a_csv(encabezados, filas)
    return Response(
        contenido,
        media_type=_TIPOS[formato],
        headers={"Content-Disposition": f'attachment; filename="{nombre}.{formato}"'},
    )
