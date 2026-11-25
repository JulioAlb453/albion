from datetime import UTC, datetime

import pytest

from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, ErrorDominio
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.ventas.application.datos_venta import DatosVenta
from src.ventas.application.eliminar_venta_use_case import EliminarVenta
from src.ventas.application.importar_ventas_use_case import ImportarVentas
from src.ventas.application.listar_ventas_use_case import ListarVentas
from src.ventas.application.registrar_venta_use_case import RegistrarVenta
from src.ventas.domain.ports.i_venta_repository import FiltroVentas
from tests.application.fakes import ADMIN, GENERAL, RelojFijo, VentaRepoMemoria
from tests.domain.fixtures import AHORA, ESPADA


def datos(**cambios):
    base = dict(
        objeto=ESPADA, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.DIRECTA,
        cantidad=1, precio_unitario=100_000,
    )
    return DatosVenta(**(base | cambios))


class TestRegistrarVenta:
    def setup_method(self):
        self.repo = VentaRepoMemoria()
        self.caso = RegistrarVenta(self.repo, RelojFijo())

    async def test_guarda_con_desglose_y_fecha_del_reloj(self):
        venta = await self.caso.ejecutar(ADMIN, datos())
        assert venta.id == 1 and venta.fecha == AHORA
        assert venta.desglose.neto == 96_000
        assert self.repo.items == {1: venta}

    async def test_normaliza_la_fecha_a_utc(self):
        venta = await self.caso.ejecutar(ADMIN, datos(fecha=datetime(2026, 11, 24, 18)))
        assert venta.fecha == datetime(2026, 11, 24, 18, tzinfo=UTC)

    async def test_un_general_no_puede_registrar(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, datos())
        assert self.repo.items == {}

    async def test_una_regla_de_dominio_impide_guardar(self):
        with pytest.raises(ErrorDominio, match="Black Market"):
            await self.caso.ejecutar(
                ADMIN, datos(ciudad=Ciudad.BLACK_MARKET, tipo=TipoVenta.ORDEN)
            )
        assert self.repo.items == {}


class TestListarVentas:
    def setup_method(self):
        self.repo = VentaRepoMemoria()
        self.registrar = RegistrarVenta(self.repo, RelojFijo())

    async def test_filtra_por_ciudad(self):
        await self.registrar.ejecutar(ADMIN, datos(ciudad=Ciudad.LYMHURST))
        await self.registrar.ejecutar(ADMIN, datos(ciudad=Ciudad.CAERLEON))
        ventas = await ListarVentas(self.repo).ejecutar(FiltroVentas(ciudad=Ciudad.CAERLEON))
        assert [v.ciudad for v in ventas] == [Ciudad.CAERLEON]

    async def test_acepta_fechas_sin_zona_en_el_filtro(self):
        await self.registrar.ejecutar(ADMIN, datos())
        filtro = FiltroVentas(desde=datetime(2026, 11, 25), hasta=datetime(2026, 11, 26))
        assert len(await ListarVentas(self.repo).ejecutar(filtro)) == 1


class TestEliminarVenta:
    def setup_method(self):
        self.repo = VentaRepoMemoria()
        self.caso = EliminarVenta(self.repo)

    async def test_elimina(self):
        venta = await RegistrarVenta(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        await self.caso.ejecutar(ADMIN, venta.id)
        assert self.repo.items == {}

    async def test_una_venta_inexistente_no_se_puede_eliminar(self):
        with pytest.raises(EntidadNoEncontrada):
            await self.caso.ejecutar(ADMIN, 99)

    async def test_un_general_no_puede_eliminar(self):
        venta = await RegistrarVenta(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, venta.id)
        assert venta.id in self.repo.items


class TestImportarVentas:
    def setup_method(self):
        self.repo = VentaRepoMemoria()
        self.caso = ImportarVentas(self.repo, RelojFijo())

    async def test_guarda_todas_en_un_lote(self):
        resultado = await self.caso.ejecutar(ADMIN, [datos(), datos(cantidad=2)])
        assert resultado.importadas == 2
        assert self.repo.lotes == 1 and len(self.repo.items) == 2

    async def test_una_fila_mala_cancela_todo(self):
        filas = [
            datos(),
            datos(ciudad=Ciudad.BLACK_MARKET, tipo=TipoVenta.ORDEN),
            datos(precio_unitario=0),
        ]
        resultado = await self.caso.ejecutar(ADMIN, filas)
        assert resultado.importadas == 0
        assert [e.fila for e in resultado.errores] == [2, 3]
        assert self.repo.items == {}

    async def test_un_general_no_puede_importar(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, [datos()])
