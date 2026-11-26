# Gestión de ventas del gremio (Albion Online)

Registro de ventas y gastos de un gremio de Albion Online (servidor Americas), con comparación de dónde
conviene vender (venta directa u orden de venta), impuestos con premium, balance, reportes y alertas.

| Carpeta | Qué es |
|---|---|
| [`backend/`](backend/README.md) | API FastAPI + SQLite, con arquitectura hexagonal (dominio, aplicación, infraestructura) |
| [`bot/`](#bot-de-discord) | Bot de Discord (TypeScript, discord.js): `/precio`, `/comparar`, `/balance`, `/venta`, `/gasto` |
| [`frontend/`](frontend/README.md) | Aplicación web React con estilo Bento Grid, para GitHub Pages |
| [`GLOSARIO.md`](GLOSARIO.md) | Los términos del dominio, tal como los usa el código |

## Cómo se conecta

```
GitHub Pages (frontend) ──HTTPS──▶ ngrok ──▶ tu PC: API FastAPI + SQLite ──▶ API de datos de Albion
                                                    ▲
Discord (inicio de sesión y roles) ─────────────────┘
```

## Para arrancar en tu PC

1. Backend: sigue [`backend/README.md`](backend/README.md) (`.env`, catálogo y `uvicorn`).
2. Frontend: sigue [`frontend/README.md`](frontend/README.md) (`npm install` y `npm run dev`).

## Con Docker (API + bot + ngrok)

> Estos archivos (`docker-compose.yml`, los `Dockerfile`) se escribieron en una máquina **sin Docker**:
> el bot y la API se probaron por separado, pero las imágenes aún no se han construido.

1. Instala **Docker Desktop** (en Windows pide activar WSL2).
2. Crea una cuenta en [ngrok](https://dashboard.ngrok.com): copia tu *authtoken* y reclama tu dominio fijo gratuito.
3. En el [portal de Discord](https://discord.com/developers/applications):
   - OAuth2 → Redirects: `https://TU-DOMINIO.ngrok-free.app/api/auth/discord/callback`.
   - Invita al bot de nuevo con los permisos `bot` y `applications.commands`
     (OAuth2 → URL Generator), para que los comandos aparezcan en el servidor.
4. `cp .env.example .env` y rellénalo (incluye `GREMIO_BOT_CLAVE`, `NGROK_AUTHTOKEN`, `NGROK_DOMINIO`).
5. Levanta todo y carga el catálogo la primera vez:

```bash
docker compose up -d --build
docker compose run --rm api python -m scripts.importar_catalogo
docker compose logs -f bot        # debe decir "Bot conectado como ..."
```

6. En GitHub: Settings → Secrets and variables → Actions → Variables → `VITE_API_URL` = `https://TU-DOMINIO.ngrok-free.app`,
   y vuelve a lanzar el workflow del frontend.

Cosas que conviene saber:

- La base vive en `./data` y las copias diarias en `./respaldos` (se conservan 30). Para restaurar, detén la API
  y copia una `gremio-AAAA-MM-DD.db` sobre `data/gremio.db`.
- Si tu PC está apagada, la web y el bot dejan de funcionar; con `restart: unless-stopped` vuelven solos al encender Docker.
- La clave del bot solo vale dentro de la red de Docker: la API la rechaza si la petición llega por ngrok.
- Al abrir el enlace de inicio de sesión en el navegador, ngrok gratis muestra una página de aviso la primera vez:
  se acepta y sigue.

## Bot de Discord

Cuatro cosas que hay que saber (el código está en [`bot/`](bot/src)):

- `/precio`, `/comparar` y `/balance` los puede usar cualquiera con el rol del gremio; `/venta` y `/gasto`, solo administradores.
  El bot **no decide**: se identifica ante la API con la clave y el ID de quien escribió el comando, y la API comprueba su rol cada vez.
- Las respuestas son privadas (solo las ve quien las pidió). `/venta` y `/gasto` además anuncian el registro en el canal.
- Los comandos se publican solo en el servidor del gremio al arrancar el bot.
- Pruebas: `cd bot && npm test`.

## Pruebas

```bash
cd backend && .venv/Scripts/python -m pytest -q     # dominio, aplicación, infraestructura y API
cd frontend && npm test                             # lógica y pantallas
cd bot && npm test                                  # comandos, cliente de la API y configuración
```

Se trabaja con pruebas primero (ver [`skill.md`](skill.md)).
