from collections.abc import Iterable

from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos


class ObtenerNombresObjetos:
    """Nombre en español de cada identificador, para mostrar en listas y reportes."""

    def __init__(self, catalogo: ICatalogoObjetos):
        self._catalogo = catalogo

    async def ejecutar(self, base_ids: Iterable[str]) -> dict[str, str]:
        nombres: dict[str, str] = {}
        for base_id in dict.fromkeys(base_ids):
            objeto = await self._catalogo.get_by_base_id(base_id)
            if objeto is not None:
                nombres[base_id] = objeto.nombre
        return nombres
