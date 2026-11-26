from src.core.application.texto import normalizar_texto as normalizar
from src.core.infrastructure.database import Database
from src.core.infrastructure.sql import clausula_where
from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos


def _como_literal(texto: str) -> str:
    """Escapa los comodines de LIKE para que el texto buscado se tome tal cual."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


_COLUMNAS = "base_id, nombre, categoria, tiene_calidad, encantamiento_min, encantamiento_max"


def _a_objeto(fila: tuple) -> Objeto:
    base_id, nombre, categoria, tiene_calidad, minimo, maximo = fila
    return Objeto(base_id, nombre, CategoriaObjeto(categoria), bool(tiene_calidad), minimo, maximo)


class SqliteCatalogoObjetos(ICatalogoObjetos):
    def __init__(self, db: Database):
        self._db = db

    async def reemplazar(self, objetos: list[Objeto]) -> None:
        """Sustituye todo el catálogo de una vez: o queda el nuevo completo o el anterior intacto."""
        filas = [
            (o.base_id, o.nombre, normalizar(o.nombre), o.categoria.value,
             int(bool(o.tiene_calidad)), o.encantamiento_min, o.encantamiento_max)
            for o in objetos
        ]
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM catalogo_objetos")
            await conn.executemany(
                "INSERT INTO catalogo_objetos (base_id, nombre, nombre_busqueda, categoria, "
                "tiene_calidad, encantamiento_min, encantamiento_max) VALUES (?, ?, ?, ?, ?, ?, ?)",
                filas,
            )

    async def buscar(
        self, texto: str, categoria: CategoriaObjeto | None = None, limite: int = 20
    ) -> list[Objeto]:
        # Cada palabra por separado y en cualquier orden: "zapato asesino" halla "Zapatos de asesino".
        palabras = [
            ("nombre_busqueda LIKE ? ESCAPE '\\'", f"%{_como_literal(palabra)}%")
            for palabra in normalizar(texto).split()
        ]
        donde, parametros = clausula_where([*palabras, ("categoria = ?", categoria and categoria.value)])
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM catalogo_objetos "
                # Agrupa el mismo objeto de distintos tiers: T4_MAIN_SWORD, T5_MAIN_SWORD…
                f"{donde} ORDER BY substr(base_id, 4), base_id LIMIT ?",
                [*parametros, limite],
            )
            filas = await cursor.fetchall()
        return [_a_objeto(fila) for fila in filas]

    async def get_by_base_id(self, base_id: str) -> Objeto | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM catalogo_objetos WHERE base_id = ?",
                (base_id,),
            )
            fila = await cursor.fetchone()
        return None if fila is None else _a_objeto(fila)
