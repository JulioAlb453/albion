import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.infrastructure.notificador_discord_webhook import NotificadorDiscordWebhook
from src.core.domain.errors import ServicioExternoNoDisponible, SesionInvalida
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.usuarios.domain.entities.identidad import IdentidadDiscord
from src.usuarios.domain.entities.usuario import Rol
from src.usuarios.infrastructure.discord_directorio_roles import DirectorioRolesDiscord
from src.usuarios.infrastructure.discord_oauth_identidad import DiscordOAuthIdentidad
from tests.application.fakes import CatalogoMemoria
from tests.domain.fixtures import AHORA, ESPADA

REDIRECT = "https://api.test/api/auth/discord/callback"
V10 = "/api/v10"


def cliente(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://discord.com/api/v10")


def oauth(handler):
    return DiscordOAuthIdentidad(cliente(handler), "cid", "csecret", REDIRECT)


class Servidor:
    """Un Discord de mentira que apunta cada petición y responde lo configurado."""

    def __init__(self, token=None, perfil=None, revocar=None):
        self.llamadas = []
        self.token = token or httpx.Response(200, json={"access_token": "tok", "token_type": "Bearer", "scope": "identify"})
        self.perfil = perfil or httpx.Response(200, json={
            "id": "1", "username": "julio", "global_name": "Julio A", "avatar": "av1", "email": "secreto@correo.com",
        })
        self.revocar = revocar or httpx.Response(200, json={})

    def __call__(self, request):
        self.llamadas.append(request)
        return {f"{V10}/oauth2/token": self.token, f"{V10}/users/@me": self.perfil, f"{V10}/oauth2/token/revoke": self.revocar}[request.url.path]

    @property
    def rutas(self):
        return [r.url.path.removeprefix(V10) for r in self.llamadas]


class TestDiscordOAuth:
    def test_la_direccion_de_autorizacion_pide_solo_identify(self):
        url = oauth(Servidor()).url_autorizacion("estado123")
        partes = urlparse(url)
        assert (partes.scheme, partes.netloc, partes.path) == ("https", "discord.com", "/oauth2/authorize")
        assert parse_qs(partes.query) == {
            "client_id": ["cid"], "response_type": ["code"], "scope": ["identify"],
            "redirect_uri": [REDIRECT], "state": ["estado123"], "prompt": ["none"],
        }

    async def test_canjea_el_codigo_pide_la_identidad_y_revoca_el_token(self):
        servidor = Servidor()
        identidad = await oauth(servidor).identificar("abc")
        assert identidad == IdentidadDiscord("1", "Julio A", "av1")
        assert servidor.rutas == ["/oauth2/token", "/users/@me", "/oauth2/token/revoke"]
        canje = parse_qs(servidor.llamadas[0].content.decode())
        assert canje == {
            "client_id": ["cid"], "client_secret": ["csecret"], "grant_type": ["authorization_code"],
            "code": ["abc"], "redirect_uri": [REDIRECT],
        }
        assert servidor.llamadas[1].headers["authorization"] == "Bearer tok"
        assert parse_qs(servidor.llamadas[2].content.decode())["token"] == ["tok"]

    async def test_no_conserva_el_correo_aunque_discord_lo_devuelva(self):
        identidad = await oauth(Servidor()).identificar("abc")
        assert not hasattr(identidad, "email") and "secreto@correo.com" not in repr(identidad)

    async def test_sin_nombre_global_usa_el_usuario(self):
        perfil = httpx.Response(200, json={"id": "1", "username": "julio", "global_name": None, "avatar": None})
        assert await oauth(Servidor(perfil=perfil)).identificar("abc") == IdentidadDiscord("1", "julio", None)

    async def test_si_falla_la_revocacion_igual_entra(self):
        servidor = Servidor(revocar=httpx.Response(500))
        assert (await oauth(servidor).identificar("abc")).discord_id == "1"

    async def test_se_revoca_aunque_falle_la_lectura_del_perfil(self):
        servidor = Servidor(perfil=httpx.Response(500))
        with pytest.raises(ServicioExternoNoDisponible):
            await oauth(servidor).identificar("abc")
        assert servidor.rutas[-1] == "/oauth2/token/revoke"

    async def test_un_codigo_rechazado_no_sigue_adelante(self):
        servidor = Servidor(token=httpx.Response(400, json={"error": "invalid_grant"}))
        with pytest.raises(SesionInvalida):
            await oauth(servidor).identificar("viejo")
        assert servidor.rutas == ["/oauth2/token"]

    @pytest.mark.parametrize("respuesta", [httpx.Response(503), httpx.Response(429)])
    async def test_discord_con_problemas_se_informa(self, respuesta):
        with pytest.raises(ServicioExternoNoDisponible):
            await oauth(Servidor(token=respuesta)).identificar("abc")

    async def test_un_fallo_de_red_se_informa(self):
        def handler(request):
            raise httpx.ConnectError("sin red", request=request)

        with pytest.raises(ServicioExternoNoDisponible, match="no respondió"):
            await oauth(handler).identificar("abc")


def directorio(handler):
    return DirectorioRolesDiscord(cliente(handler), "bot-token", "G", rol_admin_id="RA", rol_general_id="RG")


def miembro(roles):
    return lambda request: httpx.Response(200, json={"roles": roles, "user": {"id": "1"}})


class TestDirectorioRolesDiscord:
    @pytest.mark.parametrize(
        "roles, esperado",
        [(["RA"], Rol.ADMIN), (["x", "RG"], Rol.GENERAL), (["RG", "RA"], Rol.ADMIN), (["otro"], None), ([], None)],
    )
    async def test_el_rol_sale_de_los_roles_del_servidor(self, roles, esperado):
        assert await directorio(miembro(roles)).rol_de("1") == esperado

    async def test_consulta_al_miembro_con_el_token_del_bot(self):
        vistas = []

        def handler(request):
            vistas.append(request)
            return httpx.Response(200, json={"roles": []})

        await directorio(handler).rol_de("42")
        assert vistas[0].url.path == f"{V10}/guilds/G/members/42"
        assert vistas[0].headers["authorization"] == "Bot bot-token"

    async def test_quien_no_esta_en_el_servidor_no_tiene_rol(self):
        assert await directorio(lambda r: httpx.Response(404, json={"code": 10007})).rol_de("1") is None

    async def test_un_servidor_mal_configurado_no_se_confunde_con_un_miembro_ausente(self):
        with pytest.raises(ServicioExternoNoDisponible, match="GREMIO_DISCORD_GUILD_ID"):
            await directorio(lambda r: httpx.Response(404, json={"code": 10004})).rol_de("1")

    @pytest.mark.parametrize("estado", [401, 403, 500])
    async def test_otros_errores_se_informan_y_no_dejan_entrar(self, estado):
        with pytest.raises(ServicioExternoNoDisponible, match=str(estado)):
            await directorio(lambda r: httpx.Response(estado)).rol_de("1")


WEBHOOK = "https://discord.com/api/webhooks/1/abc"


def alerta(**cambios):
    datos = dict(
        seguimiento_id=1, objeto=ESPADA, ciudad=Ciudad.BLACK_MARKET, tipo=TipoVenta.DIRECTA,
        neto_unitario=144_000, neto_referencia=93_500, motivo="Black Market paga 54.0% más neto que Fort Sterling",
        fecha=AHORA,
    )
    return Alerta(**(datos | cambios))


CATALOGO = CatalogoMemoria([Objeto("T6_MAIN_SWORD", "Espada ancha del maestro", CategoriaObjeto.ARMA)])


class TestNotificadorDiscordWebhook:
    async def test_publica_un_mensaje_claro_sin_mencionar_a_nadie(self):
        vistas = []

        def handler(request):
            vistas.append(request)
            return httpx.Response(204)

        await NotificadorDiscordWebhook(cliente(handler), WEBHOOK, CATALOGO).notificar(alerta())
        [peticion] = vistas
        assert str(peticion.url) == WEBHOOK and peticion.method == "POST"
        cuerpo = json.loads(peticion.content)
        for texto in ("Espada ancha del maestro", "T6.2", "Sobresaliente", "Black Market", "144,000", "93,500", "Fort Sterling"):
            assert texto in cuerpo["content"], texto
        assert cuerpo["allowed_mentions"] == {"parse": []}  # un @everyone en un nombre no avisa a nadie

    async def test_un_objeto_fuera_del_catalogo_se_muestra_por_su_identificador(self):
        vistas = []
        notificador = NotificadorDiscordWebhook(
            cliente(lambda r: vistas.append(r) or httpx.Response(204)), WEBHOOK, CatalogoMemoria([])
        )
        await notificador.notificar(alerta(neto_referencia=None))
        assert "T6_MAIN_SWORD" in json.loads(vistas[0].content)["content"]

    @pytest.mark.parametrize("respuesta", [httpx.Response(429), httpx.Response(404), httpx.Response(500)])
    async def test_si_discord_rechaza_el_aviso_se_informa(self, respuesta):
        with pytest.raises(ServicioExternoNoDisponible):
            await NotificadorDiscordWebhook(cliente(lambda r: respuesta), WEBHOOK, CATALOGO).notificar(alerta())

    async def test_un_fallo_de_red_se_informa(self):
        def handler(request):
            raise httpx.ReadTimeout("lento", request=request)

        with pytest.raises(ServicioExternoNoDisponible):
            await NotificadorDiscordWebhook(cliente(handler), WEBHOOK, CATALOGO).notificar(alerta())
