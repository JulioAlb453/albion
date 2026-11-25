from src.balance.infrastructure.http.esquemas import ReportesOut
from src.core.infrastructure.exportacion import Tabla


def hojas(reportes: ReportesOut) -> dict[str, Tabla]:
    """La primera hoja es también lo que se lleva el CSV, que solo admite una tabla."""
    return {
        "Ganancia por objeto": (
            ("objeto", "nombre", "encantamiento", "calidad", "unidades", "bruto",
             "impuesto", "tarifa_publicacion", "neto"),
            [
                (
                    g.objeto.base_id, g.objeto.nombre or "", g.objeto.encantamiento,
                    int(g.objeto.calidad), g.unidades, g.bruto, g.impuesto,
                    g.tarifa_publicacion, g.neto,
                )
                for g in reportes.ganancia_por_objeto
            ],
        ),
        "Impuestos y resultado": (
            ("concepto", "monto"),
            [
                ("ventas_netas", reportes.ventas_netas),
                ("impuesto_venta", reportes.impuestos.impuesto_venta),
                ("tarifa_publicacion", reportes.impuestos.tarifa_publicacion),
                ("total_impuestos", reportes.impuestos.total),
                ("gastos_totales", reportes.gastos_totales),
                ("resultado", reportes.resultado),
            ],
        ),
        "Gastos por categoria": (
            ("categoria", "monto"),
            [(g.categoria.value, g.monto) for g in reportes.gastos_por_categoria],
        ),
    }
