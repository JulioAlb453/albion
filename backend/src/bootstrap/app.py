import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.alertas.infrastructure.http.router_alertas import router as router_alertas
from src.balance.infrastructure.http.router_balance import router as router_balance
from src.bootstrap.contenedor import Contenedor
from src.bootstrap.planificador import ejecutar_periodicamente
from src.core.infrastructure.http.errores import registrar_manejadores
from src.gastos.infrastructure.http.router_gastos import router as router_gastos
from src.ingresos.infrastructure.http.router_ingresos import router as router_ingresos
from src.mercado.infrastructure.http.router_mercado import router as router_mercado
from src.pagos.infrastructure.http.router_pagos import router as router_pagos
from src.usuarios.infrastructure.http.router_auth import router as router_auth
from src.ventas.infrastructure.http.router_ventas import router as router_ventas

_registro = logging.getLogger("gremio.alertas")


def crear_app(contenedor: Contenedor, con_planificador: bool = False) -> FastAPI:
    """`con_planificador` arranca la revisión periódica de alertas; las pruebas la dejan apagada."""

    async def revisar_alertas() -> None:
        resultado = await contenedor.revisar_alertas.ejecutar()
        for error in resultado.errores:
            _registro.warning("Revisión de alertas: %s", error)

    @asynccontextmanager
    async def vida(_: FastAPI):
        await contenedor.db.abrir()
        detener = asyncio.Event()
        tareas: list[asyncio.Task] = []
        if con_planificador:
            segundos = contenedor.config.intervalo_alertas_minutos * 60
            tareas.append(asyncio.create_task(ejecutar_periodicamente(revisar_alertas, segundos, detener)))
            if contenedor.respaldo is not None:
                # Se intenta cada 6 horas: hace una copia por día y sobrevive a reinicios de la PC.
                tareas.append(
                    asyncio.create_task(ejecutar_periodicamente(contenedor.respaldo.ejecutar, 6 * 3600, detener))
                )
        try:
            yield
        finally:
            detener.set()
            for tarea in tareas:
                await tarea
            await contenedor.cerrar()

    app = FastAPI(title="Gremio Albion: ventas", version="0.1.0", lifespan=vida)
    app.state.contenedor = contenedor
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(contenedor.config.cors_origenes),
        allow_methods=["*"],
        # La tercera salta la página de aviso del dominio gratuito de ngrok, que si no responde HTML.
        allow_headers=["Authorization", "Content-Type", "ngrok-skip-browser-warning"],
        expose_headers=["Content-Disposition"],  # para que el frontend lea el nombre del archivo
    )
    registrar_manejadores(app)
    for router in (
        router_auth, router_ventas, router_gastos, router_ingresos, router_pagos,
        router_mercado, router_balance, router_alertas,
    ):
        app.include_router(router)
    return app
