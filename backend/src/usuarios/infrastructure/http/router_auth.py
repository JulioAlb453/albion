from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.bootstrap.contenedor import Contenedor
from src.core.domain.errors import AccesoDenegado, ServicioExternoNoDisponible, SesionInvalida
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.usuarios.domain.entities.usuario import Rol, Usuario

router = APIRouter(prefix="/api")


class UsuarioOut(BaseModel):
    discord_id: str
    nombre: str
    avatar_hash: str | None
    rol: Rol
    puede_registrar: bool


@router.get("/salud", tags=["sistema"])
async def salud() -> dict[str, str]:
    return {"estado": "ok"}


@router.get("/auth/yo", tags=["auth"])
async def yo(usuario: Usuario = Depends(usuario_actual)) -> UsuarioOut:
    return UsuarioOut(
        discord_id=usuario.discord_id,
        nombre=usuario.nombre,
        avatar_hash=usuario.avatar_hash,
        rol=usuario.rol,
        puede_registrar=usuario.puede_registrar,
    )


@router.get("/auth/discord/login", tags=["auth"])
async def login(c: Contenedor = Depends(contenedor)) -> RedirectResponse:
    estado = c.emisor_tokens.emitir_estado()
    return RedirectResponse(c.externos.proveedor_identidad.url_autorizacion(estado))


@router.get("/auth/discord/callback", tags=["auth"])
async def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    c: Contenedor = Depends(contenedor),
) -> RedirectResponse:
    """Vuelve siempre al frontend. El resultado va en el fragmento (`#token=` o `#error=`):
    el navegador no lo envía a ningún servidor, así que no queda en logs."""

    def volver(fragmento: str) -> RedirectResponse:
        return RedirectResponse(f"{c.config.frontend_url}#{fragmento}")

    if error or not code:
        return volver("error=cancelado")
    try:
        c.emisor_tokens.verificar_estado(state or "")
    except SesionInvalida:
        return volver("error=estado_invalido")
    try:
        usuario = await c.iniciar_sesion_con_discord.ejecutar(code)
    except AccesoDenegado:
        return volver("error=sin_acceso")
    except SesionInvalida:
        return volver("error=codigo_invalido")
    except ServicioExternoNoDisponible:
        return volver("error=discord_no_disponible")
    return volver(f"token={c.emisor_tokens.emitir_sesion(usuario)}")
