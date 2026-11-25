from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from src.core.domain.errors import ErrorDominio
from src.core.domain.value_objects.tipo_venta import TipoVenta


@dataclass(frozen=True)
class TasasMercado:
    impuesto_venta: Decimal
    tarifa_publicacion: Decimal  # setup fee: se cobra al publicar la orden y no se devuelve


TASAS_PREMIUM = TasasMercado(impuesto_venta=Decimal("0.04"), tarifa_publicacion=Decimal("0.025"))
TASAS_SIN_PREMIUM = TasasMercado(impuesto_venta=Decimal("0.08"), tarifa_publicacion=Decimal("0.025"))


@dataclass(frozen=True)
class DesgloseVenta:
    bruto: int
    impuesto: int
    tarifa_publicacion: int
    neto: int

    def __post_init__(self) -> None:
        if self.bruto <= 0 or self.impuesto < 0 or self.tarifa_publicacion < 0:
            raise ErrorDominio("Desglose con montos inválidos")
        if self.neto != self.bruto - self.total_cargos:
            raise ErrorDominio("El neto no cuadra con el bruto menos los cargos")

    @property
    def total_cargos(self) -> int:
        return self.impuesto + self.tarifa_publicacion


def _porcentaje(monto: int, tasa: Decimal) -> int:
    return int((Decimal(monto) * tasa).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def calcular_desglose(
    precio_unitario: int,
    cantidad: int,
    tipo: TipoVenta,
    tasas: TasasMercado = TASAS_PREMIUM,
    tarifa_extra: int = 0,
) -> DesgloseVenta:
    """Plata que recibe el gremio por una venta.

    `tarifa_extra` es lo pagado al reajustar el precio de una orden ya publicada:
    cada reajuste vuelve a cobrar tarifa y el juego no la devuelve.
    """
    if precio_unitario <= 0:
        raise ErrorDominio("El precio unitario debe ser mayor a cero")
    if cantidad <= 0:
        raise ErrorDominio("La cantidad debe ser mayor a cero")
    if tarifa_extra < 0:
        raise ErrorDominio("La tarifa extra no puede ser negativa")
    if tipo is TipoVenta.DIRECTA and tarifa_extra:
        raise ErrorDominio("La venta directa no paga tarifa de publicación")

    bruto = precio_unitario * cantidad
    impuesto = _porcentaje(bruto, tasas.impuesto_venta)
    tarifa = 0
    if tipo is TipoVenta.ORDEN:
        tarifa = _porcentaje(bruto, tasas.tarifa_publicacion) + tarifa_extra
    return DesgloseVenta(bruto, impuesto, tarifa, bruto - impuesto - tarifa)
