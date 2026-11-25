from datetime import date, timedelta

import pytest

from src.alertas.application.listar_alertas_use_case import ListarAlertas
from src.alertas.domain.entities.alerta import Alerta
from src.balance.application.obtener_saldo_inicial_use_case import ObtenerSaldoInicial
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, SesionInvalida
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.mercado.application.obtener_nombres_objetos_use_case import ObtenerNombresObjetos
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.usuarios.application.iniciar_sesion_con_discord_use_case import IniciarSesionConDiscord
from src.usuarios.application.iniciar_sesion_use_case import IniciarSesion
from src.usuarios.domain.entities.identidad import IdentidadDiscord
from src.usuarios.domain.entities.usuario import Rol
from tests.application.fakes import (
    AlertaRepoMemoria,
    CatalogoMemoria,
    DirectorioRolesMemoria,
    ProveedorIdentidadFalso,
    SaldoRepoMemoria,
    UsuarioRepoMemoria,
)
from tests.domain.fixtures import AHORA, ESPADA


class TestObtenerNombresObjetos:
    async def test_devuelve_el_nombre_de_cada_identificador_una_sola_vez(self):
        catalogo = CatalogoMemoria([Objeto("T6_MAIN_SWORD", "Espada ancha del maestro", CategoriaObjeto.ARMA)])
        nombres = await ObtenerNombresObjetos(catalogo).ejecutar(
            ["T6_MAIN_SWORD", "T6_MAIN_SWORD", "T9_NADA"]
        )
        assert nombres == {"T6_MAIN_SWORD": "Espada ancha del maestro"}  # lo desconocido se omite

    async def test_sin_identificadores_no_hay_nombres(self):
        assert await ObtenerNombresObjetos(CatalogoMemoria([])).ejecutar([]) == {}


class TestObtenerSaldoInicial:
    async def test_devuelve_el_saldo_configurado(self):
        saldo = SaldoInicial(120_000_000, date(2026, 11, 25))
        assert await ObtenerSaldoInicial(SaldoRepoMemoria(saldo)).ejecutar() == saldo

    async def test_sin_configurar_no_existe(self):
        with pytest.raises(EntidadNoEncontrada):
            await ObtenerSaldoInicial(SaldoRepoMemoria()).ejecutar()


class TestListarAlertas:
    async def test_devuelve_las_mas_recientes_primero_y_respeta_el_limite(self):
        repo = AlertaRepoMemoria()
        for minutos in (10, 30, 20):
            await repo.save(
                Alerta(1, ESPADA, Ciudad.BLACK_MARKET, TipoVenta.DIRECTA, 1, None, "x", AHORA + timedelta(minutes=minutos))
            )
        recientes = await ListarAlertas(repo).ejecutar(limite=2)
        assert [a.fecha - AHORA for a in recientes] == [timedelta(minutes=30), timedelta(minutes=20)]


class TestIniciarSesionConDiscord:
    def setup_method(self):
        self.usuarios = UsuarioRepoMemoria()
        directorio = DirectorioRolesMemoria({"1": Rol.ADMIN})
        identidades = {
            "codigo-admin": IdentidadDiscord("1", "julio", "av1"),
            "codigo-intruso": IdentidadDiscord("99", "intruso", None),
        }
        self.caso = IniciarSesionConDiscord(
            ProveedorIdentidadFalso(identidades), IniciarSesion(self.usuarios, directorio)
        )

    async def test_un_codigo_valido_de_un_miembro_inicia_sesion(self):
        usuario = await self.caso.ejecutar("codigo-admin")
        assert (usuario.discord_id, usuario.nombre, usuario.rol) == ("1", "julio", Rol.ADMIN)
        assert self.usuarios.usuarios["1"] == usuario

    async def test_quien_no_es_del_gremio_no_entra_y_no_se_guarda(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar("codigo-intruso")
        assert self.usuarios.usuarios == {}

    async def test_un_codigo_rechazado_por_discord_no_inicia_sesion(self):
        with pytest.raises(SesionInvalida):
            await self.caso.ejecutar("codigo-falso")
