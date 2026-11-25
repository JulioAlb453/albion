# Gestión de ventas del gremio (Albion Online)

Registro de ventas y gastos de un gremio de Albion Online (servidor Americas), con comparación de dónde
conviene vender (venta directa u orden de venta), impuestos con premium, balance, reportes y alertas.

| Carpeta | Qué es |
|---|---|
| [`backend/`](backend/README.md) | API FastAPI + SQLite, con arquitectura hexagonal (dominio, aplicación, infraestructura) |
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

## Pruebas

```bash
cd backend && .venv/Scripts/python -m pytest -q     # dominio, aplicación, infraestructura y API
cd frontend && npm test                             # lógica y pantallas
```

Se trabaja con pruebas primero (ver [`skill.md`](skill.md)).
