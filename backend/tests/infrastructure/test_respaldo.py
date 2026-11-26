import sqlite3
from datetime import timedelta

import pytest_asyncio

from src.core.infrastructure.database import Database
from src.core.infrastructure.respaldo_sqlite import RespaldoSqlite
from tests.application.fakes import RelojFijo


@pytest_asyncio.fixture
async def base(tmp_path):
    """Una base real en disco, con un dato que deben conservar las copias."""
    base = Database(tmp_path / "gremio.db")
    await base.abrir()
    async with base.sesion() as conn:
        await conn.execute("INSERT INTO saldo_inicial (id, monto, fecha) VALUES (1, 120000000, '2026-11-25')")
    yield base
    await base.cerrar()


def leer(ruta, sql):
    conexion = sqlite3.connect(ruta)
    try:
        return conexion.execute(sql).fetchall()
    finally:
        conexion.close()


def nombres(carpeta):
    return sorted(p.name for p in carpeta.iterdir())


async def test_crea_una_copia_completa_con_la_fecha_del_dia(base, tmp_path):
    carpeta = tmp_path / "respaldos"
    ruta = await RespaldoSqlite(base, carpeta, RelojFijo(), conservar=30).ejecutar()
    assert ruta == carpeta / "gremio-2026-11-25.db"
    assert leer(ruta, "SELECT monto FROM saldo_inicial") == [(120_000_000,)]
    assert leer(ruta, "PRAGMA integrity_check") == [("ok",)]


async def test_crea_la_carpeta_si_no_existe(base, tmp_path):
    carpeta = tmp_path / "a" / "b" / "respaldos"
    assert await RespaldoSqlite(base, carpeta, RelojFijo(), 30).ejecutar() is not None
    assert carpeta.is_dir()


async def test_hace_una_sola_copia_por_dia(base, tmp_path):
    respaldo = RespaldoSqlite(base, tmp_path / "r", RelojFijo(), 30)
    primera = await respaldo.ejecutar()
    contenido = primera.read_bytes()
    assert await respaldo.ejecutar() is None  # el planificador la intenta varias veces al día
    assert primera.read_bytes() == contenido and len(nombres(tmp_path / "r")) == 1


async def test_al_dia_siguiente_hace_otra(base, tmp_path):
    reloj = RelojFijo()
    respaldo = RespaldoSqlite(base, tmp_path / "r", reloj, 30)
    await respaldo.ejecutar()
    reloj._ahora += timedelta(days=1)
    assert (await respaldo.ejecutar()).name == "gremio-2026-11-26.db"
    assert nombres(tmp_path / "r") == ["gremio-2026-11-25.db", "gremio-2026-11-26.db"]


async def test_conserva_solo_las_mas_recientes(base, tmp_path):
    reloj = RelojFijo()
    respaldo = RespaldoSqlite(base, tmp_path / "r", reloj, conservar=3)
    for _ in range(5):
        await respaldo.ejecutar()
        reloj._ahora += timedelta(days=1)
    assert nombres(tmp_path / "r") == ["gremio-2026-11-27.db", "gremio-2026-11-28.db", "gremio-2026-11-29.db"]


async def test_no_toca_archivos_que_no_son_suyos(base, tmp_path):
    carpeta = tmp_path / "r"
    carpeta.mkdir()
    (carpeta / "notas.txt").write_text("a mano")
    (carpeta / "gremio-viejo.db").write_text("otra cosa")
    await RespaldoSqlite(base, carpeta, RelojFijo(), conservar=1).ejecutar()
    assert nombres(carpeta) == ["gremio-2026-11-25.db", "gremio-viejo.db", "notas.txt"]


async def test_un_resto_a_medias_de_un_corte_anterior_no_lo_bloquea(base, tmp_path):
    carpeta = tmp_path / "r"
    carpeta.mkdir()
    (carpeta / "gremio-2026-11-25.db.tmp").write_bytes(b"copia a medias")  # se apagó la PC a la mitad
    ruta = await RespaldoSqlite(base, carpeta, RelojFijo(), 30).ejecutar()
    assert leer(ruta, "SELECT monto FROM saldo_inicial") == [(120_000_000,)]
    assert nombres(carpeta) == ["gremio-2026-11-25.db"]  # y no deja el temporal


async def test_la_copia_no_cambia_si_despues_se_modifica_la_base(base, tmp_path):
    ruta = await RespaldoSqlite(base, tmp_path / "r", RelojFijo(), 30).ejecutar()
    async with base.sesion() as conn:
        await conn.execute("UPDATE saldo_inicial SET monto = 1")
    assert leer(ruta, "SELECT monto FROM saldo_inicial") == [(120_000_000,)]
