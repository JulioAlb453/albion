import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from src.core.infrastructure.migraciones import MIGRACIONES


class Database:
    """Una conexión SQLite y un candado.

    Toda operación, de lectura o de escritura, pasa por `sesion()`: una sola a la vez, y todo lo
    que se hace dentro se confirma junto o se descarta junto. Así dos peticiones concurrentes
    nunca mezclan sus transacciones sobre la misma conexión. No se anidan: dentro de una sesión
    se usa la conexión recibida, no se abre otra sesión.
    """

    def __init__(self, ruta: str | Path):
        self._ruta = str(ruta)
        self._conn: aiosqlite.Connection | None = None
        self._candado = asyncio.Lock()

    async def abrir(self) -> None:
        self._conn = await aiosqlite.connect(self._ruta)
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._migrar(self._conn)

    async def cerrar(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @asynccontextmanager
    async def sesion(self) -> AsyncIterator[aiosqlite.Connection]:
        if self._conn is None:
            raise RuntimeError("La base de datos no está abierta: llama a abrir() primero")
        async with self._candado:
            try:
                yield self._conn
            except BaseException:
                await self._conn.rollback()
                raise
            await self._conn.commit()

    @staticmethod
    async def _migrar(conn: aiosqlite.Connection) -> None:
        async with conn.execute("PRAGMA user_version") as cursor:
            (version,) = await cursor.fetchone()
        for script in MIGRACIONES[version:]:
            try:
                await conn.executescript(script)
            except BaseException:
                await conn.rollback()
                raise
