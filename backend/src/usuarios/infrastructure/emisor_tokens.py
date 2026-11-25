import secrets
from datetime import timedelta

import jwt

from src.core.domain.errors import SesionInvalida
from src.core.domain.ports.i_reloj import IReloj
from src.usuarios.domain.entities.usuario import Usuario

_ALGORITMO = "HS256"
_DURACION_ESTADO = timedelta(minutes=10)


class EmisorTokens:
    """Tokens firmados (JWT) de dos clases que no se pueden confundir: sesión y estado de OAuth.

    El token de sesión lleva solo el ID de Discord y las fechas: ni nombre, ni avatar, ni rol.
    El rol se lee de la base en cada petición. La expiración se compara con el reloj propio, no
    con el del sistema, para que se pueda probar.
    """

    def __init__(self, secreto: str, horas: int, reloj: IReloj):
        self._secreto = secreto
        self._duracion_sesion = timedelta(hours=horas)
        self._reloj = reloj

    def emitir_sesion(self, usuario: Usuario) -> str:
        return self._firmar("sesion", self._duracion_sesion, sub=usuario.discord_id)

    def verificar_sesion(self, token: str) -> str:
        return self._leer(token, "sesion")["sub"]

    def emitir_estado(self) -> str:
        return self._firmar("estado", _DURACION_ESTADO, sub=secrets.token_urlsafe(8))

    def verificar_estado(self, estado: str) -> None:
        self._leer(estado, "estado")

    def _firmar(self, tipo: str, duracion: timedelta, **datos: str) -> str:
        ahora = self._reloj.ahora()
        carga = {
            **datos,
            "tipo": tipo,
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + duracion).timestamp()),
        }
        return jwt.encode(carga, self._secreto, algorithm=_ALGORITMO)

    def _leer(self, token: str, tipo: str) -> dict:
        try:
            carga = jwt.decode(
                token,
                self._secreto,
                algorithms=[_ALGORITMO],
                options={"verify_exp": False, "verify_iat": False, "require": ["exp", "tipo", "sub"]},
            )
        except jwt.PyJWTError:
            raise SesionInvalida("El token no es válido") from None
        if carga["tipo"] != tipo:
            raise SesionInvalida("El token no es válido")
        if carga["exp"] <= self._reloj.ahora().timestamp():
            raise SesionInvalida("La sesión expiró: vuelve a iniciar sesión")
        return carga
