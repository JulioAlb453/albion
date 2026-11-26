from datetime import UTC, date, datetime

import pytest

from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.infrastructure.sqlite_saldo_inicial_repository import SqliteSaldoInicialRepository
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos
from src.gastos.infrastructure.sqlite_gasto_repository import SqliteGastoRepository
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import FiltroVentas
from src.ventas.infrastructure.sqlite_venta_repository import SqliteVentaRepository
from tests.domain.fixtures import ESPADA
from src.core.domain.value_objects.objeto_ref import ObjetoRef


def dia(numero, hora=12):
    return datetime(2026, 11, numero, hora, tzinfo=UTC)


def venta(dia_=25, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.DIRECTA, objeto=ESPADA, **extra):
    return Venta.registrar(
        objeto=objeto, ciudad=ciudad, tipo=tipo, cantidad=2,
        precio_unitario=100_000, fecha=dia(dia_), **extra,
    )


class TestSqliteVentaRepository:
    @pytest.fixture
    def repo(self, db):
        return SqliteVentaRepository(db)

    async def test_guarda_y_recupera_lo_mismo(self, repo):
        guardada = await repo.save(venta(tipo=TipoVenta.ORDEN, tarifa_extra=1_500))
        assert guardada.id == 1
        assert await repo.get_by_id(1) == guardada
        assert guardada.desglose.tarifa_publicacion == 6_500  # 2.5 % de 200000 + 1500 de reajuste

    async def test_actualiza_el_objeto_de_una_venta(self, repo):
        import dataclasses
        guardada = await repo.save(venta())
        otra = await repo.save(venta(26))
        corregida = dataclasses.replace(guardada, objeto=ObjetoRef("T6_MAIN_SWORD", 4))
        await repo.update(corregida)
        assert await repo.get_by_id(guardada.id) == corregida
        assert await repo.get_by_id(otra.id) == otra

    async def test_una_venta_inexistente_es_none(self, repo):
        assert await repo.get_by_id(99) is None

    async def test_lista_ordenada_por_fecha(self, repo):
        await repo.save(venta(27))
        await repo.save(venta(25))
        await repo.save(venta(26))
        assert [v.fecha.day for v in await repo.list()] == [25, 26, 27]

    async def test_filtra_por_ciudad_tipo_y_objeto(self, repo):
        otra = ObjetoRef("T4_BAG")
        await repo.save(venta(ciudad=Ciudad.LYMHURST))
        await repo.save(venta(ciudad=Ciudad.CAERLEON, tipo=TipoVenta.ORDEN))
        await repo.save(venta(ciudad=Ciudad.LYMHURST, objeto=otra))
        assert [v.ciudad for v in await repo.list(FiltroVentas(ciudad=Ciudad.CAERLEON))] == [Ciudad.CAERLEON]
        assert len(await repo.list(FiltroVentas(tipo=TipoVenta.DIRECTA))) == 2
        assert [v.objeto for v in await repo.list(FiltroVentas(base_id="T4_BAG"))] == [otra]

    async def test_el_rango_de_fechas_incluye_los_extremos(self, repo):
        for numero in (24, 25, 26, 27):
            await repo.save(venta(numero))
        filtro = FiltroVentas(desde=dia(25), hasta=dia(26))
        assert [v.fecha.day for v in await repo.list(filtro)] == [25, 26]

    async def test_guarda_un_lote_y_asigna_ids(self, repo):
        guardadas = await repo.save_many([venta(25), venta(26)])
        assert [v.id for v in guardadas] == [1, 2]
        assert len(await repo.list()) == 2

    async def test_el_lote_es_todo_o_nada(self, repo):
        malas = [venta(25), venta(26)]
        malas[1].fecha = "no es una fecha"
        with pytest.raises(AttributeError):
            await repo.save_many(malas)
        assert await repo.list() == []
        assert malas[0].id is None  # no queda un id de una fila que se deshizo

    async def test_elimina(self, repo):
        guardada = await repo.save(venta())
        await repo.delete(guardada.id)
        assert await repo.get_by_id(guardada.id) is None


class TestSqliteGastoRepository:
    @pytest.fixture
    def repo(self, db):
        return SqliteGastoRepository(db)

    def gasto(self, dia_=25, categoria=CategoriaGasto.REPARACIONES):
        return Gasto(categoria, "ZvZ", 500_000, dia(dia_))

    async def test_guarda_y_recupera_lo_mismo(self, repo):
        guardado = await repo.save(self.gasto())
        assert guardado.id == 1 and await repo.get_by_id(1) == guardado

    async def test_filtra_por_categoria_y_rango(self, repo):
        await repo.save(self.gasto(24))
        await repo.save(self.gasto(26, CategoriaGasto.COMPRA_EQUIPO))
        await repo.save(self.gasto(28))
        por_categoria = await repo.list(FiltroGastos(categoria=CategoriaGasto.COMPRA_EQUIPO))
        assert [g.fecha.day for g in por_categoria] == [26]
        por_rango = await repo.list(FiltroGastos(desde=dia(25), hasta=dia(27)))
        assert [g.fecha.day for g in por_rango] == [26]

    async def test_el_lote_es_todo_o_nada(self, repo):
        malos = [self.gasto(25), self.gasto(26)]
        malos[1].fecha = None
        with pytest.raises(AttributeError):
            await repo.save_many(malos)
        assert await repo.list() == [] and malos[0].id is None

    async def test_elimina(self, repo):
        guardado = await repo.save(self.gasto())
        await repo.delete(guardado.id)
        assert await repo.list() == []


class TestSqliteSaldoInicialRepository:
    async def test_guardar_dos_veces_deja_un_solo_saldo(self, db):
        repo = SqliteSaldoInicialRepository(db)
        assert await repo.get() is None
        await repo.save(SaldoInicial(120_000_000, date(2026, 11, 25)))
        await repo.save(SaldoInicial(130_000_000, date(2026, 11, 26)))
        assert await repo.get() == SaldoInicial(130_000_000, date(2026, 11, 26))
