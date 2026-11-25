from src.core.domain.errors import EntidadNoEncontrada
from src.mercado.domain.entities.objeto import Objeto
from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos


class ObtenerObjeto:
    def __init__(self, catalogo: ICatalogoObjetos):
        self._catalogo = catalogo

    async def ejecutar(self, base_id: str) -> Objeto:
        objeto = await self._catalogo.get_by_base_id(base_id)
        if objeto is None:
            raise EntidadNoEncontrada(f"No existe el objeto {base_id}")
        return objeto
