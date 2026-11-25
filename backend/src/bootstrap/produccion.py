"""Arma la aplicación real: base SQLite en disco, Discord de verdad y la API de Albion."""

from pathlib import Path

import httpx

from src.alertas.infrastructure.notificador_discord_webhook import NotificadorDiscordWebhook
from src.alertas.infrastructure.notificador_nulo import NotificadorNulo
from src.bootstrap.app import crear_app
from src.bootstrap.configuracion import Configuracion, ErrorConfiguracion
from src.bootstrap.contenedor import Contenedor, Externos
from src.core.infrastructure.database import Database
from src.core.infrastructure.reloj_sistema import RelojSistema
from src.mercado.infrastructure.albion_data_api_proveedor import (
    AGENTE,
    AlbionDataApiProveedor,
    crear_cliente_albion,
)
from src.mercado.infrastructure.sqlite_catalogo_objetos import SqliteCatalogoObjetos
from src.usuarios.infrastructure.discord_directorio_roles import DirectorioRolesDiscord
from src.usuarios.infrastructure.discord_oauth_identidad import DiscordOAuthIdentidad

_API_DISCORD = "https://discord.com/api/v10"
_VARIABLES_DISCORD = {
    "discord_client_id": "GREMIO_DISCORD_CLIENT_ID",
    "discord_client_secret": "GREMIO_DISCORD_CLIENT_SECRET",
    "discord_bot_token": "GREMIO_DISCORD_BOT_TOKEN",
    "discord_guild_id": "GREMIO_DISCORD_GUILD_ID",
    "discord_rol_admin_id": "GREMIO_DISCORD_ROL_ADMIN_ID",
    "discord_rol_general_id": "GREMIO_DISCORD_ROL_GENERAL_ID",
}


def _verificar_discord(config: Configuracion) -> None:
    faltan = [variable for campo, variable in _VARIABLES_DISCORD.items() if not getattr(config, campo)]
    if faltan:
        raise ErrorConfiguracion("Faltan variables de Discord: " + ", ".join(faltan))


def crear_contenedor(config: Configuracion) -> Contenedor:
    _verificar_discord(config)
    cliente_albion = crear_cliente_albion()
    cliente_discord = httpx.AsyncClient(
        base_url=_API_DISCORD, timeout=15.0, headers={"User-Agent": AGENTE}
    )
    db = Database(config.ruta_db)
    if config.discord_webhook_alertas:
        notificador = NotificadorDiscordWebhook(
            cliente_discord, config.discord_webhook_alertas, SqliteCatalogoObjetos(db)
        )
    else:
        notificador = NotificadorNulo()
    externos = Externos(
        proveedor_precios=AlbionDataApiProveedor(cliente_albion),
        directorio_roles=DirectorioRolesDiscord(
            cliente_discord, config.discord_bot_token, config.discord_guild_id,
            config.discord_rol_admin_id, config.discord_rol_general_id,
        ),
        proveedor_identidad=DiscordOAuthIdentidad(
            cliente_discord, config.discord_client_id, config.discord_client_secret,
            f"{config.api_publica_url}/api/auth/discord/callback",
        ),
        notificador=notificador,
        reloj=RelojSistema(),
    )
    return Contenedor(config, db, externos, recursos=[cliente_albion, cliente_discord])


def crear_app_desde_entorno():
    """Para uvicorn: `uvicorn src.bootstrap.produccion:crear_app_desde_entorno --factory`."""
    config = Configuracion.desde_entorno()
    Path(config.ruta_db).parent.mkdir(parents=True, exist_ok=True)
    return crear_app(crear_contenedor(config), con_planificador=True)
