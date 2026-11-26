from datetime import datetime

from pydantic import BaseModel

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.mercado.domain.value_objects.opcion_venta import ComparacionCiudad, OpcionVenta


class ObjetoCatalogoOut(BaseModel):
    base_id: str
    nombre: str
    categoria: CategoriaObjeto
    tiene_calidad: bool
    # Rango de encantamiento que se puede elegir; min == max significa fijo (0..0: no se encanta).
    encantamiento_min: int
    encantamiento_max: int

    @classmethod
    def desde(cls, objeto: Objeto) -> "ObjetoCatalogoOut":
        return cls(
            base_id=objeto.base_id, nombre=objeto.nombre, categoria=objeto.categoria,
            tiene_calidad=bool(objeto.tiene_calidad),
            encantamiento_min=objeto.encantamiento_min, encantamiento_max=int(objeto.encantamiento_max or 0),
        )


class OpcionOut(BaseModel):
    tipo: TipoVenta
    precio_unitario: int
    bruto: int
    impuesto: int
    tarifa_publicacion: int
    neto: int
    neto_unitario: int
    fecha_dato: datetime
    antiguedad_segundos: int
    confiable: bool  # False si el dato es más viejo que el límite

    @classmethod
    def desde(cls, opcion: OpcionVenta | None) -> "OpcionOut | None":
        if opcion is None:
            return None
        return cls(
            tipo=opcion.tipo,
            precio_unitario=opcion.precio_unitario,
            bruto=opcion.desglose.bruto,
            impuesto=opcion.desglose.impuesto,
            tarifa_publicacion=opcion.desglose.tarifa_publicacion,
            neto=opcion.desglose.neto,
            neto_unitario=opcion.neto_unitario,
            fecha_dato=opcion.fecha_dato,
            antiguedad_segundos=int(opcion.antiguedad.total_seconds()),
            confiable=opcion.confiable,
        )


class ComparacionOut(BaseModel):
    ciudad: Ciudad
    es_del_gremio: bool
    directa: OpcionOut | None
    orden: OpcionOut | None  # None si nadie ha reportado órdenes de venta ahí
    mejor: TipoVenta | None
    confiable: bool  # si la mejor opción de la ciudad tiene un dato reciente
    diferencia_orden_vs_directa: int | None

    @classmethod
    def desde(cls, comparacion: ComparacionCiudad) -> "ComparacionOut":
        mejor = comparacion.mejor
        return cls(
            ciudad=comparacion.ciudad,
            es_del_gremio=comparacion.ciudad.es_del_gremio,
            confiable=comparacion.confiable,
            directa=OpcionOut.desde(comparacion.directa),
            orden=OpcionOut.desde(comparacion.orden),
            mejor=mejor.tipo if mejor else None,
            diferencia_orden_vs_directa=comparacion.diferencia_orden_vs_directa,
        )
