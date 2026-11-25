from datetime import date

from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.domain.ports.i_saldo_inicial_repository import ISaldoInicialRepository
from src.core.infrastructure.database import Database


class SqliteSaldoInicialRepository(ISaldoInicialRepository):
    """El saldo inicial es único: vive siempre en la fila con id 1."""

    def __init__(self, db: Database):
        self._db = db

    async def get(self) -> SaldoInicial | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute("SELECT monto, fecha FROM saldo_inicial WHERE id = 1")
            fila = await cursor.fetchone()
        return None if fila is None else SaldoInicial(fila[0], date.fromisoformat(fila[1]))

    async def save(self, saldo: SaldoInicial) -> SaldoInicial:
        async with self._db.sesion() as conn:
            await conn.execute(
                "INSERT INTO saldo_inicial (id, monto, fecha) VALUES (1, ?, ?) "
                "ON CONFLICT (id) DO UPDATE SET monto = excluded.monto, fecha = excluded.fecha",
                (saldo.monto, saldo.fecha.isoformat()),
            )
        return saldo
