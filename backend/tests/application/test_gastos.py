from datetime import UTC, datetime

import pytest

from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, ErrorDominio
from src.gastos.application.datos_gasto import DatosGasto
from src.gastos.application.eliminar_gasto_use_case import EliminarGasto
from src.gastos.application.importar_gastos_use_case import ImportarGastos
from src.gastos.application.listar_gastos_use_case import ListarGastos
from src.gastos.application.registrar_gasto_use_case import RegistrarGasto
from src.gastos.domain.entities.gasto import CategoriaGasto
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos
from tests.application.fakes import ADMIN, GENERAL, GastoRepoMemoria, RelojFijo
from tests.domain.fixtures import AHORA


def datos(**cambios):
    base = dict(categoria=CategoriaGasto.REPARACIONES, descripcion="  ZvZ  ", monto=500_000)
    return DatosGasto(**(base | cambios))


class TestRegistrarGasto:
    def setup_method(self):
        self.repo = GastoRepoMemoria()
        self.caso = RegistrarGasto(self.repo, RelojFijo())

    async def test_guarda_con_fecha_del_reloj_y_descripcion_limpia(self):
        gasto = await self.caso.ejecutar(ADMIN, datos())
        assert (gasto.id, gasto.fecha, gasto.descripcion) == (1, AHORA, "ZvZ")
        assert self.repo.items == {1: gasto}

    async def test_normaliza_la_fecha_a_utc(self):
        gasto = await self.caso.ejecutar(ADMIN, datos(fecha=datetime(2026, 11, 24, 18)))
        assert gasto.fecha == datetime(2026, 11, 24, 18, tzinfo=UTC)

    async def test_un_general_no_puede_registrar(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, datos())
        assert self.repo.items == {}

    @pytest.mark.parametrize(
        "cambios", [dict(monto=0), dict(categoria=CategoriaGasto.OTROS, descripcion=" ")]
    )
    async def test_una_regla_de_dominio_impide_guardar(self, cambios):
        with pytest.raises(ErrorDominio):
            await self.caso.ejecutar(ADMIN, datos(**cambios))
        assert self.repo.items == {}


class TestListarGastos:
    async def test_filtra_por_categoria(self):
        repo = GastoRepoMemoria()
        registrar = RegistrarGasto(repo, RelojFijo())
        await registrar.ejecutar(ADMIN, datos())
        await registrar.ejecutar(ADMIN, datos(categoria=CategoriaGasto.COMPRA_EQUIPO))
        gastos = await ListarGastos(repo).ejecutar(
            FiltroGastos(categoria=CategoriaGasto.COMPRA_EQUIPO)
        )
        assert [g.categoria for g in gastos] == [CategoriaGasto.COMPRA_EQUIPO]

    async def test_acepta_fechas_sin_zona_en_el_filtro(self):
        repo = GastoRepoMemoria()
        await RegistrarGasto(repo, RelojFijo()).ejecutar(ADMIN, datos())
        filtro = FiltroGastos(desde=datetime(2026, 11, 25), hasta=datetime(2026, 11, 26))
        assert len(await ListarGastos(repo).ejecutar(filtro)) == 1


class TestEliminarGasto:
    def setup_method(self):
        self.repo = GastoRepoMemoria()
        self.caso = EliminarGasto(self.repo)

    async def test_elimina(self):
        gasto = await RegistrarGasto(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        await self.caso.ejecutar(ADMIN, gasto.id)
        assert self.repo.items == {}

    async def test_un_gasto_inexistente_no_se_puede_eliminar(self):
        with pytest.raises(EntidadNoEncontrada):
            await self.caso.ejecutar(ADMIN, 99)

    async def test_un_general_no_puede_eliminar(self):
        gasto = await RegistrarGasto(self.repo, RelojFijo()).ejecutar(ADMIN, datos())
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, gasto.id)


class TestImportarGastos:
    def setup_method(self):
        self.repo = GastoRepoMemoria()
        self.caso = ImportarGastos(self.repo, RelojFijo())

    async def test_guarda_todos_en_un_lote(self):
        resultado = await self.caso.ejecutar(ADMIN, [datos(), datos(monto=1_000)])
        assert resultado.importadas == 2 and self.repo.lotes == 1

    async def test_una_fila_mala_cancela_todo(self):
        resultado = await self.caso.ejecutar(ADMIN, [datos(), datos(monto=-5)])
        assert resultado.importadas == 0
        assert [e.fila for e in resultado.errores] == [2]
        assert self.repo.items == {}

    async def test_un_general_no_puede_importar(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, [datos()])
