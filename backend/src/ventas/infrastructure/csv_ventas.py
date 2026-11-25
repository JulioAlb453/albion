from src.core.application.importacion import ErrorFila, convertir_filas
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.csv_utils import Fila, leer_tabla
from src.core.infrastructure.exportacion import a_csv
from src.ventas.application.datos_venta import DatosVenta

REQUERIDAS = ("objeto", "ciudad", "tipo", "cantidad", "precio_unitario")
ENCABEZADOS_PLANTILLA = (
    "fecha", "objeto", "encantamiento", "calidad", "ciudad", "tipo",
    "cantidad", "precio_unitario", "tarifa_extra",
)
EJEMPLO = ("2026-11-25 14:30", "T6_MAIN_SWORD", 2, "Sobresaliente", "Fort Sterling", "orden", 1, 1500000, 0)


def _a_datos(fila: Fila) -> DatosVenta:
    calidad = fila.opcion("calidad", Calidad, defecto=Calidad.NORMAL)
    identificador = fila.texto("objeto").upper()
    if "@" in identificador:  # T6_MAIN_SWORD@2: el encantamiento viene en el identificador
        objeto = ObjetoRef.desde_api_id(identificador, calidad)
    else:
        objeto = ObjetoRef(identificador, fila.entero("encantamiento", 0), calidad)
    return DatosVenta(
        objeto=objeto,
        ciudad=fila.opcion("ciudad", Ciudad),
        tipo=fila.opcion("tipo", TipoVenta),
        cantidad=fila.entero("cantidad"),
        precio_unitario=fila.entero("precio_unitario"),
        fecha=fila.fecha("fecha"),
        tarifa_extra=fila.entero("tarifa_extra", 0),
    )


def leer_ventas(contenido: bytes) -> tuple[list[DatosVenta], list[ErrorFila]]:
    """La fila 1 es el encabezado, así que los datos empiezan en la 2."""
    return convertir_filas(leer_tabla(contenido, REQUERIDAS), _a_datos, fila_inicial=2)


def plantilla_ventas() -> bytes:
    return a_csv(ENCABEZADOS_PLANTILLA, [EJEMPLO])
