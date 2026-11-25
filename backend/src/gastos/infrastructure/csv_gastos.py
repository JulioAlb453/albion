from src.core.application.importacion import ErrorFila, convertir_filas
from src.core.infrastructure.csv_utils import Fila, leer_tabla, nombre_de_columna
from src.core.infrastructure.exportacion import a_csv
from src.gastos.application.datos_gasto import DatosGasto
from src.gastos.domain.entities.gasto import CategoriaGasto

REQUERIDAS = ("categoria", "monto")
ENCABEZADOS_PLANTILLA = ("fecha", "categoria", "descripcion", "monto")
EJEMPLO = ("2026-11-25 14:30", "reparaciones", "Reparaciones tras el ZvZ", 500000)

# Como las escribiría una persona, además del valor técnico (compra_equipo) y el nombre del enum.
_ALIAS = {
    nombre_de_columna(texto): categoria
    for texto, categoria in {
        "compra de equipo": CategoriaGasto.COMPRA_EQUIPO,
        "reparacion": CategoriaGasto.REPARACIONES,
        "reequipamiento": CategoriaGasto.REEQUIPAMIENTO_BUILDS,
        "reequipamiento de builds": CategoriaGasto.REEQUIPAMIENTO_BUILDS,
        "ingredientes de comida": CategoriaGasto.INGREDIENTES_COMIDA,
        "ingredientes para comida": CategoriaGasto.INGREDIENTES_COMIDA,
    }.items()
}


def _a_datos(fila: Fila) -> DatosGasto:
    return DatosGasto(
        categoria=fila.opcion("categoria", CategoriaGasto, _ALIAS),
        descripcion=fila.texto("descripcion", ""),
        monto=fila.entero("monto"),
        fecha=fila.fecha("fecha"),
    )


def leer_gastos(contenido: bytes) -> tuple[list[DatosGasto], list[ErrorFila]]:
    """La fila 1 es el encabezado, así que los datos empiezan en la 2."""
    return convertir_filas(leer_tabla(contenido, REQUERIDAS), _a_datos, fila_inicial=2)


def plantilla_gastos() -> bytes:
    return a_csv(ENCABEZADOS_PLANTILLA, [EJEMPLO])
