from datetime import datetime

from pydantic import BaseModel, Field

from src.gastos.application.datos_gasto import DatosGasto
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto


class GastoIn(BaseModel):
    categoria: CategoriaGasto
    descripcion: str = ""
    monto: int = Field(gt=0)
    fecha: datetime | None = None  # sin fecha se usa la hora actual

    def a_dominio(self) -> DatosGasto:
        return DatosGasto(self.categoria, self.descripcion, self.monto, self.fecha)


class GastoOut(BaseModel):
    id: int
    categoria: CategoriaGasto
    descripcion: str
    monto: int
    fecha: datetime

    @classmethod
    def desde(cls, gasto: Gasto) -> "GastoOut":
        return cls(
            id=gasto.id, categoria=gasto.categoria, descripcion=gasto.descripcion,
            monto=gasto.monto, fecha=gasto.fecha,
        )
