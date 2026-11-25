from urllib.parse import parse_qs, urlparse

from src.usuarios.domain.entities.usuario import Rol
from tests.api.conftest import FRONTEND


async def iniciar(entorno):
    """Da el paso 1 del flujo (login) y devuelve el `state` que Discord reenviaría."""
    respuesta = await entorno.cliente.get("/api/auth/discord/login")
    assert respuesta.status_code == 307
    return parse_qs(urlparse(respuesta.headers["location"]).query)["state"][0]


async def volver(entorno, codigo, estado=None):
    estado = estado or await iniciar(entorno)
    respuesta = await entorno.cliente.get(
        "/api/auth/discord/callback", params={"code": codigo, "state": estado}
    )
    assert respuesta.status_code == 307
    return respuesta.headers["location"]


async def test_salud_no_pide_sesion(entorno):
    respuesta = await entorno.cliente.get("/api/salud")
    assert (respuesta.status_code, respuesta.json()) == (200, {"estado": "ok"})


class TestSesion:
    async def test_sin_token_no_entra(self, entorno):
        respuesta = await entorno.cliente.get("/api/auth/yo")
        assert respuesta.status_code == 401
        assert respuesta.headers["www-authenticate"] == "Bearer"

    async def test_con_token_devuelve_el_usuario(self, entorno):
        respuesta = await entorno.cliente.get("/api/auth/yo", headers=await entorno.encabezados(Rol.ADMIN))
        assert respuesta.json() == {
            "discord_id": "1", "nombre": "admin", "avatar_hash": None,
            "rol": "admin", "puede_registrar": True,
        }

    async def test_un_general_no_puede_registrar(self, entorno):
        respuesta = await entorno.cliente.get("/api/auth/yo", headers=await entorno.encabezados(Rol.GENERAL))
        assert respuesta.json()["puede_registrar"] is False

    async def test_un_token_falso_no_entra(self, entorno):
        respuesta = await entorno.cliente.get("/api/auth/yo", headers={"Authorization": "Bearer basura"})
        assert respuesta.status_code == 401

    async def test_un_esquema_distinto_de_bearer_no_entra(self, entorno):
        encabezados = await entorno.encabezados()
        token = encabezados["Authorization"].split()[1]
        respuesta = await entorno.cliente.get("/api/auth/yo", headers={"Authorization": f"Basic {token}"})
        assert respuesta.status_code == 401

    async def test_un_token_valido_de_alguien_que_ya_no_existe_no_entra(self, entorno):
        from src.usuarios.domain.entities.usuario import Usuario

        fantasma = Usuario("777", "fantasma", None, Rol.ADMIN)  # nunca se guardó
        token = entorno.contenedor.emisor_tokens.emitir_sesion(fantasma)
        respuesta = await entorno.cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})
        assert respuesta.status_code == 401


class TestDiscord:
    async def test_el_login_manda_a_discord_con_un_estado_firmado(self, entorno):
        respuesta = await entorno.cliente.get("/api/auth/discord/login")
        destino = respuesta.headers["location"]
        assert destino.startswith("https://discord.test/authorize?state=")
        entorno.contenedor.emisor_tokens.verificar_estado(parse_qs(urlparse(destino).query)["state"][0])

    async def test_un_miembro_vuelve_al_frontend_con_su_token_en_el_fragmento(self, entorno):
        destino = await volver(entorno, "codigo-admin")
        assert destino.startswith(f"{FRONTEND}#token=")  # el fragmento no llega a servidores ni logs
        token = destino.split("#token=")[1]
        assert entorno.contenedor.emisor_tokens.verificar_sesion(token) == "1"
        assert (await entorno.contenedor.usuarios.get_by_discord_id("1")).rol is Rol.ADMIN

    async def test_quien_no_es_del_gremio_vuelve_con_un_error_y_no_se_guarda(self, entorno):
        assert await volver(entorno, "codigo-intruso") == f"{FRONTEND}#error=sin_acceso"
        assert await entorno.contenedor.usuarios.get_by_discord_id("99") is None

    async def test_un_codigo_rechazado_vuelve_con_error(self, entorno):
        assert await volver(entorno, "codigo-falso") == f"{FRONTEND}#error=codigo_invalido"

    async def test_un_estado_falso_ni_siquiera_llama_a_discord(self, entorno):
        entorno.identidad.caido = True  # si se llamara, el error sería otro
        assert await volver(entorno, "codigo-admin", estado="falso") == f"{FRONTEND}#error=estado_invalido"

    async def test_si_la_persona_cancela_en_discord_vuelve_con_un_aviso(self, entorno):
        respuesta = await entorno.cliente.get(
            "/api/auth/discord/callback", params={"error": "access_denied"}
        )
        assert respuesta.headers["location"] == f"{FRONTEND}#error=cancelado"

    async def test_el_motivo_de_un_fallo_de_discord_queda_en_el_log_del_servidor(self, entorno, caplog):
        entorno.identidad.caido = True
        with caplog.at_level("WARNING", logger="gremio.auth"):
            await volver(entorno, "codigo-admin")
        assert "Discord no responde" in caplog.text

    async def test_un_rechazo_por_falta_de_rol_tambien_se_registra_sin_datos_personales(self, entorno, caplog):
        with caplog.at_level("WARNING", logger="gremio.auth"):
            await volver(entorno, "codigo-intruso")
        assert "sin rol del gremio" in caplog.text
        assert "99" not in caplog.text and "intruso" not in caplog.text

    async def test_discord_caido_vuelve_con_error(self, entorno):
        entorno.identidad.caido = True
        assert await volver(entorno, "codigo-admin") == f"{FRONTEND}#error=discord_no_disponible"


class TestCors:
    async def test_permite_al_frontend_configurado(self, entorno):
        respuesta = await entorno.cliente.options(
            "/api/salud",
            headers={"Origin": "https://gremio.test", "Access-Control-Request-Method": "GET"},
        )
        assert respuesta.headers["access-control-allow-origin"] == "https://gremio.test"

    async def test_no_permite_otros_origenes(self, entorno):
        respuesta = await entorno.cliente.options(
            "/api/salud",
            headers={"Origin": "https://malo.test", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" not in respuesta.headers
