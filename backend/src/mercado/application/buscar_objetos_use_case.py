from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos


class BuscarObjetos:
    def __init__(self, catalogo: ICatalogoObjetos):
        self._catalogo = catalogo

    async def ejecutar(
        self, texto: str, categoria: CategoriaObjeto | None = None, limite: int = 20
    ) -> list[Objeto]:
        return await self._catalogo.buscar(texto, categoria, limite)
