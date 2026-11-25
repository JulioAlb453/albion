import pytest_asyncio

from src.core.infrastructure.database import Database


@pytest_asyncio.fixture
async def db():
    """Base SQLite real, en memoria y con todas las migraciones aplicadas."""
    base = Database(":memory:")
    await base.abrir()
    yield base
    await base.cerrar()
