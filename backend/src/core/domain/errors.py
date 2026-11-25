class ErrorDominio(Exception):
    """Regla de negocio violada. La capa HTTP la traduce a 422."""


class EntidadNoEncontrada(ErrorDominio):
    """El recurso pedido no existe. La capa HTTP la traduce a 404."""
