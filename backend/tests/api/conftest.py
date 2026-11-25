from dataclasses import dataclass

import httpx
import pytest_asyncio

from src.bootstrap.app import crear_app
from src.bootstrap.configuracion import Configuracion
from src.bootstrap.contenedor import Contenedor, Externos
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.infrastructure.database import Database
from src.usuarios.domain.entities.identidad import IdentidadDiscord
from src.usuarios.domain.entities.usuario import Rol, Usuario
from tests.application.fakes import (
    DirectorioRolesMemoria,
    NotificadorMemoria,
    ProveedorIdentidadFalso,
    ProveedorPreciosFalso,
    RelojFijo,
)
from tests.domain.fixtures import precio

FRONTEND = "https://gremio.test/app"
PRECIOS = [
    precio(Ciudad.FORT_STERLING, venta=100_000, compra=90_000),
    precio(Ciudad.BLACK_MARKET, compra=150_000),
    precio(Ciudad.CAERLEON, venta=120_000),
]


@dataclass
class Entorno:
    """La aplicación completa con una base real en memoria y dobles solo para lo externo."""

    cliente: httpx.AsyncClient
    contenedor: Contenedor
    precios: ProveedorPreciosFalso
    notificador: NotificadorMemoria
    identidad: ProveedorIdentidadFalso
    reloj: RelojFijo

    async def encabezados(self, rol: Rol = Rol.ADMIN) -> dict[str, str]:
        """Encabezados de un usuario ya registrado con ese rol."""
        usuario = await self.contenedor.usuarios.save(
            Usuario("1" if rol is Rol.ADMIN else "2", rol.value, None, rol)
        )
        return {"Authorization": f"Bearer {self.contenedor.emisor_tokens.emitir_sesion(usuario)}"}


def armar_contenedor() -> tuple[Contenedor, ProveedorPreciosFalso, NotificadorMemoria, ProveedorIdentidadFalso, RelojFijo]:
    """Un contenedor real, con la base en memoria sin abrir y dobles para lo externo."""
    config = Configuracion(
        secreto_jwt="s" * 32,
        ruta_db=":memory:",
        frontend_url=FRONTEND,
        api_publica_url="https://api.test",
        cors_origenes=("https://gremio.test",),
    )
    reloj = RelojFijo()
    precios = ProveedorPreciosFalso(PRECIOS)
    notificador = NotificadorMemoria()
    identidad = ProveedorIdentidadFalso(
        {
            "codigo-admin": IdentidadDiscord("1", "julio", "av1"),
            "codigo-general": IdentidadDiscord("2", "general", None),
            "codigo-intruso": IdentidadDiscord("99", "intruso", None),
        }
    )
    externos = Externos(
        proveedor_precios=precios,
        directorio_roles=DirectorioRolesMemoria({"1": Rol.ADMIN, "2": Rol.GENERAL}),
        proveedor_identidad=identidad,
        notificador=notificador,
        reloj=reloj,
    )
    return Contenedor(config, Database(":memory:"), externos), precios, notificador, identidad, reloj


@pytest_asyncio.fixture
async def entorno():
    contenedor, precios, notificador, identidad, reloj = armar_contenedor()
    app = crear_app(contenedor)
    async with app.router.lifespan_context(app):
        transporte = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transporte, base_url="https://api.test") as cliente:
            yield Entorno(cliente, contenedor, precios, notificador, identidad, reloj)
