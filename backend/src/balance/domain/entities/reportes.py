from dataclasses import dataclass

from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.gastos.domain.entities.gasto import CategoriaGasto


@dataclass(frozen=True)
class GananciaObjeto:
    """Lo que dejó un objeto concreto (tier, encantamiento y calidad) en el periodo.

    Es neto de ventas: el gremio no registra el costo de compra de cada objeto.
    """

    objeto: ObjetoRef
    unidades: int
    bruto: int
    impuesto: int
    tarifa_publicacion: int
    neto: int


@dataclass(frozen=True)
class ResumenImpuestos:
    impuesto_venta: int
    tarifa_publicacion: int

    @property
    def total(self) -> int:
        return self.impuesto_venta + self.tarifa_publicacion


@dataclass(frozen=True)
class Reportes:
    ganancia_por_objeto: list[GananciaObjeto]  # de mayor a menor neto
    impuestos: ResumenImpuestos
    gastos_por_categoria: dict[CategoriaGasto, int]  # de mayor a menor monto
    ventas_netas: int
    gastos_totales: int

    @property
    def resultado(self) -> int:
        return self.ventas_netas - self.gastos_totales
