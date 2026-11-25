import asyncio
from datetime import UTC, datetime

import pytest

from src.alertas.infrastructure.notificador_discord_webhook import NotificadorDiscordWebhook
from src.alertas.infrastructure.notificador_nulo import NotificadorNulo
from src.bootstrap.app import crear_app
from src.bootstrap.configuracion import Configuracion, ErrorConfiguracion
from src.bootstrap.planificador import ejecutar_periodicamente
from src.bootstrap.produccion import crear_contenedor
from src.core.infrastructure.reloj_sistema import RelojSistema
from src.mercado.infrastructure.albion_data_api_proveedor import AlbionDataApiProveedor
from src.usuarios.infrastructure.discord_directorio_roles import DirectorioRolesDiscord
from src.usuarios.infrastructure.discord_oauth_identidad import DiscordOAuthIdentidad
from tests.api.conftest import armar_contenedor

DISCORD = dict(
    discord_client_id="cid", discord_client_secret="csecret", discord_bot_token="bot",
    discord_guild_id="G", discord_rol_admin_id="RA", discord_rol_general_id="RG",
)


def config(**cambios):
    return Configuracion(secreto_jwt="s" * 32, api_publica_url="https://api.example", **(DISCORD | cambios))


async def esperar(condicion, limite=2.0):
    """Espera a que algo pase en segundo plano, sin dormir de más."""
    fin = asyncio.get_running_loop().time() + limite
    while not condicion():
        assert asyncio.get_running_loop().time() < fin, "no ocurrió a tiempo"
        await asyncio.sleep(0.005)


class TestPlanificador:
    async def test_corre_la_tarea_al_arrancar_y_despues_cada_intervalo(self):
        veces, detener = [], asyncio.Event()
        tarea = asyncio.create_task(ejecutar_periodicamente(lambda: _anotar(veces), 0.01, detener))
        await esperar(lambda: len(veces) >= 3)
        detener.set()
        await tarea

    async def test_corre_de_inmediato_sin_esperar_el_primer_intervalo(self):
        veces, detener = [], asyncio.Event()
        tarea = asyncio.create_task(ejecutar_periodicamente(lambda: _anotar(veces), 3600, detener))
        await esperar(lambda: len(veces) == 1)
        detener.set()
        await tarea

    async def test_una_falla_se_informa_y_no_mata_el_ciclo(self):
        veces, errores, detener = [], [], asyncio.Event()

        async def tarea_inestable():
            veces.append(1)
            if len(veces) == 1:
                raise ConnectionError("la API se cayó")

        tarea = asyncio.create_task(ejecutar_periodicamente(tarea_inestable, 0.01, detener, errores.append))
        await esperar(lambda: len(veces) >= 2)
        detener.set()
        await tarea
        assert [str(e) for e in errores] == ["la API se cayó"]

    async def test_se_detiene_enseguida_aunque_falte_mucho_para_el_siguiente_ciclo(self):
        detener = asyncio.Event()
        tarea = asyncio.create_task(ejecutar_periodicamente(lambda: _anotar([]), 3600, detener))
        await asyncio.sleep(0.02)
        detener.set()
        await asyncio.wait_for(tarea, timeout=1)


async def _anotar(lista):
    lista.append(1)


class TestAppConPlanificador:
    async def test_revisa_las_alertas_al_arrancar_y_se_detiene_al_cerrar(self):
        contenedor, *_ = armar_contenedor()
        llamadas = []

        class Revisor:
            async def ejecutar(self):
                llamadas.append(1)
                return type("R", (), {"alertas": [], "errores": ["Seguimiento 1: falló"]})()

        contenedor.revisar_alertas = Revisor()
        app = crear_app(contenedor, con_planificador=True)
        async with app.router.lifespan_context(app):
            await esperar(lambda: len(llamadas) >= 1)
        veces = len(llamadas)
        await asyncio.sleep(0.05)
        assert len(llamadas) == veces  # ya no corre después de cerrar la aplicación

    async def test_sin_planificador_no_revisa_nada(self):
        contenedor, *_ = armar_contenedor()
        llamadas = []
        contenedor.revisar_alertas = type("R", (), {"ejecutar": lambda self: llamadas.append(1)})()
        app = crear_app(contenedor)  # por defecto no arranca el planificador
        async with app.router.lifespan_context(app):
            await asyncio.sleep(0.05)
        assert llamadas == []


class TestProduccion:
    async def test_arma_el_contenedor_con_los_adaptadores_reales(self):
        contenedor = crear_contenedor(config())
        try:
            externos = contenedor.externos
            assert isinstance(externos.proveedor_precios, AlbionDataApiProveedor)
            assert isinstance(externos.directorio_roles, DirectorioRolesDiscord)
            assert isinstance(externos.proveedor_identidad, DiscordOAuthIdentidad)
            assert isinstance(externos.reloj, RelojSistema)
            assert isinstance(externos.notificador, NotificadorNulo)  # sin webhook no se avisa a Discord
            assert externos.reloj.ahora().tzinfo is not None
        finally:
            await contenedor.cerrar()

    async def test_con_webhook_las_alertas_van_a_discord(self):
        contenedor = crear_contenedor(config(discord_webhook_alertas="https://discord.com/api/webhooks/1/x"))
        try:
            assert isinstance(contenedor.externos.notificador, NotificadorDiscordWebhook)
        finally:
            await contenedor.cerrar()

    async def test_el_regreso_de_discord_apunta_a_la_url_publica(self):
        contenedor = crear_contenedor(config())
        try:
            url = contenedor.externos.proveedor_identidad.url_autorizacion("e")
            assert "https%3A%2F%2Fapi.example%2Fapi%2Fauth%2Fdiscord%2Fcallback" in url
        finally:
            await contenedor.cerrar()

    @pytest.mark.parametrize("falta, variable", [
        ("discord_client_id", "GREMIO_DISCORD_CLIENT_ID"),
        ("discord_client_secret", "GREMIO_DISCORD_CLIENT_SECRET"),
        ("discord_bot_token", "GREMIO_DISCORD_BOT_TOKEN"),
        ("discord_guild_id", "GREMIO_DISCORD_GUILD_ID"),
        ("discord_rol_admin_id", "GREMIO_DISCORD_ROL_ADMIN_ID"),
        ("discord_rol_general_id", "GREMIO_DISCORD_ROL_GENERAL_ID"),
    ])
    def test_avisa_al_arrancar_si_falta_algo_de_discord(self, falta, variable):
        with pytest.raises(ErrorConfiguracion, match=variable):
            crear_contenedor(config(**{falta: ""}))
