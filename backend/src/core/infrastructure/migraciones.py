"""Cada elemento es una versión del esquema. Nunca se edita una ya publicada: se agrega otra."""

_V1 = """
BEGIN;

CREATE TABLE ventas (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    base_id            TEXT    NOT NULL,
    encantamiento      INTEGER NOT NULL,
    calidad            INTEGER NOT NULL,
    ciudad             TEXT    NOT NULL,
    tipo               TEXT    NOT NULL,
    cantidad           INTEGER NOT NULL,
    precio_unitario    INTEGER NOT NULL,
    fecha              TEXT    NOT NULL,
    bruto              INTEGER NOT NULL,
    impuesto           INTEGER NOT NULL,
    tarifa_publicacion INTEGER NOT NULL,
    neto               INTEGER NOT NULL
);
CREATE INDEX ix_ventas_fecha ON ventas (fecha);

CREATE TABLE gastos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria   TEXT    NOT NULL,
    descripcion TEXT    NOT NULL,
    monto       INTEGER NOT NULL,
    fecha       TEXT    NOT NULL
);
CREATE INDEX ix_gastos_fecha ON gastos (fecha);

CREATE TABLE saldo_inicial (
    id    INTEGER PRIMARY KEY CHECK (id = 1),
    monto INTEGER NOT NULL,
    fecha TEXT    NOT NULL
);

CREATE TABLE precios_mercado (
    base_id             TEXT    NOT NULL,
    encantamiento       INTEGER NOT NULL,
    calidad             INTEGER NOT NULL,
    ciudad              TEXT    NOT NULL,
    venta_minima        INTEGER NOT NULL,
    venta_minima_fecha  TEXT,
    compra_maxima       INTEGER NOT NULL,
    compra_maxima_fecha TEXT,
    PRIMARY KEY (base_id, encantamiento, calidad, ciudad)
);

CREATE TABLE seguimientos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    base_id           TEXT    NOT NULL,
    encantamiento     INTEGER NOT NULL,
    calidad           INTEGER NOT NULL,
    ciudad_referencia TEXT    NOT NULL,
    porcentaje_minimo TEXT,
    neto_minimo       INTEGER,
    activo            INTEGER NOT NULL
);

CREATE TABLE alertas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    seguimiento_id  INTEGER NOT NULL REFERENCES seguimientos (id) ON DELETE CASCADE,
    ciudad          TEXT    NOT NULL,
    tipo            TEXT    NOT NULL,
    neto_unitario   INTEGER NOT NULL,
    neto_referencia INTEGER,
    motivo          TEXT    NOT NULL,
    fecha           TEXT    NOT NULL
);
CREATE INDEX ix_alertas_seguimiento ON alertas (seguimiento_id, fecha);

CREATE TABLE usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id  TEXT NOT NULL UNIQUE,
    nombre      TEXT NOT NULL,
    avatar_hash TEXT,
    rol         TEXT NOT NULL
);

CREATE TABLE catalogo_objetos (
    base_id         TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    nombre_busqueda TEXT NOT NULL,
    categoria       TEXT NOT NULL
);

PRAGMA user_version = 1;
COMMIT;
"""

# La alerta guarda su objeto. Las que ya existían lo heredan de su seguimiento.
_V2 = """
BEGIN;

ALTER TABLE alertas ADD COLUMN base_id       TEXT    NOT NULL DEFAULT '';
ALTER TABLE alertas ADD COLUMN encantamiento INTEGER NOT NULL DEFAULT 0;
ALTER TABLE alertas ADD COLUMN calidad       INTEGER NOT NULL DEFAULT 1;

UPDATE alertas SET
    base_id       = (SELECT base_id       FROM seguimientos WHERE seguimientos.id = alertas.seguimiento_id),
    encantamiento = (SELECT encantamiento FROM seguimientos WHERE seguimientos.id = alertas.seguimiento_id),
    calidad       = (SELECT calidad       FROM seguimientos WHERE seguimientos.id = alertas.seguimiento_id);

PRAGMA user_version = 2;
COMMIT;
"""

MIGRACIONES: tuple[str, ...] = (_V1, _V2)
