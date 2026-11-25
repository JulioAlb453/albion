import pytest

from src.core.domain.errors import AccesoDenegado
from src.usuarios.application.iniciar_sesion_use_case import IniciarSesion
from src.usuarios.domain.entities.usuario import Rol
from tests.application.fakes import DirectorioRolesMemoria, UsuarioRepoMemoria


class TestIniciarSesion:
    def setup_method(self):
        self.usuarios = UsuarioRepoMemoria()
        self.directorio = DirectorioRolesMemoria({"1": Rol.ADMIN, "2": Rol.GENERAL})
        self.caso = IniciarSesion(self.usuarios, self.directorio)

    async def test_el_admin_entra_con_su_rol(self):
        usuario = await self.caso.ejecutar("1", "julio", "av1")
        assert (usuario.rol, usuario.puede_registrar) == (Rol.ADMIN, True)
        assert self.usuarios.usuarios["1"] == usuario

    async def test_un_general_entra_sin_poder_registrar(self):
        usuario = await self.caso.ejecutar("2", "general", None)
        assert (usuario.rol, usuario.puede_registrar) == (Rol.GENERAL, False)

    async def test_quien_no_tiene_rol_del_gremio_no_entra_ni_se_guarda(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar("99", "intruso", None)
        assert self.usuarios.usuarios == {}

    async def test_actualiza_nombre_y_rol_conservando_el_id(self):
        primero = await self.caso.ejecutar("2", "general", None)
        self.directorio.roles["2"] = Rol.ADMIN
        despues = await self.caso.ejecutar("2", "nuevo nombre", "av2")
        assert despues.id == primero.id
        assert (despues.nombre, despues.avatar_hash, despues.rol) == ("nuevo nombre", "av2", Rol.ADMIN)
        assert len(self.usuarios.usuarios) == 1
