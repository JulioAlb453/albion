class ErrorDominio(Exception):
    """Regla de negocio violada. La capa HTTP la traduce a 422."""


class EntidadNoEncontrada(ErrorDominio):
    """El recurso pedido no existe. La capa HTTP la traduce a 404."""


class AccesoDenegado(ErrorDominio):
    """El usuario no tiene permiso para la operación. La capa HTTP la traduce a 403."""


class ServicioExternoNoDisponible(Exception):
    """Un servicio del que depende el sistema (API de Albion, Discord) no respondió bien.

    No es un error de dominio: la petición era válida. La capa HTTP la traduce a 502.
    """


class SesionInvalida(Exception):
    """Falta iniciar sesión, o el token o el código de Discord no valen. La capa HTTP la traduce a 401."""
