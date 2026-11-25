"""Precios del Albion Online Data Project (https://www.albion-online-data.com).

Los precios los suben jugadores con el cliente del proyecto, así que pueden ser viejos o faltar:
cada precio trae la fecha de su dato y una fecha `0001-01-01` significa "sin datos".
"""

from collections.abc import Iterable, Iterator
from datetime import datetime

import httpx

from src.core.application.fechas import a_utc
from src.core.domain.errors import ServicioExternoNoDisponible
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.domain.ports.i_proveedor_precios import IProveedorPrecios

URL_AMERICA = "https://west.albion-online-data.com"
AGENTE = "albion-ventas-gremio/0.1"


def crear_cliente_albion(base_url: str = URL_AMERICA, timeout: float = 15.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=timeout, headers={"User-Agent": AGENTE})


def _fecha(texto: str) -> datetime | None:
    fecha = datetime.fromisoformat(texto)
    return None if fecha.year == 1 else a_utc(fecha)


def _lotes(ids: list[str], tamano: int) -> Iterator[list[str]]:
    for inicio in range(0, len(ids), tamano):
        yield ids[inicio : inicio + tamano]


class AlbionDataApiProveedor(IProveedorPrecios):
    def __init__(self, cliente: httpx.AsyncClient, tamano_lote: int = 20):
        self._cliente = cliente
        self._tamano_lote = tamano_lote

    async def obtener_precios(
        self, objetos: Iterable[ObjetoRef], ciudades: Iterable[Ciudad]
    ) -> list[PrecioMercado]:
        pedidos = {(o.api_id, int(o.calidad)): o for o in objetos}
        ciudades = list(dict.fromkeys(ciudades))
        if not pedidos or not ciudades:
            return []
        calidades = sorted({calidad for _, calidad in pedidos})
        ids = sorted({api_id for api_id, _ in pedidos})

        precios: list[PrecioMercado] = []
        for lote in _lotes(ids, self._tamano_lote):
            for fila in await self._consultar(lote, ciudades, calidades):
                precio = self._a_precio(fila, pedidos, ciudades)
                if precio is not None:
                    precios.append(precio)
        return precios

    async def _consultar(
        self, ids: list[str], ciudades: list[Ciudad], calidades: list[int]
    ) -> list[dict]:
        try:
            respuesta = await self._cliente.get(
                f"/api/v2/stats/prices/{','.join(ids)}.json",
                params={
                    "locations": ",".join(c.value for c in ciudades),
                    "qualities": ",".join(str(c) for c in calidades),
                },
            )
        except httpx.TransportError as error:
            raise ServicioExternoNoDisponible(f"La API de Albion no respondió: {error!r}") from error
        if respuesta.status_code == 429:
            raise ServicioExternoNoDisponible(
                "La API de Albion rechazó la consulta por demasiadas consultas; espera un momento"
            )
        if respuesta.is_error:
            raise ServicioExternoNoDisponible(
                f"La API de Albion respondió con el código {respuesta.status_code}"
            )
        try:
            filas = respuesta.json()
        except ValueError:
            filas = None
        if not isinstance(filas, list):
            raise ServicioExternoNoDisponible("La API de Albion devolvió una respuesta inválida")
        return filas

    @staticmethod
    def _a_precio(
        fila: dict, pedidos: dict[tuple[str, int], ObjetoRef], ciudades: list[Ciudad]
    ) -> PrecioMercado | None:
        """La API devuelve todas las combinaciones de objeto, ciudad y calidad: solo valen las pedidas."""
        try:
            objeto = pedidos.get((fila["item_id"], fila["quality"]))
            ciudad = Ciudad(fila["city"]) if fila["city"] in Ciudad else None
            if objeto is None or ciudad not in ciudades:
                return None
            return PrecioMercado(
                objeto=objeto,
                ciudad=ciudad,
                venta_minima=fila["sell_price_min"],
                venta_minima_fecha=_fecha(fila["sell_price_min_date"]),
                compra_maxima=fila["buy_price_max"],
                compra_maxima_fecha=_fecha(fila["buy_price_max_date"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ServicioExternoNoDisponible("La API de Albion devolvió una respuesta inválida") from error
