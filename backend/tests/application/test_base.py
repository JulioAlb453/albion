from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.core.application.fechas import a_utc, a_utc_o_none
from src.core.application.importacion import importar
from src.core.domain.errors import AccesoDenegado, ErrorDominio
from src.usuarios.domain.services.autorizacion import exigir_admin
from tests.application.fakes import ADMIN, GENERAL


class TestFechas:
    def test_sin_zona_se_toma_como_utc(self):
        assert a_utc(datetime(2026, 11, 25, 12)) == datetime(2026, 11, 25, 12, tzinfo=UTC)

    def test_con_zona_se_convierte_a_utc(self):
        mexico = timezone(timedelta(hours=-6))
        resultado = a_utc(datetime(2026, 11, 25, 6, tzinfo=mexico))
        assert resultado == datetime(2026, 11, 25, 12, tzinfo=UTC)
        assert resultado.utcoffset() == timedelta(0)

    def test_none_se_queda_en_none(self):
        assert a_utc_o_none(None) is None


class TestAutorizacion:
    def test_admin_pasa(self):
        exigir_admin(ADMIN)

    def test_general_es_rechazado(self):
        with pytest.raises(AccesoDenegado):
            exigir_admin(GENERAL)


class TestImportar:
    async def importar_filas(self, filas, guardados, **opciones):
        async def guardar(lote):
            guardados.append(lote)

        def construir(valor):
            if valor < 0:
                raise ErrorDominio(f"negativo: {valor}")
            return valor * 2

        return await importar(filas, construir, guardar, **opciones)

    async def test_guarda_todo_en_un_lote(self):
        guardados = []
        resultado = await self.importar_filas([1, 2, 3], guardados)
        assert (resultado.importadas, resultado.errores) == (3, [])
        assert guardados == [[2, 4, 6]]

    async def test_con_errores_no_guarda_nada_y_numera_las_filas(self):
        guardados = []
        resultado = await self.importar_filas([1, -1, 3, -2], guardados)
        assert resultado.importadas == 0
        assert [(e.fila, e.mensaje) for e in resultado.errores] == [
            (2, "negativo: -1"), (4, "negativo: -2")
        ]
        assert guardados == []

    async def test_la_numeracion_puede_empezar_en_otra_fila(self):
        # En un CSV la fila 1 es el encabezado, así que los datos empiezan en la 2.
        resultado = await self.importar_filas([-1], [], fila_inicial=2)
        assert resultado.errores[0].fila == 2

    async def test_sin_filas_no_guarda(self):
        guardados = []
        resultado = await self.importar_filas([], guardados)
        assert resultado.importadas == 0 and guardados == []
