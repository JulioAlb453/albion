from collections.abc import Mapping
from datetime import date

from pydantic import BaseModel, Field

from src.balance.domain.entities.punto_balance import PuntoBalance
from src.balance.domain.entities.reportes import GananciaObjeto, Reportes
from src.core.infrastructure.http.esquemas import ObjetoOut, objeto_out
from src.gastos.domain.entities.gasto import CategoriaGasto
from src.ingresos.domain.entities.ingreso import CategoriaIngreso


class SaldoInicialIO(BaseModel):
    monto: int = Field(ge=0)
    fecha: date


class PuntoBalanceOut(BaseModel):
    fecha: date
    ingresos: int  # ventas netas y otros ingresos del día
    gastos: int
    saldo: int  # saldo al cierre del día

    @classmethod
    def desde(cls, punto: PuntoBalance) -> "PuntoBalanceOut":
        return cls(fecha=punto.fecha, ingresos=punto.ingresos, gastos=punto.gastos, saldo=punto.saldo)


class GananciaObjetoOut(BaseModel):
    objeto: ObjetoOut
    unidades: int
    bruto: int
    impuesto: int
    tarifa_publicacion: int
    neto: int

    @classmethod
    def desde(cls, ganancia: GananciaObjeto, nombres: Mapping[str, str]) -> "GananciaObjetoOut":
        return cls(
            objeto=objeto_out(ganancia.objeto, nombres),
            unidades=ganancia.unidades,
            bruto=ganancia.bruto,
            impuesto=ganancia.impuesto,
            tarifa_publicacion=ganancia.tarifa_publicacion,
            neto=ganancia.neto,
        )


class ImpuestosOut(BaseModel):
    impuesto_venta: int
    tarifa_publicacion: int
    total: int


class GastoCategoriaOut(BaseModel):
    categoria: CategoriaGasto
    monto: int


class IngresoCategoriaOut(BaseModel):
    categoria: CategoriaIngreso
    monto: int


class ReportesOut(BaseModel):
    ganancia_por_objeto: list[GananciaObjetoOut]
    impuestos: ImpuestosOut
    gastos_por_categoria: list[GastoCategoriaOut]
    ventas_netas: int
    gastos_totales: int
    ingresos_extra: int  # plata que entró sin vender objetos
    ingresos_por_categoria: list[IngresoCategoriaOut]
    pagos_semanales: int  # lo pagado a miembros
    resultado: int

    @classmethod
    def desde(cls, reportes: Reportes, nombres: Mapping[str, str]) -> "ReportesOut":
        return cls(
            ganancia_por_objeto=[GananciaObjetoOut.desde(g, nombres) for g in reportes.ganancia_por_objeto],
            impuestos=ImpuestosOut(
                impuesto_venta=reportes.impuestos.impuesto_venta,
                tarifa_publicacion=reportes.impuestos.tarifa_publicacion,
                total=reportes.impuestos.total,
            ),
            gastos_por_categoria=[
                GastoCategoriaOut(categoria=categoria, monto=monto)
                for categoria, monto in reportes.gastos_por_categoria.items()
            ],
            ventas_netas=reportes.ventas_netas,
            gastos_totales=reportes.gastos_totales,
            ingresos_extra=reportes.ingresos_extra,
            ingresos_por_categoria=[
                IngresoCategoriaOut(categoria=categoria, monto=monto)
                for categoria, monto in reportes.ingresos_por_categoria.items()
            ],
            pagos_semanales=reportes.pagos_semanales,
            resultado=reportes.resultado,
        )
