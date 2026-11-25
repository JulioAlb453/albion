from src.gastos.infrastructure.http.esquemas import GastoOut

ENCABEZADOS = ("fecha", "categoria", "descripcion", "monto")


def filas(gastos: list[GastoOut]) -> list[tuple]:
    return [
        (g.fecha.strftime("%Y-%m-%d %H:%M"), g.categoria.value, g.descripcion, g.monto)
        for g in gastos
    ]
