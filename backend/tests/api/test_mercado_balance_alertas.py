from datetime import timedelta
from decimal import Decimal

from src.core.domain.errors import ServicioExternoNoDisponible
from src.core.domain.value_objects.ciudad import Ciudad
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.usuarios.domain.entities.usuario import Rol
from tests.domain.fixtures import precio

ESPADA = {"base_id": "T6_MAIN_SWORD", "encantamiento": 2, "calidad": 4}
CATALOGO = [
    Objeto("T6_MAIN_SWORD", "Espada ancha del maestro", CategoriaObjeto.ARMA),
    Objeto("T6_ARMOR_PLATE_SET1", "Armadura de soldado del maestro", CategoriaObjeto.ARMADURA),
]


class TestCatalogo:
    async def test_busca_por_nombre_y_categoria(self, entorno):
        await entorno.contenedor.catalogo.reemplazar(CATALOGO)
        general = await entorno.encabezados(Rol.GENERAL)
        respuesta = await entorno.cliente.get("/api/catalogo", params={"q": "ESPADA"}, headers=general)
        assert respuesta.json() == [
            {"base_id": "T6_MAIN_SWORD", "nombre": "Espada ancha del maestro", "categoria": "arma", "tiene_calidad": True}
        ]
        solo_armaduras = await entorno.cliente.get("/api/catalogo", params={"q": "maestro", "categoria": "armadura"}, headers=general)
        assert [o["base_id"] for o in solo_armaduras.json()] == ["T6_ARMOR_PLATE_SET1"]

    async def test_pide_sesion(self, entorno):
        assert (await entorno.cliente.get("/api/catalogo")).status_code == 401


class TestComparar:
    async def comparar(self, entorno, **params):
        return await entorno.cliente.get(
            "/api/mercado/comparar", params=ESPADA | params, headers=await entorno.encabezados(Rol.GENERAL)
        )

    async def test_compara_directa_contra_orden_por_ciudad(self, entorno):
        respuesta = await self.comparar(entorno)
        assert respuesta.status_code == 200
        ciudades = respuesta.json()
        assert [c["ciudad"] for c in ciudades] == ["Black Market", "Caerleon", "Fort Sterling"]
        black_market, caerleon, fort = ciudades
        assert black_market["directa"]["neto"] == 144_000 and black_market["orden"] is None
        assert black_market["mejor"] == "directa" and black_market["es_del_gremio"] is False
        assert caerleon["es_del_gremio"] is True and caerleon["mejor"] == "orden"
        assert (fort["directa"]["neto"], fort["orden"]["neto"]) == (86_400, 93_500)
        assert fort["diferencia_orden_vs_directa"] == 7_100
        assert fort["orden"]["antiguedad_segundos"] == 1_800 and fort["orden"]["confiable"] is True

    async def test_la_cantidad_escala_los_netos(self, entorno):
        primero = (await self.comparar(entorno, cantidad=3)).json()[0]
        assert primero["directa"]["neto"] == 432_000 and primero["directa"]["neto_unitario"] == 144_000

    async def test_marca_los_datos_viejos(self, entorno):
        entorno.precios.precios = [precio(Ciudad.CAERLEON, venta=120_000, hace=timedelta(days=1))]
        [caerleon] = (await self.comparar(entorno)).json()
        assert caerleon["orden"]["confiable"] is False

    async def test_un_objeto_invalido_da_422(self, entorno):
        assert (await self.comparar(entorno, base_id="ESPADA")).status_code == 422

    async def test_si_la_api_de_albion_cae_responde_502(self, entorno):
        entorno.precios.fallo = ServicioExternoNoDisponible("La API de Albion no respondió")
        respuesta = await self.comparar(entorno)
        assert respuesta.status_code == 502 and "no respondió" in respuesta.json()["detail"]

    async def test_pide_sesion(self, entorno):
        assert (await entorno.cliente.get("/api/mercado/comparar", params=ESPADA)).status_code == 401


class TestBalance:
    async def test_el_saldo_inicial_lo_configura_solo_el_admin(self, entorno):
        cuerpo = {"monto": 120_000_000, "fecha": "2026-11-25"}
        general = await entorno.encabezados(Rol.GENERAL)
        assert (await entorno.cliente.put("/api/balance/saldo-inicial", json=cuerpo, headers=general)).status_code == 403
        admin = await entorno.encabezados()
        assert (await entorno.cliente.get("/api/balance/saldo-inicial", headers=admin)).status_code == 404
        respuesta = await entorno.cliente.put("/api/balance/saldo-inicial", json=cuerpo, headers=admin)
        assert respuesta.json() == cuerpo
        assert (await entorno.cliente.get("/api/balance/saldo-inicial", headers=general)).json() == cuerpo

    async def test_un_saldo_negativo_da_422(self, entorno):
        respuesta = await entorno.cliente.put(
            "/api/balance/saldo-inicial", json={"monto": -1, "fecha": "2026-11-25"}, headers=await entorno.encabezados()
        )
        assert respuesta.status_code == 422

    async def preparar(self, entorno):
        admin = await entorno.encabezados()
        await entorno.contenedor.catalogo.reemplazar(CATALOGO)
        await entorno.cliente.put("/api/balance/saldo-inicial", json={"monto": 120_000_000, "fecha": "2026-11-25"}, headers=admin)
        await entorno.cliente.post("/api/ventas", json=ESPADA | {"ciudad": "Lymhurst", "tipo": "directa", "cantidad": 1, "precio_unitario": 1_000_000}, headers=admin)
        await entorno.cliente.post("/api/ventas", json=ESPADA | {"ciudad": "Caerleon", "tipo": "orden", "cantidad": 1, "precio_unitario": 100_000}, headers=admin)
        await entorno.cliente.post("/api/gastos", json={"categoria": "reequipamiento_builds", "monto": 500_000}, headers=admin)
        return await entorno.encabezados(Rol.GENERAL)

    async def test_sin_saldo_inicial_no_hay_evolucion(self, entorno):
        respuesta = await entorno.cliente.get("/api/balance/evolucion", headers=await entorno.encabezados())
        assert respuesta.status_code == 404

    async def test_evolucion_del_balance(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/balance/evolucion", headers=general)
        # 120.000.000 + 960.000 (directa) + 93.500 (orden) - 500.000 (gasto)
        assert respuesta.json() == [
            {"fecha": "2026-11-25", "ingresos": 1_053_500, "gastos": 500_000, "saldo": 120_553_500}
        ]

    async def test_reportes_resumen_con_nombres(self, entorno):
        general = await self.preparar(entorno)
        reportes = (await entorno.cliente.get("/api/reportes", headers=general)).json()
        [espada] = reportes["ganancia_por_objeto"]
        assert espada["objeto"]["nombre"] == "Espada ancha del maestro"
        assert (espada["unidades"], espada["neto"]) == (2, 1_053_500)
        assert reportes["impuestos"] == {"impuesto_venta": 44_000, "tarifa_publicacion": 2_500, "total": 46_500}
        assert reportes["gastos_por_categoria"] == [{"categoria": "reequipamiento_builds", "monto": 500_000}]
        assert (reportes["ventas_netas"], reportes["gastos_totales"], reportes["resultado"]) == (1_053_500, 500_000, 553_500)

    async def test_reportes_filtra_por_fechas(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/reportes", params={"desde": "2026-12-01T00:00:00"}, headers=general)
        assert respuesta.json()["resultado"] == 0


class TestSeguimientosYAlertas:
    def seguimiento(self, **cambios):
        return ESPADA | {"porcentaje_minimo": 15} | cambios

    async def test_solo_el_admin_crea_y_borra(self, entorno):
        general = await entorno.encabezados(Rol.GENERAL)
        assert (await entorno.cliente.post("/api/seguimientos", json=self.seguimiento(), headers=general)).status_code == 403
        admin = await entorno.encabezados()
        creado = await entorno.cliente.post("/api/seguimientos", json=self.seguimiento(), headers=admin)
        assert creado.status_code == 201
        assert creado.json()["ciudad_referencia"] == "Fort Sterling" and creado.json()["porcentaje_minimo"] == 15
        assert (await entorno.cliente.delete(f"/api/seguimientos/{creado.json()['id']}", headers=general)).status_code == 403
        assert (await entorno.cliente.delete(f"/api/seguimientos/{creado.json()['id']}", headers=admin)).status_code == 204
        assert (await entorno.cliente.delete("/api/seguimientos/99", headers=admin)).status_code == 404

    async def test_sin_ningun_criterio_da_422(self, entorno):
        respuesta = await entorno.cliente.post("/api/seguimientos", json=ESPADA, headers=await entorno.encabezados())
        assert respuesta.status_code == 422

    async def test_lista_los_seguimientos_activos(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/seguimientos", json=self.seguimiento(), headers=admin)
        lista = await entorno.cliente.get("/api/seguimientos", headers=await entorno.encabezados(Rol.GENERAL))
        assert [s["objeto"]["etiqueta"] for s in lista.json()] == ["T6.2"]

    async def test_las_alertas_emitidas_aparecen_con_su_objeto(self, entorno):
        admin = await entorno.encabezados()
        await entorno.contenedor.catalogo.reemplazar(CATALOGO)
        await entorno.cliente.post("/api/seguimientos", json=self.seguimiento(), headers=admin)
        resultado = await entorno.contenedor.revisar_alertas.ejecutar()
        assert len(resultado.alertas) == 1 and len(entorno.notificador.enviadas) == 1

        [alerta] = (await entorno.cliente.get("/api/alertas", headers=await entorno.encabezados(Rol.GENERAL))).json()
        assert alerta["objeto"]["nombre"] == "Espada ancha del maestro"
        assert (alerta["ciudad"], alerta["tipo"], alerta["neto_unitario"]) == ("Black Market", "directa", 144_000)
        assert alerta["neto_referencia"] == 93_500 and "Fort Sterling" in alerta["motivo"]

    async def test_pide_sesion(self, entorno):
        assert (await entorno.cliente.get("/api/alertas")).status_code == 401
        assert (await entorno.cliente.get("/api/seguimientos")).status_code == 401
