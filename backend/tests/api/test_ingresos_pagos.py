from src.usuarios.domain.entities.usuario import Rol

# El reloj de pruebas marca el miércoles 2026-11-25 12:00 UTC: la semana va del 23 al 29.


def ingreso(**cambios):
    return {"categoria": "donacion", "descripcion": "Ana", "monto": 2_000_000} | cambios


def asignacion(**cambios):
    return {"miembro": "Ana", "monto": 1_000_000} | cambios


class TestIngresos:
    async def test_el_admin_registra_y_todos_listan(self, entorno):
        admin = await entorno.encabezados()
        respuesta = await entorno.cliente.post("/api/ingresos", json=ingreso(), headers=admin)
        assert respuesta.status_code == 201
        assert respuesta.json() | {"fecha": None} == {
            "id": 1, "categoria": "donacion", "descripcion": "Ana", "monto": 2_000_000, "fecha": None,
        }
        general = await entorno.encabezados(Rol.GENERAL)
        assert [i["monto"] for i in (await entorno.cliente.get("/api/ingresos", headers=general)).json()] == [2_000_000]

    async def test_filtra_por_fecha_y_categoria(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/ingresos", json=ingreso(fecha="2026-11-20T10:00:00"), headers=admin)
        await entorno.cliente.post("/api/ingresos", json=ingreso(categoria="territorios"), headers=admin)
        por_fecha = await entorno.cliente.get("/api/ingresos", params={"desde": "2026-11-24T00:00:00"}, headers=admin)
        assert [i["categoria"] for i in por_fecha.json()] == ["territorios"]
        por_categoria = await entorno.cliente.get("/api/ingresos", params={"categoria": "donacion"}, headers=admin)
        assert [i["categoria"] for i in por_categoria.json()] == ["donacion"]

    async def test_permisos_y_errores(self, entorno):
        general = await entorno.encabezados(Rol.GENERAL)
        admin = await entorno.encabezados()
        assert (await entorno.cliente.post("/api/ingresos", json=ingreso(), headers=general)).status_code == 403
        otros = await entorno.cliente.post("/api/ingresos", json=ingreso(categoria="otros", descripcion=""), headers=admin)
        assert otros.status_code == 422
        creado = (await entorno.cliente.post("/api/ingresos", json=ingreso(), headers=admin)).json()
        assert (await entorno.cliente.delete(f"/api/ingresos/{creado['id']}", headers=general)).status_code == 403
        assert (await entorno.cliente.delete(f"/api/ingresos/{creado['id']}", headers=admin)).status_code == 204
        assert (await entorno.cliente.delete(f"/api/ingresos/{creado['id']}", headers=admin)).status_code == 404


class TestPagosSemanales:
    async def test_asigna_en_la_semana_actual_por_defecto(self, entorno):
        respuesta = await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=await entorno.encabezados())
        assert respuesta.status_code == 201
        assert respuesta.json() == {
            "id": 1, "miembro": "Ana", "monto": 1_000_000, "descripcion": "", "semana": "2026-11-23",
            "fin_semana": "2026-11-29", "pagado": 0, "fecha_pago": None, "estado": "pendiente", "no_reclamado": 0,
        }

    async def test_cualquier_dia_de_la_semana_se_lleva_a_su_lunes(self, entorno):
        respuesta = await entorno.cliente.post(
            "/api/pagos-semanales", json=asignacion(semana="2026-11-19"), headers=await entorno.encabezados()
        )
        # semana del 16 al 22, ya terminada y sin pagar: todo queda para el gremio
        assert (respuesta.json()["semana"], respuesta.json()["estado"], respuesta.json()["no_reclamado"]) == (
            "2026-11-16", "no_reclamado", 1_000_000,
        )

    async def test_registra_y_corrige_un_pago_parcial(self, entorno):
        admin = await entorno.encabezados()
        creado = (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=admin)).json()
        ruta = f"/api/pagos-semanales/{creado['id']}"
        parcial = await entorno.cliente.patch(ruta, json={"pagado": 400_000}, headers=admin)
        assert parcial.status_code == 200
        assert (parcial.json()["pagado"], parcial.json()["estado"]) == (400_000, "parcial")
        assert parcial.json()["fecha_pago"].startswith("2026-11-25T12:00:00")  # sin fecha: ahora
        corregido = await entorno.cliente.patch(
            ruta, json={"pagado": 1_000_000, "fecha_pago": "2026-11-24T18:00:00"}, headers=admin
        )
        assert (corregido.json()["estado"], corregido.json()["fecha_pago"][:10]) == ("pagado", "2026-11-24")

    async def test_reglas_del_pago(self, entorno):
        admin = await entorno.encabezados()
        creado = (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=admin)).json()
        ruta = f"/api/pagos-semanales/{creado['id']}"
        de_mas = await entorno.cliente.patch(ruta, json={"pagado": 1_000_001}, headers=admin)
        assert de_mas.status_code == 422 and "asignado" in de_mas.json()["detail"]
        fuera = await entorno.cliente.patch(ruta, json={"pagado": 10, "fecha_pago": "2026-11-30T10:00:00"}, headers=admin)
        assert fuera.status_code == 422 and "semana" in fuera.json()["detail"]

    async def test_lista_por_semana(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/pagos-semanales", json=asignacion(miembro="Ana"), headers=admin)
        await entorno.cliente.post("/api/pagos-semanales", json=asignacion(miembro="Beto", semana="2026-11-18"), headers=admin)
        general = await entorno.encabezados(Rol.GENERAL)
        esta = await entorno.cliente.get("/api/pagos-semanales", params={"semana": "2026-11-27"}, headers=general)
        assert [p["miembro"] for p in esta.json()] == ["Ana"]
        todas = await entorno.cliente.get("/api/pagos-semanales", headers=general)
        assert [p["miembro"] for p in todas.json()] == ["Beto", "Ana"]

    async def test_permisos(self, entorno):
        admin, general = await entorno.encabezados(), await entorno.encabezados(Rol.GENERAL)
        assert (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=general)).status_code == 403
        creado = (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=admin)).json()
        ruta = f"/api/pagos-semanales/{creado['id']}"
        assert (await entorno.cliente.patch(ruta, json={"pagado": 1}, headers=general)).status_code == 403
        assert (await entorno.cliente.delete(ruta, headers=general)).status_code == 403
        assert (await entorno.cliente.delete(ruta, headers=admin)).status_code == 204
        assert (await entorno.cliente.patch(ruta, json={"pagado": 1}, headers=admin)).status_code == 404


class TestBalanceConIngresosYPagos:
    async def test_el_saldo_suma_ingresos_y_resta_solo_lo_pagado(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.put("/api/balance/saldo-inicial", json={"monto": 10_000_000, "fecha": "2026-11-23"}, headers=admin)
        await entorno.cliente.post("/api/ingresos", json=ingreso(fecha="2026-11-24T10:00:00"), headers=admin)
        creado = (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=admin)).json()
        await entorno.cliente.patch(
            f"/api/pagos-semanales/{creado['id']}", json={"pagado": 400_000, "fecha_pago": "2026-11-25T08:00:00"}, headers=admin
        )
        puntos = (await entorno.cliente.get("/api/balance/evolucion", headers=admin)).json()
        assert [(p["fecha"], p["saldo"]) for p in puntos] == [
            ("2026-11-23", 10_000_000), ("2026-11-24", 12_000_000), ("2026-11-25", 11_600_000),
        ]

    async def test_los_reportes_separan_otros_ingresos_y_pagos_semanales(self, entorno):
        admin = await entorno.encabezados()
        await entorno.cliente.post("/api/ingresos", json=ingreso(), headers=admin)
        await entorno.cliente.post("/api/ingresos", json=ingreso(categoria="territorios", monto=500_000), headers=admin)
        creado = (await entorno.cliente.post("/api/pagos-semanales", json=asignacion(), headers=admin)).json()
        await entorno.cliente.patch(f"/api/pagos-semanales/{creado['id']}", json={"pagado": 300_000}, headers=admin)
        reportes = (await entorno.cliente.get("/api/reportes", headers=admin)).json()
        assert reportes["ingresos_extra"] == 2_500_000
        assert reportes["ingresos_por_categoria"] == [
            {"categoria": "donacion", "monto": 2_000_000}, {"categoria": "territorios", "monto": 500_000},
        ]
        assert reportes["pagos_semanales"] == 300_000
        assert reportes["resultado"] == 2_500_000 - 300_000
