import pytest

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.usuarios.domain.entities.usuario import Rol


def venta(**cambios):
    return {
        "base_id": "T6_MAIN_SWORD", "encantamiento": 2, "calidad": 4, "ciudad": "Lymhurst",
        "tipo": "directa", "cantidad": 2, "precio_unitario": 100_000,
    } | cambios


def gasto(**cambios):
    return {"categoria": "reparaciones", "descripcion": "ZvZ", "monto": 500_000} | cambios


class TestVentas:
    async def test_sin_sesion_no_hay_acceso(self, entorno):
        assert (await entorno.cliente.get("/api/ventas")).status_code == 401
        assert (await entorno.cliente.post("/api/ventas", json=venta())).status_code == 401

    async def test_el_admin_registra_y_se_calculan_los_impuestos(self, entorno):
        await entorno.contenedor.catalogo.reemplazar(
            [Objeto("T6_MAIN_SWORD", "Espada ancha del maestro", CategoriaObjeto.ARMA)]
        )
        respuesta = await entorno.cliente.post("/api/ventas", json=venta(tipo="orden"), headers=await entorno.encabezados())
        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert cuerpo["id"] == 1 and cuerpo["fecha"].startswith("2026-11-25T12:00:00")
        assert cuerpo["objeto"] == {
            "base_id": "T6_MAIN_SWORD", "nombre": "Espada ancha del maestro",
            "etiqueta": "T6.2", "encantamiento": 2, "calidad": 4,
        }
        assert (cuerpo["bruto"], cuerpo["impuesto"], cuerpo["tarifa_publicacion"], cuerpo["neto"]) == (
            200_000, 8_000, 5_000, 187_000
        )

    async def test_un_objeto_fuera_del_catalogo_no_tiene_nombre_pero_se_registra(self, entorno):
        respuesta = await entorno.cliente.post("/api/ventas", json=venta(), headers=await entorno.encabezados())
        assert respuesta.status_code == 201 and respuesta.json()["objeto"]["nombre"] is None

    async def test_un_general_no_puede_registrar(self, entorno):
        respuesta = await entorno.cliente.post("/api/ventas", json=venta(), headers=await entorno.encabezados(Rol.GENERAL))
        assert respuesta.status_code == 403
        assert (await entorno.cliente.get("/api/ventas", headers=await entorno.encabezados())).json() == []

    @pytest.mark.parametrize(
        "cambios, texto",
        [
            (dict(ciudad="Black Market", tipo="orden"), "Black Market"),
            (dict(base_id="ESPADA"), "inválido"),
            (dict(encantamiento=2, base_id="T6_MAIN_SWORD@2"), "inválido"),
        ],
    )
    async def test_las_reglas_del_dominio_dan_422_con_la_razon(self, entorno, cambios, texto):
        respuesta = await entorno.cliente.post("/api/ventas", json=venta(**cambios), headers=await entorno.encabezados())
        assert respuesta.status_code == 422 and texto in respuesta.json()["detail"]

    @pytest.mark.parametrize("cambios", [dict(cantidad=0), dict(precio_unitario=-1), dict(calidad=9), dict(ciudad="Narnia")])
    async def test_los_datos_mal_formados_dan_422(self, entorno, cambios):
        respuesta = await entorno.cliente.post("/api/ventas", json=venta(**cambios), headers=await entorno.encabezados())
        assert respuesta.status_code == 422

    async def test_cualquier_miembro_lista_y_filtra(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/ventas", json=venta(ciudad="Lymhurst", fecha="2026-11-24T10:00:00"), headers=admin)
        await entorno.cliente.post("/api/ventas", json=venta(ciudad="Caerleon", fecha="2026-11-26T10:00:00"), headers=admin)
        general = await entorno.encabezados(Rol.GENERAL)
        todas = await entorno.cliente.get("/api/ventas", headers=general)
        assert [v["ciudad"] for v in todas.json()] == ["Lymhurst", "Caerleon"]
        por_ciudad = await entorno.cliente.get("/api/ventas", params={"ciudad": "Caerleon"}, headers=general)
        assert [v["ciudad"] for v in por_ciudad.json()] == ["Caerleon"]
        por_fecha = await entorno.cliente.get("/api/ventas", params={"desde": "2026-11-25T00:00:00", "hasta": "2026-11-27T00:00:00"}, headers=general)
        assert [v["ciudad"] for v in por_fecha.json()] == ["Caerleon"]

    async def test_elimina_y_distingue_los_errores(self, entorno):
        admin = await entorno.encabezados()
        creada = (await entorno.cliente.post("/api/ventas", json=venta(), headers=admin)).json()
        general = await entorno.encabezados(Rol.GENERAL)
        assert (await entorno.cliente.delete(f"/api/ventas/{creada['id']}", headers=general)).status_code == 403
        assert (await entorno.cliente.delete(f"/api/ventas/{creada['id']}", headers=admin)).status_code == 204
        assert (await entorno.cliente.delete(f"/api/ventas/{creada['id']}", headers=admin)).status_code == 404


class TestGastos:
    async def test_sin_sesion_no_hay_acceso(self, entorno):
        assert (await entorno.cliente.get("/api/gastos")).status_code == 401

    async def test_el_admin_registra(self, entorno):
        respuesta = await entorno.cliente.post("/api/gastos", json=gasto(), headers=await entorno.encabezados())
        assert respuesta.status_code == 201
        assert respuesta.json() == {
            "id": 1, "categoria": "reparaciones", "descripcion": "ZvZ", "monto": 500_000,
            "fecha": respuesta.json()["fecha"],
        }
        assert respuesta.json()["fecha"].startswith("2026-11-25T12:00:00")

    async def test_un_general_no_puede_registrar(self, entorno):
        respuesta = await entorno.cliente.post("/api/gastos", json=gasto(), headers=await entorno.encabezados(Rol.GENERAL))
        assert respuesta.status_code == 403

    @pytest.mark.parametrize(
        "cambios, codigo",
        [(dict(categoria="otros", descripcion=" "), 422), (dict(monto=0), 422), (dict(categoria="lujos"), 422)],
    )
    async def test_los_gastos_invalidos_dan_422(self, entorno, cambios, codigo):
        respuesta = await entorno.cliente.post("/api/gastos", json=gasto(**cambios), headers=await entorno.encabezados())
        assert respuesta.status_code == codigo

    async def test_lista_filtra_por_categoria_y_elimina(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/gastos", json=gasto(), headers=admin)
        creado = (await entorno.cliente.post("/api/gastos", json=gasto(categoria="compra_equipo"), headers=admin)).json()
        lista = await entorno.cliente.get("/api/gastos", params={"categoria": "compra_equipo"}, headers=admin)
        assert [g["id"] for g in lista.json()] == [creado["id"]]
        assert (await entorno.cliente.delete(f"/api/gastos/{creado['id']}", headers=admin)).status_code == 204
        assert (await entorno.cliente.delete(f"/api/gastos/{creado['id']}", headers=admin)).status_code == 404
