from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.application.actualizar_precios_use_case import CIUDADES_MERCADO, ActualizarPrecios
from src.mercado.application.buscar_objetos_use_case import BuscarObjetos
from src.mercado.application.comparar_precios_use_case import CompararPrecios
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from tests.application.fakes import (
    CatalogoMemoria,
    PrecioRepoMemoria,
    ProveedorPreciosFalso,
    RelojFijo,
)
from tests.domain.fixtures import ESPADA, precio

PRECIOS = [
    precio(Ciudad.FORT_STERLING, venta=100_000, compra=90_000),
    precio(Ciudad.BLACK_MARKET, compra=150_000),
    precio(Ciudad.CAERLEON, venta=120_000),
]


class TestBuscarObjetos:
    def setup_method(self):
        self.caso = BuscarObjetos(
            CatalogoMemoria(
                [
                    Objeto("T6_MAIN_SWORD", "Espada ancha de adepto", CategoriaObjeto.ARMA),
                    Objeto("T6_ARMOR_PLATE_SET1", "Armadura de placas", CategoriaObjeto.ARMADURA),
                ]
            )
        )

    async def test_busca_por_nombre(self):
        encontrados = await self.caso.ejecutar("espada")
        assert [o.base_id for o in encontrados] == ["T6_MAIN_SWORD"]

    async def test_filtra_por_categoria(self):
        assert await self.caso.ejecutar("a", CategoriaObjeto.ARMADURA) == [
            Objeto("T6_ARMOR_PLATE_SET1", "Armadura de placas", CategoriaObjeto.ARMADURA)
        ]


class TestActualizarPrecios:
    def setup_method(self):
        self.proveedor = ProveedorPreciosFalso(PRECIOS)
        self.repo = PrecioRepoMemoria()
        self.caso = ActualizarPrecios(self.proveedor, self.repo)

    async def test_guarda_lo_que_devuelve_la_api(self):
        obtenidos = await self.caso.ejecutar([ESPADA])
        assert len(obtenidos) == 3
        assert set(self.repo.items) == {(ESPADA, p.ciudad) for p in PRECIOS}

    async def test_consulta_una_sola_vez_aunque_haya_objetos_repetidos(self):
        await self.caso.ejecutar([ESPADA, ESPADA])
        assert self.proveedor.llamadas == [{ESPADA}]

    async def test_sin_objetos_no_consulta_la_api(self):
        assert await self.caso.ejecutar([]) == []
        assert self.proveedor.llamadas == []

    async def test_por_defecto_consulta_todas_las_ciudades(self):
        assert set(CIUDADES_MERCADO) == set(Ciudad)

    async def test_solo_guarda_las_ciudades_pedidas(self):
        await self.caso.ejecutar([ESPADA], [Ciudad.CAERLEON])
        assert set(self.repo.items) == {(ESPADA, Ciudad.CAERLEON)}


class TestCompararPrecios:
    def armar(self, precios=PRECIOS):
        self.proveedor = ProveedorPreciosFalso(precios)
        repo = PrecioRepoMemoria()
        return CompararPrecios(repo, ActualizarPrecios(self.proveedor, repo), RelojFijo())

    async def test_ordena_las_ciudades_por_neto(self):
        comparaciones = await self.armar().ejecutar(ESPADA)
        # Black Market directa 144000 > Caerleon orden 112200 > Fort Sterling orden 93500
        assert [c.ciudad for c in comparaciones] == [
            Ciudad.BLACK_MARKET, Ciudad.CAERLEON, Ciudad.FORT_STERLING
        ]
        assert comparaciones[2].mejor.tipo is TipoVenta.ORDEN

    async def test_con_la_cache_vacia_consulta_la_api_y_despues_la_reutiliza(self):
        caso = self.armar()
        await caso.ejecutar(ESPADA)
        await caso.ejecutar(ESPADA)
        assert len(self.proveedor.llamadas) == 1

    async def test_la_cantidad_escala_el_neto(self):
        [primera, *_] = await self.armar().ejecutar(ESPADA, cantidad=3)
        assert primera.directa.desglose.neto == 432_000

    async def test_sin_datos_devuelve_vacio(self):
        assert await self.armar(precios=[]).ejecutar(ESPADA) == []
