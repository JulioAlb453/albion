import httpx

from src.core.domain.errors import ServicioExternoNoDisponible


async def enviar(
    cliente: httpx.AsyncClient, metodo: str, ruta: str, servicio: str, **opciones
) -> httpx.Response:
    """Hace la petición y convierte los fallos de red en `ServicioExternoNoDisponible`.
    Qué hacer con cada código de estado lo decide quien la llama."""
    try:
        return await cliente.request(metodo, ruta, **opciones)
    except httpx.TransportError as error:
        raise ServicioExternoNoDisponible(f"{servicio} no respondió: {error!r}") from error
