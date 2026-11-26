from dataclasses import dataclass, field

from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.gastos.domain.entities.gasto import CategoriaGasto
from src.ingresos.domain.entities.ingreso import CategoriaIngreso


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
    ingresos_por_categoria: dict[CategoriaIngreso, int] = field(default_factory=dict)  # de mayor a menor
    pagos_semanales: int = 0  # lo pagado a miembros en el periodo

    @property
    def ingresos_extra(self) -> int:
        return sum(self.ingresos_por_categoria.values())

    @property
    def resultado(self) -> int:
        return self.ventas_netas + self.ingresos_extra - self.gastos_totales - self.pagos_semanales
