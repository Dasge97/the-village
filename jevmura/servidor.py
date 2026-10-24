"""Servidor web: hace avanzar el mundo y lo emite en directo.

- `GET /api/aldeas`: las aldeas del mundo (la segunda puede no existir todavía).
- `GET /api/mapa`: el mapa fijo.
- Todas admiten `?aldea=2` para la segunda aldea, también el websocket.
- `GET /api/estado`: el estado actual de la aldea.
- `GET /api/salud`: turno, decisor y fallos seguidos de Jev, para la vigilancia del servidor.
- `GET /api/habitante/{id}`: la ficha completa de un habitante vivo.
- `GET /api/arbol`: todas las personas que han vivido en la aldea, para el árbol genealógico.
- `GET /api/resumenes`: un resumen por año del mundo.
- `WS /ws`: al conectar manda el mapa y el estado; después, el estado tras cada turno.
- `/api/admin/…`: el panel de administración, con contraseña (ver `admin.py`).
- Todo lo demás: la web ya compilada (`web/dist`).

Uso: python -m jevmura.servidor [--db ruta] [--semilla N] [--jev] [--puerto 8000]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .admin import crear_admin
from .bucle import SEGUNDA, Mundo
from .motor import modelos as m
from .motor.aldea import Aldea
from .mundo.grande import Grande
from .vista import arbol_publico, estado_publico, ficha_habitante, mapa_publico
from .vista_grande import arbol_grande, estado_grande, ficha_notable


def estado_de(a) -> dict:
    """El estado de una aldea o de un pueblo, villa o ciudad, con la misma forma para la web."""
    return estado_grande(a) if isinstance(a, Grande) else estado_publico(a)

WEB = Path(__file__).resolve().parent.parent / "web" / "dist"


def crear_app(mundo: Mundo) -> FastAPI:
    clientes: dict[WebSocket, int] = {}          # cada web conectada y la aldea que mira (1 o 2)
    bucle_web: asyncio.AbstractEventLoop | None = None

    async def emitir(n: int, estado: dict) -> None:
        for ws, mira in list(clientes.items()):
            if mira != n:
                continue
            try:
                await ws.send_json({"tipo": "estado", "estado": estado})
            except Exception:
                clientes.pop(ws, None)

    def al_avanzar(aldea: Aldea, n: int) -> None:
        # Se llama desde el hilo del mundo; el estado se calcula aquí y se envía en el bucle de la web.
        if bucle_web and n in clientes.values():
            with mundo.cerrojo:
                estado = estado_web(aldea)
            asyncio.run_coroutine_threadsafe(emitir(n, estado), bucle_web)

    def estado_web(a) -> dict:
        # La duración de un turno es la de ahora (el mundo se puede acelerar desde el panel de
        # administración); la web la usa para que los habitantes anden a la velocidad buena.
        return {**estado_de(a), "segundos_por_turno": mundo.segundos_por_turno or m.TURNO_SEGUNDOS,
                "pausado": mundo.ajustes["pausado"], "mundo": mundo.resumen()}

    def elegir(n: int):
        a = mundo.asentamiento(n)
        if a is None:
            raise HTTPException(404, "Ese asentamiento todavía no existe.")
        return a

    def vigilar() -> None:
        # Las aldeas que alguien mira tienen prioridad con Jev (ver mundo/presupuesto.py).
        mundo.vigiladas = set(clientes.values())

    @asynccontextmanager
    async def vida(app: FastAPI):
        nonlocal bucle_web
        bucle_web = asyncio.get_running_loop()
        mundo.al_avanzar.append(al_avanzar)
        hilo = threading.Thread(target=mundo.ejecutar, name="mundo", daemon=True)
        hilo.start()
        yield
        mundo.parar()
        hilo.join(timeout=15)

    app = FastAPI(title="La aldea", lifespan=vida)
    app.include_router(crear_admin(mundo, lambda: len(clientes)))

    @app.get("/api/aldeas")
    def aldeas() -> list[dict]:
        """Los asentamientos del mundo, del más poblado al menos. Mientras solo haya uno, sale
        también la Aldea del río con `existe: false`, para contar cuándo nacerá."""
        with mundo.cerrojo:
            lista = [{"id": n, "nombre": meta["nombre"], "tipo": mundo.tipo(n), "existe": True,
                      "poblacion": mundo.poblacion(n), "ano": mundo.asentamiento(n).ano, "zona": meta["zona"],
                      "bioma": meta["bioma"]} for n, meta in mundo.meta.items()]
        lista.sort(key=lambda x: (-x["poblacion"], x["id"]))
        if len(lista) == 1:
            lista.append({"id": 2, "nombre": SEGUNDA, "tipo": "aldea", "existe": False, "poblacion": 0,
                          "poblacion_para_fundarla": m.POBLACION_MAXIMA})
        return lista

    @app.get("/api/mundo")
    def mapa_mundo() -> dict:
        with mundo.cerrojo:
            return mundo.publico()

    @app.get("/api/mapa")
    def mapa(aldea: int = 1) -> dict:
        return mapa_publico(elegir(aldea))

    @app.get("/api/estado")
    def estado(aldea: int = 1) -> dict:
        with mundo.cerrojo:
            return estado_web(elegir(aldea))

    @app.get("/api/salud")
    def salud() -> dict:
        a = mundo.aldea
        jev = a.decisor if a.decisor is not a.respaldo else None
        return {
            "turno": a.turno,
            "ano": a.ano,
            "estacion": a.estacion,
            "poblacion": len(a.habitantes),
            "aldeas": [{"id": n, "nombre": x.nombre, "poblacion": len(x.habitantes)} for n, x in mundo.aldeas.items()],
            "grandes": [{"id": n, "nombre": g.nombre, "tipo": g.tipo, "poblacion": g.poblacion} for n, g in mundo.grandes.items()],
            "poblacion_mundo": sum(mundo.poblacion(n) for n in mundo.meta),
            "presupuesto": mundo.presupuesto.resumen(),
            "pausado": mundo.ajustes["pausado"],          # en pausa desde el panel: no es un fallo
            "velocidad": mundo.ajustes["velocidad"],
            "decisor": a.decisor.nombre,
            "fallos_seguidos": a.fallos_seguidos,
            "decisiones": dict(a.decisiones),
            "jev": {"llamadas": jev.llamadas, "errores": jev.errores, "coste_usd": round(jev.coste, 4)}
            if jev and hasattr(jev, "llamadas") else None,
        }

    @app.get("/api/habitante/{id}")
    def habitante(id: int, aldea: int = 1) -> dict:
        with mundo.cerrojo:
            a = elegir(aldea)
            ficha = ficha_notable(a, id) if isinstance(a, Grande) else ficha_habitante(a, id)
        if ficha is None:
            raise HTTPException(404, "Este habitante ya no vive en la aldea.")
        return ficha

    @app.get("/api/arbol")
    def arbol(aldea: int = 1) -> dict:
        with mundo.cerrojo:
            a = elegir(aldea)
            return arbol_grande(a) if isinstance(a, Grande) else arbol_publico(a)

    @app.get("/api/resumenes")
    def resumenes(aldea: int = 1) -> list[dict]:
        with mundo.cerrojo:
            return list(elegir(aldea).resumenes)

    @app.websocket("/ws")
    async def ws(websocket: WebSocket, aldea: int = 1) -> None:
        await websocket.accept()
        n = aldea if mundo.asentamiento(aldea) is not None else 1
        with mundo.cerrojo:
            a = mundo.asentamiento(n)
            inicio = {"tipo": "inicio", "aldea": n, "mapa": mapa_publico(a), "estado": estado_web(a)}
        await websocket.send_json(inicio)
        clientes[websocket] = n
        vigilar()
        try:
            while True:
                await websocket.receive_text()   # la web no manda nada; esto solo detecta la desconexión
        except WebSocketDisconnect:
            clientes.pop(websocket, None)
            vigilar()

    if WEB.exists():
        app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
    return app


def main() -> None:
    import uvicorn

    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.environ.get("JEVMURA_DB", "datos/mundo.db"))
    p.add_argument("--semilla", type=int, default=int(os.environ.get("JEVMURA_SEMILLA", "0")))
    p.add_argument("--hora-inicial", type=float, default=float(os.environ.get("JEVMURA_HORA_INICIAL", "7")),
                   help="hora del mundo a la que empieza un mundo nuevo")
    p.add_argument("--jev", action="store_true", default=os.environ.get("JEVMURA_JEV") == "1")
    p.add_argument("--puerto", type=int, default=8000)
    p.add_argument("--rapido", type=float, default=None, help="segundos por turno, para probar")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    decisor = None
    if args.jev:
        from .motor.jev import DecisorJev
        decisor = DecisorJev()
    mundo = Mundo(args.db, args.semilla, decisor, hora_inicial=args.hora_inicial)
    mundo.aplicar_ajustes()                  # velocidad y gasto máximo guardados desde el panel
    if args.rapido is not None:
        mundo.segundos_por_turno = args.rapido
    uvicorn.run(crear_app(mundo), host="0.0.0.0", port=args.puerto)


if __name__ == "__main__":
    main()
