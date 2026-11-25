from datetime import timedelta
from decimal import Decimal

import pytest

from src.alertas.application.crear_seguimiento_use_case import CrearSeguimiento
from src.alertas.application.eliminar_seguimiento_use_case import EliminarSeguimiento
from src.alertas.application.listar_seguimientos_use_case import ListarSeguimientos
from src.alertas.application.revisar_alertas_use_case import RevisarAlertas
from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, ErrorDominio
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.application.actualizar_precios_use_case import ActualizarPrecios
from tests.application.fakes import (
    ADMIN,
    GENERAL,
    AlertaRepoMemoria,
    NotificadorMemoria,
    PrecioRepoMemoria,
    ProveedorPreciosFalso,
    RelojFijo,
    SeguimientoRepoMemoria,
)
from tests.domain.fixtures import AHORA, ESPADA, precio

ESPADA_T5 = ObjetoRef("T5_MAIN_SWORD")
PRECIOS = [
    precio(Ciudad.FORT_STERLING, compra=100_000),
    precio(Ciudad.BLACK_MARKET, compra=120_000),
    precio(Ciudad.FORT_STERLING, compra=100_000, objeto=ESPADA_T5),
    precio(Ciudad.BLACK_MARKET, compra=120_000, objeto=ESPADA_T5),
]


class TestSeguimientos:
    def setup_method(self):
        self.repo = SeguimientoRepoMemoria()
        self.crear = CrearSeguimiento(self.repo)

    async def test_el_admin_crea_un_seguimiento(self):
        seguimiento = await self.crear.ejecutar(ADMIN, ESPADA, porcentaje_minimo=Decimal("15"))
        assert seguimiento.id == 1 and seguimiento.ciudad_referencia is Ciudad.FORT_STERLING
        assert self.repo.items == {1: seguimiento}

    async def test_un_general_no_puede_crearlo(self):
        with pytest.raises(AccesoDenegado):
            await self.crear.ejecutar(GENERAL, ESPADA, neto_minimo=1)

    async def test_sin_criterio_no_se_crea(self):
        with pytest.raises(ErrorDominio):
            await self.crear.ejecutar(ADMIN, ESPADA)
        assert self.repo.items == {}

    async def test_listar_devuelve_solo_los_activos(self):
        await self.crear.ejecutar(ADMIN, ESPADA, neto_minimo=1)
        inactivo = await self.crear.ejecutar(ADMIN, ESPADA_T5, neto_minimo=1)
        inactivo.activo = False
        assert [s.objeto for s in await ListarSeguimientos(self.repo).ejecutar()] == [ESPADA]

    async def test_eliminar(self):
        seguimiento = await self.crear.ejecutar(ADMIN, ESPADA, neto_minimo=1)
        await EliminarSeguimiento(self.repo).ejecutar(ADMIN, seguimiento.id)
        assert self.repo.items == {}

    async def test_eliminar_uno_inexistente(self):
        with pytest.raises(EntidadNoEncontrada):
            await EliminarSeguimiento(self.repo).ejecutar(ADMIN, 99)

    async def test_un_general_no_puede_eliminar(self):
        seguimiento = await self.crear.ejecutar(ADMIN, ESPADA, neto_minimo=1)
        with pytest.raises(AccesoDenegado):
            await EliminarSeguimiento(self.repo).ejecutar(GENERAL, seguimiento.id)


class TestRevisarAlertas:
    def setup_method(self):
        self.seguimientos = SeguimientoRepoMemoria()
        self.alertas = AlertaRepoMemoria()
        self.proveedor = ProveedorPreciosFalso(PRECIOS)
        self.notificador = NotificadorMemoria()
        self.reloj = RelojFijo()
        self.armar()

    def armar(self):
        precios = PrecioRepoMemoria()
        self.caso = RevisarAlertas(
            self.seguimientos, self.alertas, precios,
            ActualizarPrecios(self.proveedor, precios), self.notificador, self.reloj,
        )

    async def vigilar(self, objeto=ESPADA):
        return await CrearSeguimiento(self.seguimientos).ejecutar(
            ADMIN, objeto, porcentaje_minimo=Decimal("15")
        )

    async def test_guarda_y_notifica_la_alerta(self):
        seguimiento = await self.vigilar()
        resultado = await self.caso.ejecutar()
        [alerta] = resultado.alertas
        assert (alerta.seguimiento_id, alerta.ciudad) == (seguimiento.id, Ciudad.BLACK_MARKET)
        assert self.alertas.items == {1: alerta}
        assert self.notificador.enviadas == [alerta]
        assert resultado.errores == []

    async def test_no_repite_dentro_del_tiempo_de_espera(self):
        await self.vigilar()
        await self.caso.ejecutar()
        segunda = await self.caso.ejecutar()
        assert segunda.alertas == [] and len(self.notificador.enviadas) == 1

    async def test_vuelve_a_avisar_pasado_el_tiempo_de_espera(self):
        await self.vigilar()
        await self.caso.ejecutar()
        self.reloj._ahora = AHORA + timedelta(hours=3)
        # Los precios de prueba tienen entonces 3.5 h: siguen siendo confiables (límite: 6 h).
        resultado = await self.caso.ejecutar()
        assert len(resultado.alertas) == 1 and len(self.notificador.enviadas) == 2

    async def test_sin_seguimientos_no_consulta_la_api(self):
        resultado = await self.caso.ejecutar()
        assert resultado.alertas == [] and self.proveedor.llamadas == []

    async def test_consulta_la_api_una_sola_vez_para_todos(self):
        await self.vigilar(ESPADA)
        await self.vigilar(ESPADA_T5)
        resultado = await self.caso.ejecutar()
        assert len(resultado.alertas) == 2
        assert self.proveedor.llamadas == [{ESPADA, ESPADA_T5}]

    async def test_un_fallo_al_notificar_no_frena_a_los_demas(self):
        self.notificador.fallar = True
        await self.vigilar(ESPADA)
        await self.vigilar(ESPADA_T5)
        resultado = await self.caso.ejecutar()
        assert len(resultado.alertas) == 2 and len(self.alertas.items) == 2
        assert len(resultado.errores) == 2 and "Discord no responde" in resultado.errores[0]
