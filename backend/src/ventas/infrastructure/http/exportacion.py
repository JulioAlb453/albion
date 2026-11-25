from src.ventas.infrastructure.http.esquemas import VentaOut

ENCABEZADOS = (
    "fecha", "objeto", "nombre", "encantamiento", "calidad", "ciudad", "tipo",
    "cantidad", "precio_unitario", "bruto", "impuesto", "tarifa_publicacion", "neto",
)


def filas(ventas: list[VentaOut]) -> list[tuple]:
    return [
        (
            v.fecha.strftime("%Y-%m-%d %H:%M"), v.objeto.base_id, v.objeto.nombre or "",
            v.objeto.encantamiento, int(v.objeto.calidad), v.ciudad.value, v.tipo.value,
            v.cantidad, v.precio_unitario, v.bruto, v.impuesto, v.tarifa_publicacion, v.neto,
        )
        for v in ventas
    ]
