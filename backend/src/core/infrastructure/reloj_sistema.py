from datetime import UTC, datetime

from src.core.domain.ports.i_reloj import IReloj


class RelojSistema(IReloj):
    def ahora(self) -> datetime:
        return datetime.now(UTC)
