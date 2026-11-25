from abc import ABC, abstractmethod

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto


class ICatalogoObjetos(ABC):
    """Catálogo del juego (armas, armaduras y artefactos) con nombres en español."""

    @abstractmethod
    async def buscar(
        self, texto: str, categoria: CategoriaObjeto | None = None, limite: int = 20
    ) -> list[Objeto]: ...

    @abstractmethod
    async def get_by_base_id(self, base_id: str) -> Objeto | None: ...
