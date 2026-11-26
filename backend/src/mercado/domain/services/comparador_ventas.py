from collections.abc import Iterable
from datetime import datetime, timedelta

from src.core.domain.errors import ErrorDominio
from src.core.domain.services.calculadora_impuestos import (
    TASAS_PREMIUM,
    TasasMercado,
    calcular_desglose,
)
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.domain.value_objects.opcion_venta import ComparacionCiudad, OpcionVenta

# Los precios los suben jugadores; pasado este tiempo el dato se marca como no confiable.
ANTIGUEDAD_MAXIMA = timedelta(hours=6)


def _opcion(
    precio: PrecioMercado,
    tipo: TipoVenta,
    precio_unitario: int,
    fecha: datetime,
    cantidad: int,
    tasas: TasasMercado,
    ahora: datetime,
    antiguedad_maxima: timedelta,
) -> OpcionVenta:
    antiguedad = max(ahora - fecha, timedelta(0))
    return OpcionVenta(
        objeto=precio.objeto,
        ciudad=precio.ciudad,
        tipo=tipo,
        precio_unitario=precio_unitario,
        cantidad=cantidad,
        desglose=calcular_desglose(precio_unitario, cantidad, tipo, tasas),
        fecha_dato=fecha,
        antiguedad=antiguedad,
        confiable=antiguedad <= antiguedad_maxima,
    )


def comparar_por_ciudad(
    precios: Iterable[PrecioMercado],
    *,
    ahora: datetime,
    cantidad: int = 1,
    tasas: TasasMercado = TASAS_PREMIUM,
    antiguedad_maxima: timedelta = ANTIGUEDAD_MAXIMA,
) -> list[ComparacionCiudad]:
    """Venta directa contra orden de venta en cada ciudad, de mayor a menor neto
    (las de dato viejo, al final).

    - Directa: se vende a la orden de compra más alta.
    - Orden: se publica al precio de la orden de venta más barata (sin rebajarla).
    Las ciudades sin ningún dato quedan fuera.
    """
    precios = list(precios)
    if len({p.objeto for p in precios}) > 1:
        raise ErrorDominio("La comparación debe ser de un solo objeto")

    args = (cantidad, tasas, ahora, antiguedad_maxima)
    comparaciones = []
    for precio in precios:
        directa = None
        if precio.tiene_orden_compra:
            directa = _opcion(
                precio, TipoVenta.DIRECTA, precio.compra_maxima, precio.compra_maxima_fecha, *args
            )
        orden = None
        if precio.tiene_orden_venta:
            orden = _opcion(
                precio, TipoVenta.ORDEN, precio.venta_minima, precio.venta_minima_fecha, *args
            )
        if directa or orden:
            comparaciones.append(ComparacionCiudad(precio.ciudad, directa, orden))

    # Primero las ciudades con dato reciente, de mayor a menor neto; después las de dato viejo.
    return sorted(comparaciones, key=lambda c: (c.confiable, c.mejor.desglose.neto), reverse=True)


def mejores_opciones(comparaciones: Iterable[ComparacionCiudad]) -> list[OpcionVenta]:
    """Todas las opciones en una sola lista: primero las confiables, luego por neto."""
    opciones = [o for c in comparaciones for o in (c.directa, c.orden) if o is not None]
    return sorted(opciones, key=lambda o: (o.confiable, o.desglose.neto), reverse=True)
