from src.core.domain.errors import AccesoDenegado
from src.usuarios.domain.entities.usuario import Usuario


def exigir_admin(actor: Usuario) -> None:
    if not actor.puede_registrar:
        raise AccesoDenegado("Solo un administrador puede hacer esta operación")
