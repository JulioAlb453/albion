# Backend: gestión de ventas del gremio

API FastAPI con SQLite para registrar ventas y gastos de un gremio de Albion Online (servidor
Americas), comparar dónde conviene vender (venta directa u orden de venta) y recibir alertas.
Arquitectura hexagonal; los términos del dominio están en [`../GLOSARIO.md`](../GLOSARIO.md).

## Puesta en marcha

Desde `backend/`:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"      # en Linux/Mac: .venv/bin/python
cp .env.example .env                                  # y completa los valores
.venv/Scripts/python -m scripts.importar_catalogo     # carga armas, armaduras y artefactos
.venv/Scripts/python -m uvicorn src.bootstrap.produccion:crear_app_desde_entorno --factory --env-file .env
```

La documentación interactiva queda en <http://localhost:8000/docs>.

## Pruebas

```bash
.venv/Scripts/python -m pytest -q
```

Las pruebas usan una base SQLite real en memoria y dobles solo para Discord y la API de Albion:
no necesitan red ni credenciales.

## Cómo está organizado

```
src/<módulo>/domain/          entidades, puertos y reglas (sin librerías externas)
src/<módulo>/application/     casos de uso: una clase por operación
src/<módulo>/infrastructure/  adaptadores: SQLite, API de Albion, Discord, HTTP
src/bootstrap/                configuración y raíz de composición
```

Módulos: `ventas`, `gastos`, `mercado`, `balance`, `alertas`, `usuarios`, y `core` (lo compartido).
La regla es que el dominio no importa nada de afuera y la aplicación solo importa dominio.

## Permisos

Dos roles, que salen de los roles del servidor de Discord:

| Rol | Puede |
|---|---|
| **admin** | todo: registrar, importar y borrar ventas y gastos, saldo inicial, seguimientos |
| **general** | consultar el panel, el comparador y los reportes, y exportar |

El inicio de sesión pide a Discord solo el permiso `identify`: no se recibe correo. Se guarda el ID,
el nombre, el avatar y el rol. El token de Discord se revoca al instante de usarlo.

## Importar y exportar

- `GET /api/ventas/plantilla` y `/api/gastos/plantilla` descargan un CSV de ejemplo.
- `POST /api/ventas/importar` y `/api/gastos/importar` reciben un CSV (campo `archivo`). Es todo o
  nada: si una fila falla no se guarda ninguna, y se informan todas con su número.
  Acepta `,` o `;`, UTF-8 o la codificación de Windows, fechas `2026-11-25` o `25/11/2026`.
- `GET /api/ventas/exportar`, `/api/gastos/exportar` y `/api/reportes/exportar` con
  `?formato=csv|xlsx` y los mismos filtros del listado.
