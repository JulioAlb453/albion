import os
from collections.abc import Mapping
from dataclasses import dataclass


class ErrorConfiguracion(ValueError):
    """Falta una variable de entorno o trae un valor inválido. Se detecta al arrancar."""


@dataclass(frozen=True)
class Configuracion:
    secreto_jwt: str
    ruta_db: str = "data/gremio.db"
    token_horas: int = 12
    frontend_url: str = "http://localhost:5173"
    api_publica_url: str = "http://localhost:8000"
    cors_origenes: tuple[str, ...] = ()
    intervalo_alertas_minutos: int = 15
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_bot_token: str = ""
    discord_guild_id: str = ""
    discord_rol_admin_id: str = ""
    discord_rol_general_id: str = ""
    discord_webhook_alertas: str = ""
    bot_clave: str = ""  # vacía: el bot de Discord no puede usar la API
    respaldos_dir: str = "respaldos"
    respaldos_conservar: int = 30  # cuántas copias diarias se guardan; 0 apaga las copias

    def __post_init__(self) -> None:
        if len(self.secreto_jwt) < 32:
            raise ErrorConfiguracion("GREMIO_JWT_SECRET debe tener al menos 32 caracteres")
        if self.bot_clave and len(self.bot_clave) < 32:
            raise ErrorConfiguracion("GREMIO_BOT_CLAVE debe tener al menos 32 caracteres")
        if self.respaldos_conservar < 0:
            raise ErrorConfiguracion("GREMIO_RESPALDOS_CONSERVAR no puede ser negativo")

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> "Configuracion":
        entorno = os.environ if entorno is None else entorno

        def texto(nombre: str, defecto: str = "") -> str:
            return entorno.get(f"GREMIO_{nombre}", defecto)

        def entero(nombre: str, defecto: int) -> int:
            try:
                return int(texto(nombre, str(defecto)))
            except ValueError:
                raise ErrorConfiguracion(f"GREMIO_{nombre} debe ser un número entero") from None

        por_defecto = cls.__dataclass_fields__
        return cls(
            secreto_jwt=texto("JWT_SECRET"),
            ruta_db=texto("DB", por_defecto["ruta_db"].default),
            token_horas=entero("TOKEN_HORAS", por_defecto["token_horas"].default),
            frontend_url=texto("FRONTEND_URL", por_defecto["frontend_url"].default),
            api_publica_url=texto("API_URL", por_defecto["api_publica_url"].default),
            cors_origenes=tuple(o.strip() for o in texto("CORS_ORIGENES").split(",") if o.strip()),
            intervalo_alertas_minutos=entero(
                "INTERVALO_ALERTAS_MINUTOS", por_defecto["intervalo_alertas_minutos"].default
            ),
            discord_client_id=texto("DISCORD_CLIENT_ID"),
            discord_client_secret=texto("DISCORD_CLIENT_SECRET"),
            discord_bot_token=texto("DISCORD_BOT_TOKEN"),
            discord_guild_id=texto("DISCORD_GUILD_ID"),
            discord_rol_admin_id=texto("DISCORD_ROL_ADMIN_ID"),
            discord_rol_general_id=texto("DISCORD_ROL_GENERAL_ID"),
            discord_webhook_alertas=texto("DISCORD_WEBHOOK_ALERTAS"),
            bot_clave=texto("BOT_CLAVE"),
            respaldos_dir=texto("RESPALDOS_DIR", por_defecto["respaldos_dir"].default),
            respaldos_conservar=entero("RESPALDOS_CONSERVAR", por_defecto["respaldos_conservar"].default),
        )
