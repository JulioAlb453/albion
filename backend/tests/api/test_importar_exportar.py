import csv
import io

import openpyxl
import pytest

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.usuarios.domain.entities.usuario import Rol

CABECERA = "fecha,objeto,encantamiento,calidad,ciudad,tipo,cantidad,precio_unitario"


async def subir(entorno, ruta, contenido, rol=Rol.ADMIN):
    if isinstance(contenido, str):
        contenido = contenido.encode("utf-8")
    return await entorno.cliente.post(
        ruta, files={"archivo": ("datos.csv", contenido, "text/csv")}, headers=await entorno.encabezados(rol)
    )


def filas_csv(respuesta):
    return list(csv.reader(io.StringIO(respuesta.content.decode("utf-8-sig"))))


def filas_xlsx(respuesta, hoja):
    libro = openpyxl.load_workbook(io.BytesIO(respuesta.content))
    return [list(fila) for fila in libro[hoja].iter_rows(values_only=True)]


class TestImportarVentas:
    async def test_importa_con_nombres_de_calidad_fechas_de_excel_y_miles(self, entorno):
        contenido = (
            f"{CABECERA}\n"
            '2026-11-24 10:00,T6_MAIN_SWORD,2,Sobresaliente,Lymhurst,directa,2,"100,000"\n'
            "25/11/2026,T4_MAIN_AXE@1,,,Caerleon,orden,1,50000\n"
        )
        respuesta = await subir(entorno, "/api/ventas/importar", contenido)
        assert (respuesta.status_code, respuesta.json()) == (200, {"importadas": 2, "errores": []})

        primera, segunda = (await entorno.cliente.get("/api/ventas", headers=await entorno.encabezados())).json()
        assert (primera["objeto"]["calidad"], primera["precio_unitario"], primera["fecha"][:16]) == (4, 100_000, "2026-11-24T10:00")
        assert (segunda["objeto"]["etiqueta"], segunda["objeto"]["calidad"], segunda["fecha"][:10]) == ("T4.1", 1, "2026-11-25")

    async def test_acepta_punto_y_coma_y_bom_como_los_guarda_excel_en_espanol(self, entorno):
        contenido = ("﻿" + CABECERA.replace(",", ";") + "\n2026-11-24;T4_BAG;0;1;Fort Sterling;directa;1;5000\n").encode("utf-8")
        assert (await subir(entorno, "/api/ventas/importar", contenido)).json()["importadas"] == 1

    async def test_los_errores_de_formato_se_informan_todos_con_su_fila_y_no_se_guarda_nada(self, entorno):
        contenido = (
            f"{CABECERA}\n"
            "2026-11-24,T6_MAIN_SWORD,0,1,Narnia,directa,1,100\n"
            "2026-11-24,T6_MAIN_SWORD,0,1,Lymhurst,directa,abc,100\n"
            "ayer,T6_MAIN_SWORD,0,1,Lymhurst,directa,1,100\n"
        )
        respuesta = await subir(entorno, "/api/ventas/importar", contenido)
        assert respuesta.status_code == 422
        cuerpo = respuesta.json()
        assert cuerpo["importadas"] == 0
        assert [(e["fila"], palabra in e["mensaje"]) for e, palabra in zip(cuerpo["errores"], ("ciudad", "cantidad", "fecha"))] == [
            (2, True), (3, True), (4, True)
        ]
        assert (await entorno.cliente.get("/api/ventas", headers=await entorno.encabezados())).json() == []

    async def test_una_regla_del_dominio_se_informa_con_su_fila_y_cancela_todo(self, entorno):
        contenido = (
            f"{CABECERA}\n"
            "2026-11-24,T6_MAIN_SWORD,0,1,Lymhurst,directa,1,100\n"
            "2026-11-24,ESPADA,0,1,Black Market,orden,1,100\n"
        )
        respuesta = await subir(entorno, "/api/ventas/importar", contenido)
        assert respuesta.status_code == 422
        [error] = respuesta.json()["errores"]
        assert error["fila"] == 3 and "inválido" in error["mensaje"]
        assert (await entorno.cliente.get("/api/ventas", headers=await entorno.encabezados())).json() == []

    async def test_avisa_de_las_columnas_que_faltan(self, entorno):
        respuesta = await subir(entorno, "/api/ventas/importar", "objeto,tipo\nT4_BAG,directa\n")
        [error] = respuesta.json()["errores"]
        assert respuesta.status_code == 422 and error["fila"] == 1
        assert "ciudad" in error["mensaje"] and "cantidad" in error["mensaje"]

    async def test_un_archivo_vacio_se_rechaza(self, entorno):
        assert (await subir(entorno, "/api/ventas/importar", b"")).status_code == 422

    async def test_un_general_recibe_403_sin_que_se_lea_el_archivo(self, entorno):
        assert (await subir(entorno, "/api/ventas/importar", "basura", Rol.GENERAL)).status_code == 403

    async def test_sin_sesion_no_hay_acceso(self, entorno):
        respuesta = await entorno.cliente.post("/api/ventas/importar", files={"archivo": ("a.csv", b"x")})
        assert respuesta.status_code == 401

    async def test_la_plantilla_descargada_se_puede_importar_tal_cual(self, entorno):
        plantilla = await entorno.cliente.get("/api/ventas/plantilla", headers=await entorno.encabezados(Rol.GENERAL))
        assert plantilla.status_code == 200 and plantilla.headers["content-type"].startswith("text/csv")
        assert filas_csv(plantilla)[0][:3] == ["fecha", "objeto", "encantamiento"]
        assert (await subir(entorno, "/api/ventas/importar", plantilla.content)).json()["importadas"] == 1


class TestImportarGastos:
    async def test_importa_con_codificacion_de_windows_y_nombres_de_categoria(self, entorno):
        contenido = (
            "fecha,categoria,descripcion,monto\n"
            '2026-11-24,Reparaciones,Reparación ZvZ,"500,000"\n'
            "2026-11-25,compra de equipo,,1200000\n"
        ).encode("cp1252")
        respuesta = await subir(entorno, "/api/gastos/importar", contenido)
        assert respuesta.json() == {"importadas": 2, "errores": []}
        gastos = (await entorno.cliente.get("/api/gastos", headers=await entorno.encabezados())).json()
        assert [(g["categoria"], g["descripcion"], g["monto"]) for g in gastos] == [
            ("reparaciones", "Reparación ZvZ", 500_000), ("compra_equipo", "", 1_200_000)
        ]

    async def test_una_categoria_desconocida_se_informa_con_su_fila(self, entorno):
        respuesta = await subir(entorno, "/api/gastos/importar", "categoria,monto\nreparaciones,10\nlujos,5\n")
        [error] = respuesta.json()["errores"]
        assert respuesta.status_code == 422 and error["fila"] == 3 and "categoria" in error["mensaje"]

    async def test_la_plantilla_se_puede_importar(self, entorno):
        plantilla = await entorno.cliente.get("/api/gastos/plantilla", headers=await entorno.encabezados())
        assert (await subir(entorno, "/api/gastos/importar", plantilla.content)).json()["importadas"] == 1


class TestExportar:
    async def preparar(self, entorno):
        admin = await entorno.encabezados()
        await entorno.contenedor.catalogo.reemplazar(
            [Objeto("T6_MAIN_SWORD", "Espada ancha del maestro", CategoriaObjeto.ARMA)]
        )
        base = {"base_id": "T6_MAIN_SWORD", "encantamiento": 2, "calidad": 4, "cantidad": 2, "precio_unitario": 100_000}
        await entorno.cliente.post("/api/ventas", json=base | {"ciudad": "Lymhurst", "tipo": "directa"}, headers=admin)
        await entorno.cliente.post("/api/ventas", json=base | {"ciudad": "Caerleon", "tipo": "orden"}, headers=admin)
        await entorno.cliente.post("/api/gastos", json={"categoria": "reparaciones", "descripcion": "ZvZ", "monto": 500_000}, headers=admin)
        return await entorno.encabezados(Rol.GENERAL)

    async def test_ventas_en_csv(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/ventas/exportar", headers=general)
        assert respuesta.headers["content-type"].startswith("text/csv")
        assert respuesta.headers["content-disposition"] == 'attachment; filename="ventas-2026-11-25.csv"'
        cabecera, primera, segunda = filas_csv(respuesta)
        assert cabecera == ["fecha", "objeto", "nombre", "encantamiento", "calidad", "ciudad", "tipo",
                            "cantidad", "precio_unitario", "bruto", "impuesto", "tarifa_publicacion", "neto"]
        assert primera == ["2026-11-25 12:00", "T6_MAIN_SWORD", "Espada ancha del maestro", "2", "4",
                           "Lymhurst", "directa", "2", "100000", "200000", "8000", "0", "192000"]
        assert segunda[5:7] == ["Caerleon", "orden"] and segunda[-1] == "187000"

    async def test_ventas_en_excel_con_numeros_de_verdad(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/ventas/exportar", params={"formato": "xlsx"}, headers=general)
        assert respuesta.headers["content-type"].endswith("spreadsheetml.sheet")
        assert 'filename="ventas-2026-11-25.xlsx"' in respuesta.headers["content-disposition"]
        cabecera, primera, _ = filas_xlsx(respuesta, "Ventas")
        assert cabecera[0] == "fecha" and primera[-1] == 192_000 and isinstance(primera[-1], int)

    async def test_la_exportacion_respeta_los_filtros(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/ventas/exportar", params={"ciudad": "Caerleon"}, headers=general)
        assert [fila[5] for fila in filas_csv(respuesta)[1:]] == ["Caerleon"]

    async def test_gastos_en_csv_y_excel(self, entorno):
        general = await self.preparar(entorno)
        csv_ = filas_csv(await entorno.cliente.get("/api/gastos/exportar", headers=general))
        assert csv_ == [["fecha", "categoria", "descripcion", "monto"], ["2026-11-25 12:00", "reparaciones", "ZvZ", "500000"]]
        xlsx = await entorno.cliente.get("/api/gastos/exportar", params={"formato": "xlsx"}, headers=general)
        assert filas_xlsx(xlsx, "Gastos")[1][1:] == ["reparaciones", "ZvZ", 500_000]

    async def test_reportes_en_excel_con_una_hoja_por_tabla(self, entorno):
        general = await self.preparar(entorno)
        respuesta = await entorno.cliente.get("/api/reportes/exportar", params={"formato": "xlsx"}, headers=general)
        libro = openpyxl.load_workbook(io.BytesIO(respuesta.content))
        assert libro.sheetnames == ["Ganancia por objeto", "Impuestos y resultado", "Gastos por categoria"]
        resumen = {fila[0]: fila[1] for fila in filas_xlsx(respuesta, "Impuestos y resultado")[1:]}
        assert resumen["ventas_netas"] == 379_000 and resumen["gastos_totales"] == 500_000 and resumen["resultado"] == -121_000
        assert resumen["impuesto_venta"] == 16_000 and resumen["tarifa_publicacion"] == 5_000

    async def test_reportes_en_csv_es_la_ganancia_por_objeto(self, entorno):
        general = await self.preparar(entorno)
        cabecera, fila = filas_csv(await entorno.cliente.get("/api/reportes/exportar", headers=general))
        assert cabecera[:3] == ["objeto", "nombre", "encantamiento"] and fila[1] == "Espada ancha del maestro"
        assert fila[-1] == "379000"

    async def test_un_texto_que_parece_formula_no_se_ejecuta_al_abrir_el_archivo(self, entorno):
        admin = await entorno.encabezados()
        peligro = '=HYPERLINK("http://malo.test","clic")'
        await entorno.cliente.post("/api/gastos", json={"categoria": "otros", "descripcion": peligro, "monto": 1}, headers=admin)
        for formato, leer in (("csv", lambda r: filas_csv(r)[1][2]), ("xlsx", lambda r: filas_xlsx(r, "Gastos")[1][2])):
            respuesta = await entorno.cliente.get("/api/gastos/exportar", params={"formato": formato}, headers=admin)
            assert leer(respuesta) == "'" + peligro

    async def test_un_formato_desconocido_da_422(self, entorno):
        respuesta = await entorno.cliente.get("/api/ventas/exportar", params={"formato": "pdf"}, headers=await entorno.encabezados())
        assert respuesta.status_code == 422

    @pytest.mark.parametrize("ruta", ["/api/ventas/exportar", "/api/gastos/exportar", "/api/reportes/exportar", "/api/ventas/plantilla"])
    async def test_pide_sesion(self, entorno, ruta):
        assert (await entorno.cliente.get(ruta)).status_code == 401
