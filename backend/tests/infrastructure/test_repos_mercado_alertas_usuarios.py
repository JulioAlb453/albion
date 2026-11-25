import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.infrastructure.sqlite_alerta_repository import SqliteAlertaRepository
from src.alertas.infrastructure.sqlite_seguimiento_repository import SqliteSeguimientoRepository
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.infrastructure.sqlite_precio_mercado_repository import (
    SqlitePrecioMercadoRepository,
)
from src.usuarios.domain.entities.usuario import Rol, Usuario
from src.usuarios.infrastructure.sqlite_usuario_repository import SqliteUsuarioRepository
from tests.domain.fixtures import AHORA, ESPADA, precio

BOLSA = ObjetoRef("T4_BAG")


class TestSqlitePrecioMercadoRepository:
    @pytest.fixture
    def repo(self, db):
        return SqlitePrecioMercadoRepository(db)

    async def test_guarda_y_devuelve_los_precios_pedidos(self, repo):
        fort = precio(Ciudad.FORT_STERLING, venta=100_000, compra=90_000)
        await repo.save_many([fort, precio(Ciudad.CAERLEON, venta=120_000), precio(Ciudad.CAERLEON, compra=1, objeto=BOLSA)])
        assert await repo.get(ESPADA, [Ciudad.FORT_STERLING]) == [fort]
        assert {p.ciudad for p in await repo.get(ESPADA, list(Ciudad))} == {Ciudad.FORT_STERLING, Ciudad.CAERLEON}

    async def test_conserva_los_precios_sin_ordenes_con_fechas_vacias(self, repo):
        sin_datos = precio(Ciudad.MARTLOCK)
        await repo.save_many([sin_datos])
        [leido] = await repo.get(ESPADA, [Ciudad.MARTLOCK])
        assert leido == sin_datos
        assert leido.venta_minima_fecha is None and not leido.tiene_orden_venta

    async def test_un_precio_nuevo_reemplaza_al_anterior(self, repo):
        await repo.save_many([precio(Ciudad.LYMHURST, venta=100_000)])
        nuevo = precio(Ciudad.LYMHURST, venta=80_000, hace=timedelta(minutes=5))
        await repo.save_many([nuevo])
        assert await repo.get(ESPADA, [Ciudad.LYMHURST]) == [nuevo]

    async def test_sin_ciudades_no_devuelve_nada(self, repo):
        await repo.save_many([precio(Ciudad.LYMHURST, venta=1)])
        assert await repo.get(ESPADA, []) == []

    async def test_la_calidad_distingue_precios(self, repo):
        otra_calidad = replace(precio(Ciudad.LYMHURST, venta=5), objeto=replace(ESPADA, calidad=Calidad.NORMAL))
        await repo.save_many([precio(Ciudad.LYMHURST, venta=9), otra_calidad])
        assert [p.venta_minima for p in await repo.get(ESPADA, [Ciudad.LYMHURST])] == [9]


class TestSqliteSeguimientoRepository:
    @pytest.fixture
    def repo(self, db):
        return SqliteSeguimientoRepository(db)

    async def test_guarda_y_recupera_con_el_porcentaje_exacto(self, repo):
        guardado = await repo.save(Seguimiento(ESPADA, Ciudad.LYMHURST, porcentaje_minimo=Decimal("12.5")))
        leido = await repo.get_by_id(guardado.id)
        assert leido == guardado and leido.porcentaje_minimo == Decimal("12.5")

    async def test_solo_neto_minimo(self, repo):
        guardado = await repo.save(Seguimiento(BOLSA, neto_minimo=50_000))
        assert (await repo.get_by_id(guardado.id)).porcentaje_minimo is None

    async def test_guardar_uno_con_id_lo_actualiza(self, repo):
        seguimiento = await repo.save(Seguimiento(ESPADA, neto_minimo=1))
        seguimiento.activo = False
        await repo.save(seguimiento)
        assert await repo.list_activos() == []
        assert (await repo.get_by_id(seguimiento.id)).activo is False

    async def test_lista_solo_los_activos(self, repo):
        await repo.save(Seguimiento(ESPADA, neto_minimo=1))
        await repo.save(Seguimiento(BOLSA, neto_minimo=1, activo=False))
        assert [s.objeto for s in await repo.list_activos()] == [ESPADA]

    async def test_eliminarlo_borra_sus_alertas(self, db, repo):
        alertas = SqliteAlertaRepository(db)
        seguimiento = await repo.save(Seguimiento(ESPADA, neto_minimo=1))
        await alertas.save(Alerta(seguimiento.id, ESPADA, Ciudad.CAERLEON, TipoVenta.DIRECTA, 10, None, "x", AHORA))
        await repo.delete(seguimiento.id)
        assert await alertas.list_recientes() == []


class TestSqliteAlertaRepository:
    @pytest.fixture
    async def seguimiento_id(self, db):
        return (await SqliteSeguimientoRepository(db).save(Seguimiento(ESPADA, neto_minimo=1))).id

    @pytest.fixture
    def repo(self, db):
        return SqliteAlertaRepository(db)

    def alerta(self, seguimiento_id, minutos=0, neto_referencia=96_000):
        return Alerta(
            seguimiento_id, ESPADA, Ciudad.BLACK_MARKET, TipoVenta.DIRECTA, 115_200,
            neto_referencia, "Black Market paga 20.0% más", AHORA + timedelta(minutes=minutos),
        )

    async def test_guarda_y_recupera(self, repo, seguimiento_id):
        guardada = await repo.save(self.alerta(seguimiento_id, neto_referencia=None))
        assert guardada.id == 1
        assert await repo.list_recientes() == [guardada]

    async def test_la_ultima_es_la_mas_reciente_de_ese_seguimiento(self, db, repo, seguimiento_id):
        otro = (await SqliteSeguimientoRepository(db).save(Seguimiento(BOLSA, neto_minimo=1))).id
        await repo.save(self.alerta(seguimiento_id, minutos=0))
        ultima = await repo.save(self.alerta(seguimiento_id, minutos=30))
        await repo.save(self.alerta(otro, minutos=90))
        assert await repo.ultima_de(seguimiento_id) == ultima
        assert await repo.ultima_de(999) is None

    async def test_recientes_de_la_mas_nueva_a_la_mas_vieja_con_limite(self, repo, seguimiento_id):
        for minutos in (10, 30, 20):
            await repo.save(self.alerta(seguimiento_id, minutos=minutos))
        recientes = await repo.list_recientes(limite=2)
        assert [a.fecha - AHORA for a in recientes] == [timedelta(minutes=30), timedelta(minutes=20)]

    async def test_no_admite_alertas_de_un_seguimiento_inexistente(self, repo):
        with pytest.raises(sqlite3.IntegrityError):
            await repo.save(self.alerta(999))


class TestSqliteUsuarioRepository:
    @pytest.fixture
    def repo(self, db):
        return SqliteUsuarioRepository(db)

    async def test_guarda_y_busca_por_discord_id(self, repo):
        guardado = await repo.save(Usuario("1", "julio", "av1", Rol.ADMIN))
        assert guardado.id == 1
        assert await repo.get_by_discord_id("1") == guardado
        assert await repo.get_by_discord_id("2") is None

    async def test_guardar_otra_vez_actualiza_y_conserva_el_id(self, repo):
        primero = await repo.save(Usuario("2", "general", None, Rol.GENERAL))
        despues = await repo.save(Usuario("2", "nuevo nombre", "av2", Rol.ADMIN))
        assert despues.id == primero.id
        assert await repo.get_by_discord_id("2") == Usuario("2", "nuevo nombre", "av2", Rol.ADMIN, primero.id)
