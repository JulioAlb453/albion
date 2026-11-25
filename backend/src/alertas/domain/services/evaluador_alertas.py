from collections.abc import Iterable
from datetime import datetime, timedelta

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.core.domain.errors import ErrorDominio
from src.mercado.domain.value_objects.opcion_venta import ComparacionCiudad

# Evita repetir el mismo aviso en cada revisión de precios.
ESPERA_ENTRE_ALERTAS = timedelta(hours=2)


def evaluar(
    seguimiento: Seguimiento,
    comparaciones: Iterable[ComparacionCiudad],
    *,
    ultima_alerta: Alerta | None,
    ahora: datetime,
    espera: timedelta = ESPERA_ENTRE_ALERTAS,
) -> Alerta | None:
    """Devuelve la alerta de la mejor opción que cumple algún criterio, o None.

    Solo se consideran datos confiables (recientes): un precio viejo no dispara avisos.
    """
    if seguimiento.id is None:
        raise ErrorDominio("El seguimiento debe estar guardado antes de evaluarse")
    if not seguimiento.activo:
        return None
    if ultima_alerta is not None and ahora - ultima_alerta.fecha < espera:
        return None

    mejores = [c.mejor for c in comparaciones]
    candidatas = sorted(
        (o for o in mejores if o is not None and o.confiable),
        key=lambda o: o.neto_unitario,
        reverse=True,
    )
    referencia = next(
        (o.neto_unitario for o in candidatas if o.ciudad is seguimiento.ciudad_referencia), None
    )

    for opcion in candidatas:
        motivo = None
        if (
            seguimiento.porcentaje_minimo is not None
            and referencia
            and opcion.ciudad is not seguimiento.ciudad_referencia
            and opcion.neto_unitario * 100 >= referencia * (100 + seguimiento.porcentaje_minimo)
        ):
            ganancia = (opcion.neto_unitario - referencia) * 100 / referencia
            motivo = (
                f"{opcion.ciudad} paga {ganancia:.1f}% más neto que "
                f"{seguimiento.ciudad_referencia}"
            )
        elif seguimiento.neto_minimo is not None and opcion.neto_unitario >= seguimiento.neto_minimo:
            motivo = f"El neto en {opcion.ciudad} alcanza {opcion.neto_unitario:,} de plata"

        if motivo:
            return Alerta(
                seguimiento_id=seguimiento.id,
                ciudad=opcion.ciudad,
                tipo=opcion.tipo,
                neto_unitario=opcion.neto_unitario,
                neto_referencia=referencia,
                motivo=motivo,
                fecha=ahora,
            )
    return None
