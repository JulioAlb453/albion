from urllib.parse import quote

import pytest

from src.usuarios.domain.entities.usuario import Rol
from tests.api.conftest import CLAVE_BOT, montar_entorno

VENTA = {
    "base_id": "T6_MAIN_SWORD", "encantamiento": 2, "calidad": 4, "ciudad": "Lymhurst",
    "tipo": "directa", "cantidad": 1, "precio_unitario": 100_000,
}


def del_bot(discord_id="1", nombre="Julio", **cambios):
    """Los encabezados con los que el bot pide algo en nombre de quien usó el comando."""
    base = {"X-Bot-Clave": CLAVE_BOT, "X-Discord-Id": discord_id, "X-Discord-Nombre": quote(nombre)}
    return {**base, **cambios}


class TestElBotActuaComoQuienLoUsa:
    async def test_un_admin_registra_una_venta_a_traves_del_bot(self, entorno):
        respuesta = await entorno.cliente.post("/api/ventas", json=VENTA, headers=del_bot("1"))
        assert respuesta.status_code == 201 and respuesta.json()["neto"] == 96_000

    async def test_un_general_consulta_pero_no_puede_registrar(self, entorno):
        assert (await entorno.cliente.get("/api/ventas", headers=del_bot("2"))).status_code == 200
        assert (await entorno.cliente.post("/api/ventas", json=VENTA, headers=del_bot("2"))).status_code == 403

    async def test_quien_no_tiene_rol_del_gremio_no_pasa_por_el_bot(self, entorno):
        respuesta = await entorno.cliente.get("/api/ventas", headers=del_bot("99"))
        assert respuesta.status_code == 403

    async def test_el_rol_se_consulta_en_cada_peticion(self, entorno):
        assert (await entorno.cliente.post("/api/ventas", json=VENTA, headers=del_bot("1"))).status_code == 201
        entorno.contenedor.externos.directorio_roles.roles["1"] = Rol.GENERAL  # le quitan el rol de admin
        assert (await entorno.cliente.post("/api/ventas", json=VENTA, headers=del_bot("1"))).status_code == 403
        del entorno.contenedor.externos.directorio_roles.roles["1"]  # y luego el del gremio
        assert (await entorno.cliente.get("/api/ventas", headers=del_bot("1"))).status_code == 403

    async def test_guarda_el_nombre_aunque_tenga_tildes(self, entorno):
        await entorno.cliente.get("/api/ventas", headers=del_bot("1", nombre="Julio Ávila"))
        assert (await entorno.contenedor.usuarios.get_by_discord_id("1")).nombre == "Julio Ávila"


class TestLaClaveDelBot:
    async def test_una_clave_equivocada_no_entra(self, entorno):
        respuesta = await entorno.cliente.get("/api/ventas", headers=del_bot(**{"X-Bot-Clave": "x" * 32}))
        assert respuesta.status_code == 401

    async def test_sin_clave_configurada_el_bot_no_puede_entrar_con_ninguna(self):
        async with montar_entorno(bot_clave="") as sin_bot:
            assert (await sin_bot.cliente.get("/api/ventas", headers=del_bot())).status_code == 401
            assert (await sin_bot.cliente.get("/api/ventas", headers=del_bot(**{"X-Bot-Clave": ""}))).status_code == 401

    @pytest.mark.parametrize("id_", ["", "abc", "12 3", "1; DROP"])
    async def test_sin_un_id_de_discord_valido_no_entra(self, entorno, id_):
        assert (await entorno.cliente.get("/api/ventas", headers=del_bot(id_))).status_code == 401

    async def test_falta_el_id(self, entorno):
        encabezados = {"X-Bot-Clave": CLAVE_BOT}
        assert (await entorno.cliente.get("/api/ventas", headers=encabezados)).status_code == 401

    async def test_la_clave_no_vale_si_la_peticion_llego_por_internet(self, entorno):
        # ngrok agrega X-Forwarded-For; el bot habla directo con la API y nunca lo lleva.
        respuesta = await entorno.cliente.get("/api/ventas", headers=del_bot(**{"X-Forwarded-For": "203.0.113.9"}))
        assert respuesta.status_code == 401
        assert "red interna" in respuesta.json()["detail"]

    async def test_el_inicio_de_sesion_normal_sigue_funcionando(self, entorno):
        assert (await entorno.cliente.get("/api/ventas", headers=await entorno.encabezados())).status_code == 200
