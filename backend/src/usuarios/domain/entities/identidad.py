from dataclasses import dataclass


@dataclass(frozen=True)
class IdentidadDiscord:
    """Lo único que se toma de Discord (scope `identify`): sin correo ni tokens."""

    discord_id: str
    nombre: str
    avatar_hash: str | None
