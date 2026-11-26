from datetime import UTC, datetime

import pytest

from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, ErrorDominio
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.ventas.application.datos_venta import DatosVenta
from src.core.domain.value_objects.calidad import Calidad
from src.ventas.application.corregir_venta_use_case import CorregirVenta
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
        with pytest.raises(ErrorDominio, match="tarifa"):
            await self.caso.ejecutar(ADMIN, datos(tipo=TipoVenta.DIRECTA, tarifa_extra=500))
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


class TestCorregirVenta:
    def setup_method(self):
        self.repo = VentaRepoMemoria()
        self.caso = CorregirVenta(self.repo)

    async def test_cambia_encantamiento_y_calidad_sin_tocar_lo_demas(self):
        venta = await RegistrarVenta(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        desglose, fecha = venta.desglose, venta.fecha
        corregida = await self.caso.ejecutar(ADMIN, venta.id, encantamiento=3, calidad=5)
        assert (corregida.objeto.base_id, corregida.objeto.encantamiento, corregida.objeto.calidad) == (
            "T6_MAIN_SWORD", 3, Calidad.OBRA_MAESTRA
        )
        assert (corregida.desglose, corregida.fecha, corregida.id) == (desglose, fecha, venta.id)
        assert self.repo.items[venta.id].objeto.encantamiento == 3

    async def test_un_encantamiento_fuera_de_rango_no_se_guarda(self):
        venta = await RegistrarVenta(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        with pytest.raises(ErrorDominio):
            await self.caso.ejecutar(ADMIN, venta.id, encantamiento=5, calidad=1)
        assert self.repo.items[venta.id].objeto.encantamiento == 2

    async def test_una_venta_inexistente(self):
        with pytest.raises(EntidadNoEncontrada):
            await self.caso.ejecutar(ADMIN, 99, encantamiento=1, calidad=1)

    async def test_un_general_no_puede_corregir(self):
        venta = await RegistrarVenta(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, venta.id, encantamiento=1, calidad=1)


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
            datos(tipo=TipoVenta.DIRECTA, tarifa_extra=500),
            datos(precio_unitario=0),
        ]
        resultado = await self.caso.ejecutar(ADMIN, filas)
        assert resultado.importadas == 0
        assert [e.fila for e in resultado.errores] == [2, 3]
        assert self.repo.items == {}

    async def test_un_general_no_puede_importar(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, [datos()])
