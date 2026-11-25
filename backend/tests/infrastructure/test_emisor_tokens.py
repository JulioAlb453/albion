from datetime import timedelta

import jwt
import pytest

from src.core.domain.errors import SesionInvalida
from src.usuarios.infrastructure.emisor_tokens import EmisorTokens
from tests.application.fakes import ADMIN, RelojFijo
from tests.domain.fixtures import AHORA

SECRETO = "s" * 32


class TestEmisorTokens:
    def setup_method(self):
        self.reloj = RelojFijo()
        self.emisor = EmisorTokens(SECRETO, horas=12, reloj=self.reloj)

    def test_la_sesion_lleva_el_discord_id(self):
        assert self.emisor.verificar_sesion(self.emisor.emitir_sesion(ADMIN)) == "1"

    def test_el_token_no_lleva_nada_personal_salvo_el_id(self):
        carga = jwt.decode(self.emisor.emitir_sesion(ADMIN), options={"verify_signature": False})
        assert set(carga) == {"sub", "tipo", "iat", "exp"}

    def test_expira_a_las_horas_configuradas(self):
        token = self.emisor.emitir_sesion(ADMIN)
        self.reloj._ahora = AHORA + timedelta(hours=11)
        assert self.emisor.verificar_sesion(token) == "1"
        self.reloj._ahora = AHORA + timedelta(hours=13)
        with pytest.raises(SesionInvalida, match="expiró"):
            self.emisor.verificar_sesion(token)

    def test_otra_firma_no_vale(self):
        ajeno = EmisorTokens("t" * 32, horas=12, reloj=self.reloj).emitir_sesion(ADMIN)
        with pytest.raises(SesionInvalida):
            self.emisor.verificar_sesion(ajeno)

    def test_basura_no_vale(self):
        with pytest.raises(SesionInvalida):
            self.emisor.verificar_sesion("no-es-un-token")

    def test_un_estado_no_sirve_como_sesion_ni_al_reves(self):
        with pytest.raises(SesionInvalida):
            self.emisor.verificar_sesion(self.emisor.emitir_estado())
        with pytest.raises(SesionInvalida):
            self.emisor.verificar_estado(self.emisor.emitir_sesion(ADMIN))

    def test_el_estado_dura_diez_minutos_y_es_distinto_cada_vez(self):
        estado = self.emisor.emitir_estado()
        assert estado != self.emisor.emitir_estado()
        self.reloj._ahora = AHORA + timedelta(minutes=9)
        self.emisor.verificar_estado(estado)
        self.reloj._ahora = AHORA + timedelta(minutes=11)
        with pytest.raises(SesionInvalida, match="expiró"):
            self.emisor.verificar_estado(estado)
