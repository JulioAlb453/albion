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

# El catálogo deja de ser solo armas, armaduras y artefactos: cada objeto dice qué admite.
_V3 = """
BEGIN;

ALTER TABLE catalogo_objetos ADD COLUMN tiene_calidad     INTEGER NOT NULL DEFAULT 1;
ALTER TABLE catalogo_objetos ADD COLUMN encantamiento_min INTEGER NOT NULL DEFAULT 0;
ALTER TABLE catalogo_objetos ADD COLUMN encantamiento_max INTEGER NOT NULL DEFAULT 4;

UPDATE catalogo_objetos SET tiene_calidad = 0, encantamiento_max = 0 WHERE categoria = 'artefacto';

PRAGMA user_version = 3;
COMMIT;
"""

# Plata que entra sin vender objetos, y los pagos semanales a miembros.
_V4 = """
BEGIN;

CREATE TABLE ingresos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria   TEXT    NOT NULL,
    descripcion TEXT    NOT NULL DEFAULT '',
    monto       INTEGER NOT NULL CHECK (monto > 0),
    fecha       TEXT    NOT NULL
);
CREATE INDEX ix_ingresos_fecha ON ingresos (fecha);

CREATE TABLE pagos_semanales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    miembro     TEXT    NOT NULL,
    monto       INTEGER NOT NULL CHECK (monto > 0),
    semana      TEXT    NOT NULL,
    descripcion TEXT    NOT NULL DEFAULT '',
    pagado      INTEGER NOT NULL DEFAULT 0 CHECK (pagado >= 0 AND pagado <= monto),
    fecha_pago  TEXT
);
CREATE INDEX ix_pagos_semana ON pagos_semanales (semana);
CREATE INDEX ix_pagos_fecha_pago ON pagos_semanales (fecha_pago);

PRAGMA user_version = 4;
COMMIT;
"""

MIGRACIONES: tuple[str, ...] = (_V1, _V2, _V3, _V4)
