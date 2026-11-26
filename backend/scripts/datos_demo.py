"""Llena una base de datos con datos de ejemplo para ver la interfaz con vida.

NO la uses con tu base de verdad: se niega a trabajar si la base ya tiene ventas.
Úsala sobre una copia (con el catálogo ya cargado):

    python -m scripts.datos_demo --db RUTA/demo.db
"""

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.infrastructure.sqlite_alerta_repository import SqliteAlertaRepository
from src.alertas.infrastructure.sqlite_seguimiento_repository import SqliteSeguimientoRepository
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.infrastructure.sqlite_saldo_inicial_repository import SqliteSaldoInicialRepository
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.database import Database
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.gastos.infrastructure.sqlite_gasto_repository import SqliteGastoRepository
from src.usuarios.domain.entities.usuario import Rol, Usuario
from src.usuarios.infrastructure.sqlite_usuario_repository import SqliteUsuarioRepository
from src.ventas.domain.entities.venta import Venta
from src.ventas.infrastructure.sqlite_venta_repository import SqliteVentaRepository

# (identificador, encantamiento, calidad, precio base, cantidades posibles)
OBJETOS = [
    ("T6_MAIN_SWORD", 2, Calidad.SOBRESALIENTE, 210_000, (1, 2)),
    ("T6_ARMOR_PLATE_SET1", 1, Calidad.NOTABLE, 260_000, (1, 2)),
    ("T5_2H_BOW", 0, Calidad.BUENA, 120_000, (1, 3)),
    ("T7_HEAD_PLATE_SET1", 0, Calidad.NORMAL, 95_000, (1, 2)),
    ("T6_OFF_SHIELD", 3, Calidad.OBRA_MAESTRA, 340_000, (1,)),
    ("T4_ARTEFACT_2H_BOW_KEEPER", 0, Calidad.NORMAL, 46_000, (5, 8, 12)),
]
CIUDADES = [
    Ciudad.FORT_STERLING, Ciudad.FORT_STERLING, Ciudad.FORT_STERLING, Ciudad.FORT_STERLING,
    Ciudad.LYMHURST, Ciudad.LYMHURST, Ciudad.LYMHURST,
    Ciudad.CAERLEON, Ciudad.CAERLEON,
    Ciudad.BLACK_MARKET, Ciudad.BLACK_MARKET,
    Ciudad.MARTLOCK, Ciudad.BRIDGEWATCH,
]
GASTOS = [
    (CategoriaGasto.REPARACIONES, "Reparaciones tras el ZvZ", 900_000, 1_400_000),
    (CategoriaGasto.REPARACIONES, "Reparaciones de la guardia", 300_000, 600_000),
    (CategoriaGasto.REEQUIPAMIENTO_BUILDS, "Regear de la caza de mazmorras", 1_500_000, 2_800_000),
    (CategoriaGasto.REEQUIPAMIENTO_BUILDS, "Regear de la sesión de Avalon", 1_200_000, 2_200_000),
    (CategoriaGasto.COMPRA_EQUIPO, "Compra de armaduras T6", 2_500_000, 4_000_000),
    (CategoriaGasto.COMPRA_EQUIPO, "Compra de bastones", 800_000, 1_600_000),
    (CategoriaGasto.INGREDIENTES_COMIDA, "Ingredientes para tarta de carne", 150_000, 350_000),
    (CategoriaGasto.INGREDIENTES_COMIDA, "Ingredientes para sopa", 90_000, 220_000),
    (CategoriaGasto.OTROS, "Impuesto de la isla de Lymhurst", 400_000, 400_000),
]


async def sembrar(db: Database) -> dict[str, int]:
    ventas, gastos = SqliteVentaRepository(db), SqliteGastoRepository(db)
    if await ventas.list():
        raise SystemExit("La base ya tiene ventas: este script solo es para bases de ejemplo.")

    azar = random.Random(7)  # siempre los mismos datos
    ahora = datetime.now(UTC)

    await SqliteSaldoInicialRepository(db).save(SaldoInicial(120_000_000, (ahora - timedelta(days=20)).date()))

    lote = []
    for _ in range(38):
        base_id, encantamiento, calidad, precio_base, cantidades = azar.choice(OBJETOS)
        ciudad = azar.choice(CIUDADES)
        orden = azar.random() >= 0.45
        lote.append(
            Venta.registrar(
                objeto=ObjetoRef(base_id, encantamiento, calidad),
                ciudad=ciudad,
                tipo=TipoVenta.ORDEN if orden else TipoVenta.DIRECTA,
                cantidad=azar.choice(cantidades),
                precio_unitario=int(round(precio_base * azar.uniform(0.85, 1.25), -2)),
                fecha=ahora - timedelta(days=azar.randint(0, 19), hours=azar.randint(0, 23), minutes=azar.randint(0, 59)),
            )
        )
    await ventas.save_many(lote)

    await gastos.save_many(
        [
            Gasto(categoria, descripcion, int(round(azar.uniform(minimo, maximo), -3)),
                  ahora - timedelta(days=azar.randint(0, 19), hours=azar.randint(0, 23)))
            for categoria, descripcion, minimo, maximo in GASTOS
        ]
    )

    seguimientos = SqliteSeguimientoRepository(db)
    espada = await seguimientos.save(Seguimiento(ObjetoRef("T6_MAIN_SWORD", 2, Calidad.SOBRESALIENTE), porcentaje_minimo=15))
    await seguimientos.save(Seguimiento(ObjetoRef("T6_ARMOR_PLATE_SET1", 1, Calidad.NOTABLE), Ciudad.LYMHURST, porcentaje_minimo=10))
    escudo = await seguimientos.save(Seguimiento(ObjetoRef("T6_OFF_SHIELD", 3, Calidad.OBRA_MAESTRA), neto_minimo=300_000))

    alertas = SqliteAlertaRepository(db)
    await alertas.save(Alerta(espada.id, espada.objeto, Ciudad.BLACK_MARKET, TipoVenta.DIRECTA, 244_800, 187_000,
                              "Black Market paga 30.9% más neto que Fort Sterling", ahora - timedelta(hours=2)))
    await alertas.save(Alerta(escudo.id, escudo.objeto, Ciudad.CAERLEON, TipoVenta.ORDEN, 318_000, None,
                              "El neto en Caerleon alcanza 318,000 de plata", ahora - timedelta(hours=9)))
    await alertas.save(Alerta(espada.id, espada.objeto, Ciudad.LYMHURST, TipoVenta.ORDEN, 221_000, 187_000,
                              "Lymhurst paga 18.2% más neto que Fort Sterling", ahora - timedelta(days=1, hours=3)))

    usuarios = SqliteUsuarioRepository(db)
    await usuarios.save(Usuario("1", "Julio (demo)", None, Rol.ADMIN))
    await usuarios.save(Usuario("2", "Invitado (demo)", None, Rol.GENERAL))
    return {"ventas": len(lote), "gastos": len(GASTOS), "seguimientos": 3, "alertas": 3}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True, help="base de ejemplo (nunca la de verdad)")
    argumentos = parser.parse_args()
    db = Database(argumentos.db)
    await db.abrir()
    try:
        resumen = await sembrar(db)
    finally:
        await db.cerrar()
    print("Datos de ejemplo creados:", resumen)


if __name__ == "__main__":
    asyncio.run(main())
