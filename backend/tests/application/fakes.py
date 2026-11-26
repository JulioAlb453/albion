"""Dobles en memoria de los puertos, para probar los casos de uso sin infraestructura."""

from datetime import datetime

from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.ports.i_alerta_repository import IAlertaRepository
from src.alertas.domain.ports.i_notificador_alertas import INotificadorAlertas
from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository
from src.balance.domain.ports.i_saldo_inicial_repository import ISaldoInicialRepository
from src.core.domain.errors import ServicioExternoNoDisponible, SesionInvalida
from src.core.domain.ports.i_reloj import IReloj
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository
from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos
from src.mercado.domain.ports.i_precio_mercado_repository import IPrecioMercadoRepository
from src.mercado.domain.ports.i_proveedor_precios import IProveedorPrecios
from src.usuarios.domain.entities.usuario import Rol, Usuario
from src.usuarios.domain.ports.i_directorio_roles import IDirectorioRoles
from src.usuarios.domain.ports.i_proveedor_identidad import IProveedorIdentidad
from src.usuarios.domain.ports.i_usuario_repository import IUsuarioRepository
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos, IIngresoRepository
from src.pagos.domain.ports.i_pago_semanal_repository import FiltroPagos, IPagoSemanalRepository
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository
from tests.domain.fixtures import AHORA

ADMIN = Usuario("1", "julio", None, Rol.ADMIN, id=1)
GENERAL = Usuario("2", "general", None, Rol.GENERAL, id=2)


class RelojFijo(IReloj):
    def __init__(self, ahora: datetime = AHORA):
        self._ahora = ahora

    def ahora(self) -> datetime:
        return self._ahora


class _Memoria:
    def __init__(self):
        self.items = {}
        self._siguiente = 1

    def _guardar(self, entidad):
        if entidad.id is None:
            entidad.id = self._siguiente
            self._siguiente += 1
        self.items[entidad.id] = entidad
        return entidad


def _en_rango(fecha, desde, hasta):
    return (desde is None or fecha >= desde) and (hasta is None or fecha <= hasta)


class VentaRepoMemoria(_Memoria, IVentaRepository):
    def __init__(self):
        super().__init__()
        self.lotes = 0

    async def save(self, venta):
        return self._guardar(venta)

    async def save_many(self, ventas):
        self.lotes += 1
        return [self._guardar(v) for v in ventas]

    async def get_by_id(self, venta_id):
        return self.items.get(venta_id)

    async def delete(self, venta_id):
        self.items.pop(venta_id, None)

    async def update(self, venta):
        self.items[venta.id] = venta
        return venta

    async def list(self, filtro=FiltroVentas()):
        return [
            v for v in self.items.values()
            if _en_rango(v.fecha, filtro.desde, filtro.hasta)
            and filtro.ciudad in (None, v.ciudad)
            and filtro.tipo in (None, v.tipo)
            and filtro.base_id in (None, v.objeto.base_id)
        ]


class GastoRepoMemoria(_Memoria, IGastoRepository):
    def __init__(self):
        super().__init__()
        self.lotes = 0

    async def save(self, gasto):
        return self._guardar(gasto)

    async def save_many(self, gastos):
        self.lotes += 1
        return [self._guardar(g) for g in gastos]

    async def get_by_id(self, gasto_id):
        return self.items.get(gasto_id)

    async def delete(self, gasto_id):
        self.items.pop(gasto_id, None)

    async def list(self, filtro=FiltroGastos()):
        return [
            g for g in self.items.values()
            if _en_rango(g.fecha, filtro.desde, filtro.hasta)
            and filtro.categoria in (None, g.categoria)
        ]


class IngresoRepoMemoria(_Memoria, IIngresoRepository):
    async def save(self, ingreso):
        return self._guardar(ingreso)

    async def get_by_id(self, ingreso_id):
        return self.items.get(ingreso_id)

    async def delete(self, ingreso_id):
        self.items.pop(ingreso_id, None)

    async def list(self, filtro=FiltroIngresos()):
        return [
            i for i in self.items.values()
            if _en_rango(i.fecha, filtro.desde, filtro.hasta) and filtro.categoria in (None, i.categoria)
        ]


class PagoRepoMemoria(_Memoria, IPagoSemanalRepository):
    async def save(self, pago):
        import dataclasses
        if pago.id is None:
            pago = dataclasses.replace(pago, id=self._siguiente)
            self._siguiente += 1
        self.items[pago.id] = pago
        return pago

    async def get_by_id(self, pago_id):
        return self.items.get(pago_id)

    async def delete(self, pago_id):
        self.items.pop(pago_id, None)

    async def list(self, filtro=FiltroPagos()):
        return [
            p for p in self.items.values()
            if filtro.semana in (None, p.semana)
            and (filtro.pagado_desde is None and filtro.pagado_hasta is None
                 or p.fecha_pago is not None and _en_rango(p.fecha_pago, filtro.pagado_desde, filtro.pagado_hasta))
        ]


class CatalogoMemoria(ICatalogoObjetos):
    def __init__(self, objetos):
        self._objetos = [*objetos]

    async def buscar(self, texto, categoria=None, limite=20):
        coincidencias = [
            o for o in self._objetos
            if texto.lower() in o.nombre.lower() and categoria in (None, o.categoria)
        ]
        return coincidencias[:limite]

    async def get_by_base_id(self, base_id):
        return next((o for o in self._objetos if o.base_id == base_id), None)


class ProveedorPreciosFalso(IProveedorPrecios):
    def __init__(self, precios=()):
        self.precios = [*precios]
        self.llamadas = []  # un conjunto de objetos por cada consulta a la API
        self.fallo = None   # una excepción que lanzar, para simular que la API se cae

    async def obtener_precios(self, objetos, ciudades):
        if self.fallo is not None:
            raise self.fallo
        objetos, ciudades = set(objetos), set(ciudades)
        self.llamadas.append(objetos)
        return [p for p in self.precios if p.objeto in objetos and p.ciudad in ciudades]


class PrecioRepoMemoria(IPrecioMercadoRepository):
    def __init__(self):
        self.items = {}

    async def save_many(self, precios):
        for precio in precios:
            self.items[(precio.objeto, precio.ciudad)] = precio

    async def get(self, objeto, ciudades):
        return [self.items[(objeto, c)] for c in ciudades if (objeto, c) in self.items]


class SaldoRepoMemoria(ISaldoInicialRepository):
    def __init__(self, saldo=None):
        self.saldo = saldo

    async def get(self):
        return self.saldo

    async def save(self, saldo):
        self.saldo = saldo
        return saldo


class SeguimientoRepoMemoria(_Memoria, ISeguimientoRepository):
    async def save(self, seguimiento: Seguimiento):
        return self._guardar(seguimiento)

    async def get_by_id(self, seguimiento_id):
        return self.items.get(seguimiento_id)

    async def list_activos(self):
        return [s for s in self.items.values() if s.activo]

    async def delete(self, seguimiento_id):
        self.items.pop(seguimiento_id, None)


class AlertaRepoMemoria(_Memoria, IAlertaRepository):
    async def save(self, alerta):
        return self._guardar(alerta)

    async def ultima_de(self, seguimiento_id):
        propias = [a for a in self.items.values() if a.seguimiento_id == seguimiento_id]
        return max(propias, key=lambda a: a.fecha, default=None)

    async def list_recientes(self, limite=50):
        return sorted(self.items.values(), key=lambda a: a.fecha, reverse=True)[:limite]


class NotificadorMemoria(INotificadorAlertas):
    def __init__(self, fallar=False):
        self.fallar = fallar
        self.enviadas = []

    async def notificar(self, alerta):
        if self.fallar:
            raise ConnectionError("Discord no responde")
        self.enviadas.append(alerta)


class UsuarioRepoMemoria(IUsuarioRepository):
    def __init__(self):
        self.usuarios = {}

    async def get_by_discord_id(self, discord_id):
        return self.usuarios.get(discord_id)

    async def save(self, usuario):
        existente = self.usuarios.get(usuario.discord_id)
        usuario.id = existente.id if existente else len(self.usuarios) + 1
        self.usuarios[usuario.discord_id] = usuario
        return usuario


class DirectorioRolesMemoria(IDirectorioRoles):
    def __init__(self, roles):
        self.roles = dict(roles)

    async def rol_de(self, discord_id):
        return self.roles.get(discord_id)


class ProveedorIdentidadFalso(IProveedorIdentidad):
    """`identidades` va de código de autorización a la identidad que Discord devolvería."""

    def __init__(self, identidades):
        self.identidades = dict(identidades)
        self.caido = False

    def url_autorizacion(self, estado):
        return f"https://discord.test/authorize?state={estado}"

    async def identificar(self, codigo):
        if self.caido:
            raise ServicioExternoNoDisponible("Discord no responde")
        if codigo not in self.identidades:
            raise SesionInvalida("Discord rechazó el código")
        return self.identidades[codigo]
