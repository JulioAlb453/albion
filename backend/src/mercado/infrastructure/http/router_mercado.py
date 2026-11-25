from fastapi import APIRouter, Depends, Query

from src.bootstrap.contenedor import Contenedor
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.mercado.domain.entities.objeto import CategoriaObjeto
from src.mercado.infrastructure.http.esquemas import ComparacionOut, ObjetoCatalogoOut

router = APIRouter(prefix="/api", tags=["mercado"], dependencies=[Depends(usuario_actual)])


@router.get("/catalogo")
async def buscar_en_el_catalogo(
    q: str = Query("", max_length=60),
    categoria: CategoriaObjeto | None = None,
    limite: int = Query(20, ge=1, le=100),
    c: Contenedor = Depends(contenedor),
) -> list[ObjetoCatalogoOut]:
    objetos = await c.buscar_objetos.ejecutar(q, categoria, limite)
    return [ObjetoCatalogoOut.desde(objeto) for objeto in objetos]


@router.get("/catalogo/{base_id}")
async def obtener_del_catalogo(base_id: str, c: Contenedor = Depends(contenedor)) -> ObjetoCatalogoOut:
    return ObjetoCatalogoOut.desde(await c.obtener_objeto.ejecutar(base_id))


@router.get("/mercado/comparar")
async def comparar(
    base_id: str,
    encantamiento: int = Query(0, ge=0, le=4),
    calidad: Calidad = Calidad.NORMAL,
    cantidad: int = Query(1, gt=0),
    c: Contenedor = Depends(contenedor),
) -> list[ComparacionOut]:
    """Venta directa contra orden de venta en cada ciudad, de mayor a menor neto."""
    comparaciones = await c.comparar_precios.ejecutar(
        ObjetoRef(base_id, encantamiento, calidad), cantidad
    )
    return [ComparacionOut.desde(comparacion) for comparacion in comparaciones]
