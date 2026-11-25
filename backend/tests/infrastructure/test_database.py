from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto, desde_texto
from src.core.infrastructure.migraciones import MIGRACIONES

TABLAS = {
    "ventas", "gastos", "saldo_inicial", "precios_mercado",
    "seguimientos", "alertas", "usuarios", "catalogo_objetos",
}


async def consultar(db, sql, *params):
    async with db.sesion() as conn:
        return await (await conn.execute(sql, params)).fetchall()


class TestDatabase:
    async def test_aplica_todas_las_migraciones(self, db):
        [(version,)] = await consultar(db, "PRAGMA user_version")
        assert version == len(MIGRACIONES)
        tablas = {fila[0] for fila in await consultar(db, "SELECT name FROM sqlite_master WHERE type='table'")}
        assert TABLAS <= tablas

    async def test_las_claves_foraneas_estan_activas(self, db):
        assert await consultar(db, "PRAGMA foreign_keys") == [(1,)]

    async def test_reabrir_conserva_los_datos_y_no_repite_migraciones(self, tmp_path):
        ruta = tmp_path / "gremio.db"
        primera = Database(ruta)
        await primera.abrir()
        async with primera.sesion() as conn:
            await conn.execute("INSERT INTO saldo_inicial (id, monto, fecha) VALUES (1, 120, '2026-11-25')")
        await primera.cerrar()

        segunda = Database(ruta)
        await segunda.abrir()
        try:
            assert await consultar(segunda, "SELECT monto FROM saldo_inicial") == [(120,)]
        finally:
            await segunda.cerrar()

    async def test_si_la_sesion_falla_no_se_guarda_nada(self, db):
        with pytest.raises(RuntimeError):
            async with db.sesion() as conn:
                await conn.execute("INSERT INTO saldo_inicial (id, monto, fecha) VALUES (1, 1, 'x')")
                raise RuntimeError("falla a mitad")
        assert await consultar(db, "SELECT * FROM saldo_inicial") == []

    async def test_usarla_cerrada_da_un_error_claro(self):
        with pytest.raises(RuntimeError, match="abrir"):
            async with Database(":memory:").sesion():
                pass


class TestFechasSql:
    def test_ida_y_vuelta(self):
        fecha = datetime(2026, 11, 25, 12, 30, 5, 123, tzinfo=UTC)
        assert desde_texto(a_texto(fecha)) == fecha

    def test_el_texto_ordena_igual_que_el_tiempo_aunque_vengan_con_otra_zona(self):
        mexico = timezone(timedelta(hours=-6))
        fechas = [
            datetime(2026, 11, 25, 9, tzinfo=mexico),   # 15:00 UTC
            datetime(2026, 11, 25, 14, tzinfo=UTC),
            datetime(2026, 11, 25, 12, 0, 0, 5, tzinfo=UTC),
        ]
        assert sorted(fechas, key=a_texto) == sorted(fechas)

    def test_una_fecha_sin_zona_se_guarda_como_utc(self):
        assert a_texto(datetime(2026, 11, 25, 12)) == a_texto(datetime(2026, 11, 25, 12, tzinfo=UTC))
