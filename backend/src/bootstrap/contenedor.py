"""Raíz de composición: el único lugar que conoce las implementaciones concretas y las conecta."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from src.alertas.application.crear_seguimiento_use_case import CrearSeguimiento
from src.alertas.application.eliminar_seguimiento_use_case import EliminarSeguimiento
from src.alertas.application.listar_alertas_use_case import ListarAlertas
from src.alertas.application.listar_seguimientos_use_case import ListarSeguimientos
from src.alertas.application.revisar_alertas_use_case import RevisarAlertas
from src.alertas.domain.ports.i_notificador_alertas import INotificadorAlertas
from src.alertas.infrastructure.sqlite_alerta_repository import SqliteAlertaRepository
from src.alertas.infrastructure.sqlite_seguimiento_repository import SqliteSeguimientoRepository
from src.balance.application.configurar_saldo_inicial_use_case import ConfigurarSaldoInicial
from src.balance.application.obtener_evolucion_balance_use_case import ObtenerEvolucionBalance
from src.balance.application.obtener_reportes_use_case import ObtenerReportes
from src.balance.application.obtener_saldo_inicial_use_case import ObtenerSaldoInicial
from src.balance.infrastructure.sqlite_saldo_inicial_repository import SqliteSaldoInicialRepository
from src.bootstrap.configuracion import Configuracion
from src.core.domain.ports.i_reloj import IReloj
from src.core.infrastructure.database import Database
from src.gastos.application.eliminar_gasto_use_case import EliminarGasto
from src.gastos.application.importar_gastos_use_case import ImportarGastos
from src.gastos.application.listar_gastos_use_case import ListarGastos
from src.gastos.application.registrar_gasto_use_case import RegistrarGasto
from src.gastos.infrastructure.sqlite_gasto_repository import SqliteGastoRepository
from src.mercado.application.actualizar_precios_use_case import ActualizarPrecios
from src.mercado.application.buscar_objetos_use_case import BuscarObjetos
from src.mercado.application.comparar_precios_use_case import CompararPrecios
from src.mercado.application.obtener_nombres_objetos_use_case import ObtenerNombresObjetos
from src.mercado.application.obtener_objeto_use_case import ObtenerObjeto
from src.mercado.domain.ports.i_proveedor_precios import IProveedorPrecios
from src.mercado.infrastructure.sqlite_catalogo_objetos import SqliteCatalogoObjetos
from src.mercado.infrastructure.sqlite_precio_mercado_repository import (
    SqlitePrecioMercadoRepository,
)
from src.usuarios.application.iniciar_sesion_con_discord_use_case import IniciarSesionConDiscord
from src.usuarios.application.iniciar_sesion_use_case import IniciarSesion
from src.usuarios.domain.ports.i_directorio_roles import IDirectorioRoles
from src.usuarios.domain.ports.i_proveedor_identidad import IProveedorIdentidad
from src.usuarios.infrastructure.emisor_tokens import EmisorTokens
from src.usuarios.infrastructure.sqlite_usuario_repository import SqliteUsuarioRepository
from src.ventas.application.eliminar_venta_use_case import EliminarVenta
from src.ventas.application.importar_ventas_use_case import ImportarVentas
from src.ventas.application.listar_ventas_use_case import ListarVentas
from src.ventas.application.registrar_venta_use_case import RegistrarVenta
from src.ventas.infrastructure.sqlite_venta_repository import SqliteVentaRepository


class _Cerrable(Protocol):
    async def aclose(self) -> None: ...


@dataclass
class Externos:
    """Lo que vive fuera del sistema. En producción son Discord y la API de Albion; en las
    pruebas, dobles: lo demás (base de datos, casos de uso, HTTP) siempre es el real."""

    proveedor_precios: IProveedorPrecios
    directorio_roles: IDirectorioRoles
    proveedor_identidad: IProveedorIdentidad
    notificador: INotificadorAlertas
    reloj: IReloj


class Contenedor:
    def __init__(
        self,
        config: Configuracion,
        db: Database,
        externos: Externos,
        recursos: Sequence[_Cerrable] = (),
    ):
        self.config, self.db, self.externos = config, db, externos
        self._recursos = recursos
        reloj = self.reloj = externos.reloj
        self.emisor_tokens = EmisorTokens(config.secreto_jwt, config.token_horas, reloj)

        ventas, gastos = SqliteVentaRepository(db), SqliteGastoRepository(db)
        saldos, precios = SqliteSaldoInicialRepository(db), SqlitePrecioMercadoRepository(db)
        seguimientos, alertas = SqliteSeguimientoRepository(db), SqliteAlertaRepository(db)
        self.usuarios = SqliteUsuarioRepository(db)
        self.catalogo = SqliteCatalogoObjetos(db)

        self.registrar_venta = RegistrarVenta(ventas, reloj)
        self.listar_ventas = ListarVentas(ventas)
        self.eliminar_venta = EliminarVenta(ventas)
        self.importar_ventas = ImportarVentas(ventas, reloj)

        self.registrar_gasto = RegistrarGasto(gastos, reloj)
        self.listar_gastos = ListarGastos(gastos)
        self.eliminar_gasto = EliminarGasto(gastos)
        self.importar_gastos = ImportarGastos(gastos, reloj)

        self.buscar_objetos = BuscarObjetos(self.catalogo)
        self.obtener_objeto = ObtenerObjeto(self.catalogo)
        self.obtener_nombres = ObtenerNombresObjetos(self.catalogo)
        self.actualizar_precios = ActualizarPrecios(externos.proveedor_precios, precios)
        self.comparar_precios = CompararPrecios(precios, self.actualizar_precios, reloj)

        self.configurar_saldo_inicial = ConfigurarSaldoInicial(saldos)
        self.obtener_saldo_inicial = ObtenerSaldoInicial(saldos)
        self.obtener_evolucion = ObtenerEvolucionBalance(saldos, ventas, gastos, reloj)
        self.obtener_reportes = ObtenerReportes(ventas, gastos)

        self.crear_seguimiento = CrearSeguimiento(seguimientos)
        self.listar_seguimientos = ListarSeguimientos(seguimientos)
        self.eliminar_seguimiento = EliminarSeguimiento(seguimientos)
        self.listar_alertas = ListarAlertas(alertas)
        self.revisar_alertas = RevisarAlertas(
            seguimientos, alertas, precios, self.actualizar_precios, externos.notificador, reloj
        )

        iniciar_sesion = IniciarSesion(self.usuarios, externos.directorio_roles)
        self.iniciar_sesion_con_discord = IniciarSesionConDiscord(
            externos.proveedor_identidad, iniciar_sesion
        )

    async def cerrar(self) -> None:
        await self.db.cerrar()
        for recurso in self._recursos:
            await recurso.aclose()
