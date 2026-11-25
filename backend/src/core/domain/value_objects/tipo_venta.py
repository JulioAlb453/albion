from enum import StrEnum


class TipoVenta(StrEnum):
    DIRECTA = "directa"  # se vende a la orden de compra más alta
    ORDEN = "orden"      # se publica una orden de venta y se espera comprador
