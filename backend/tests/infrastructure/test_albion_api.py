from datetime import UTC, datetime

import httpx
import pytest

from src.core.domain.errors import ServicioExternoNoDisponible
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.infrastructure.albion_data_api_proveedor import (
    AlbionDataApiProveedor,
    crear_cliente_albion,
)
from tests.domain.fixtures import ESPADA

BOLSA = ObjetoRef("T4_BAG")
SIN_DATO = "0001-01-01T00:00:00"


def fila(item_id, ciudad, calidad, venta=0, venta_fecha=SIN_DATO, compra=0, compra_fecha=SIN_DATO):
    """Una fila con el formato real de /api/v2/stats/prices."""
    return {
        "item_id": item_id, "city": ciudad, "quality": calidad,
        "sell_price_min": venta, "sell_price_min_date": venta_fecha,
        "sell_price_max": venta, "sell_price_max_date": venta_fecha,
        "buy_price_min": compra, "buy_price_min_date": compra_fecha,
        "buy_price_max": compra, "buy_price_max_date": compra_fecha,
    }


def proveedor(handler, **opciones):
    cliente = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://west.albion-online-data.com"
    )
    return AlbionDataApiProveedor(cliente, **opciones)


def responde(filas):
    return lambda request: httpx.Response(200, json=filas)


class TestPeticion:
    async def test_pide_los_ids_las_ciudades_y_las_calidades(self):
        recibidas = []

        def handler(request):
            recibidas.append(request)
            return httpx.Response(200, json=[])

        await proveedor(handler).obtener_precios(
            [ESPADA, BOLSA], [Ciudad.CAERLEON, Ciudad.BLACK_MARKET]
        )
        [peticion] = recibidas
        assert peticion.url.path == "/api/v2/stats/prices/T4_BAG,T6_MAIN_SWORD@2.json"
        assert peticion.url.params["locations"] == "Caerleon,Black Market"
        assert peticion.url.params["qualities"] == "1,4"  # la de la bolsa y la de la espada

    async def test_divide_en_lotes_y_no_repite_objetos(self):
        recibidas = []

        def handler(request):
            recibidas.append(request.url.path.removeprefix("/api/v2/stats/prices/").removesuffix(".json").split(","))
            return httpx.Response(200, json=[])

        objetos = [ObjetoRef(f"T4_ITEM{n}") for n in range(45)]
        await proveedor(handler, tamano_lote=20).obtener_precios(objetos + objetos[:5], [Ciudad.LYMHURST])
        assert [len(lote) for lote in recibidas] == [20, 20, 5]
        assert sorted(i for lote in recibidas for i in lote) == sorted(o.api_id for o in objetos)

    async def test_sin_objetos_o_sin_ciudades_no_llama_a_la_api(self):
        def handler(request):
            raise AssertionError("no debería haber consultado")

        assert await proveedor(handler).obtener_precios([], [Ciudad.LYMHURST]) == []
        assert await proveedor(handler).obtener_precios([ESPADA], []) == []


class TestRespuesta:
    async def test_convierte_las_filas_en_precios(self):
        api = proveedor(responde([
            fila("T6_MAIN_SWORD@2", "Caerleon", 4, venta=13_996, venta_fecha="2026-11-25T10:15:00"),
            fila("T6_MAIN_SWORD@2", "Black Market", 4, compra=4_898, compra_fecha="2026-11-25T19:25:00"),
        ]))
        precios = await api.obtener_precios([ESPADA], [Ciudad.CAERLEON, Ciudad.BLACK_MARKET])
        assert precios == [
            PrecioMercado(ESPADA, Ciudad.CAERLEON, 13_996, datetime(2026, 11, 25, 10, 15, tzinfo=UTC), 0, None),
            PrecioMercado(ESPADA, Ciudad.BLACK_MARKET, 0, None, 4_898, datetime(2026, 11, 25, 19, 25, tzinfo=UTC)),
        ]

    async def test_una_fecha_vacia_significa_que_no_hay_datos(self):
        [precio] = await proveedor(responde([fila("T6_MAIN_SWORD@2", "Martlock", 4)])).obtener_precios(
            [ESPADA], [Ciudad.MARTLOCK]
        )
        assert not precio.tiene_orden_venta and not precio.tiene_orden_compra

    async def test_ignora_calidades_y_ciudades_que_no_se_pidieron(self):
        api = proveedor(responde([
            fila("T4_BAG", "Lymhurst", 1, venta=100, venta_fecha="2026-11-25T10:00:00"),     # pedida
            fila("T4_BAG", "Lymhurst", 4, venta=200, venta_fecha="2026-11-25T10:00:00"),     # otra calidad
            fila("T6_MAIN_SWORD@2", "Lymhurst", 1, venta=300, venta_fecha="2026-11-25T10:00:00"),  # otra calidad
            fila("T4_BAG", "Thetford", 1, venta=400, venta_fecha="2026-11-25T10:00:00"),     # otra ciudad
            fila("T4_BAG", "Ciudad Inventada", 1, venta=500, venta_fecha="2026-11-25T10:00:00"),
            fila("T9_OTRA_COSA", "Lymhurst", 1, venta=600, venta_fecha="2026-11-25T10:00:00"),
        ]))
        precios = await api.obtener_precios([BOLSA, ESPADA], [Ciudad.LYMHURST])
        assert [(p.objeto, p.venta_minima) for p in precios] == [(BOLSA, 100)]

    async def test_conserva_la_calidad_pedida(self):
        buena = ObjetoRef("T4_BAG", 0, Calidad.BUENA)
        [precio] = await proveedor(responde([fila("T4_BAG", "Lymhurst", 2, compra=7, compra_fecha="2026-11-25T10:00:00")])).obtener_precios(
            [buena], [Ciudad.LYMHURST]
        )
        assert precio.objeto == buena


class TestErrores:
    @pytest.mark.parametrize(
        "respuesta, mensaje",
        [
            (httpx.Response(429), "demasiadas consultas"),
            (httpx.Response(503), "503"),
            (httpx.Response(200, text="<html>no es json</html>"), "inválida"),
            (httpx.Response(200, json={"error": "no es una lista"}), "inválida"),
        ],
    )
    async def test_una_respuesta_mala_se_informa(self, respuesta, mensaje):
        with pytest.raises(ServicioExternoNoDisponible, match=mensaje):
            await proveedor(lambda request: respuesta).obtener_precios([ESPADA], [Ciudad.LYMHURST])

    async def test_un_fallo_de_red_se_informa(self):
        def handler(request):
            raise httpx.ConnectTimeout("sin respuesta", request=request)

        with pytest.raises(ServicioExternoNoDisponible, match="no respondió"):
            await proveedor(handler).obtener_precios([ESPADA], [Ciudad.LYMHURST])


def test_el_cliente_apunta_al_servidor_de_america_y_se_identifica():
    cliente = crear_cliente_albion()
    assert str(cliente.base_url).startswith("https://west.albion-online-data.com")
    assert "albion-ventas-gremio" in cliente.headers["User-Agent"]
