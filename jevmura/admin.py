"""Panel de administración: entrar con contraseña, acelerar o pausar el mundo, ver y limitar el
gasto en Jev y el estado del servidor.

La contraseña llega en la variable de entorno `ALDEA_ADMIN_CLAVE`.
Sin ella, el panel está cerrado. Al entrar, el servidor da una cookie firmada con la contraseña
que dura 7 días; así la sesión sigue aunque se reinicie el contenedor, y cambiar la contraseña
cierra todas las sesiones.

- `GET  /api/admin/sesion`: si el panel está configurado y si ya se ha entrado.
- `POST /api/admin/entrar`: `{clave}`. Tras 5 fallos desde la misma dirección, espera 15 minutos.
- `POST /api/admin/salir`
- `GET  /api/admin/estado`: tiempo, gasto, presupuesto y servidor.
- `POST /api/admin/ajustes`: `{velocidad?, pausado?, usd_dia?, jev?}`. Se guardan con el mundo.
- `POST /api/admin/guardar`: guarda el mundo ahora.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from .motor import modelos as m
from .mundo.mundo import COSTE_LLAMADA, VELOCIDADES, Mundo

COOKIE = "aldea_admin"
DURACION = 7 * 24 * 3600
FALLOS_MAXIMOS = 5
ESPERA_FALLOS = 15 * 60
USD_DIA_MAXIMO = 5.0


class Entrada(BaseModel):
    clave: str


class Ajustes(BaseModel):
    velocidad: int | None = None
    pausado: bool | None = None
    usd_dia: float | None = None
    jev: bool | None = None


def crear_admin(mundo: Mundo, conectados: Callable[[], int]) -> APIRouter:
    r = APIRouter(prefix="/api/admin")
    fallos: dict[str, list[float]] = {}

    def clave() -> str:
        return os.environ.get("ALDEA_ADMIN_CLAVE", "")

    def firma(hasta: int) -> str:
        return hmac.new(clave().encode(), f"admin:{hasta}".encode(), hashlib.sha256).hexdigest()

    def dentro(request: Request) -> bool:
        valor = request.cookies.get(COOKIE, "")
        hasta, _, f = valor.partition(".")
        if not clave() or not hasta.isdigit() or int(hasta) < time.time():
            return False
        return hmac.compare_digest(f, firma(int(hasta)))

    def exigir(request: Request) -> None:
        if not dentro(request):
            raise HTTPException(401, "Tienes que entrar con la contraseña.")

    def direccion(request: Request) -> str:
        reenviada = request.headers.get("x-forwarded-for", "")
        return reenviada.split(",")[0].strip() or (request.client.host if request.client else "?")

    @r.get("/sesion")
    def sesion(request: Request) -> dict:
        return {"configurado": bool(clave()), "dentro": dentro(request)}

    @r.post("/entrar")
    def entrar(datos: Entrada, request: Request, response: Response) -> dict:
        if not clave():
            raise HTTPException(503, "El panel no tiene contraseña configurada en el servidor.")
        ip = direccion(request)
        ahora = time.time()
        recientes = [t for t in fallos.get(ip, []) if ahora - t < ESPERA_FALLOS]
        if len(recientes) >= FALLOS_MAXIMOS:
            raise HTTPException(429, "Demasiados intentos. Vuelve a probar dentro de 15 minutos.")
        if not hmac.compare_digest(datos.clave.encode(), clave().encode()):
            fallos[ip] = recientes + [ahora]
            raise HTTPException(401, "La contraseña no es correcta.")
        fallos.pop(ip, None)
        hasta = int(ahora + DURACION)
        segura = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        response.set_cookie(COOKIE, f"{hasta}.{firma(hasta)}", max_age=DURACION, httponly=True,
                            secure=segura, samesite="strict", path="/api/admin")
        return {"dentro": True}

    @r.post("/salir")
    def salir(response: Response) -> dict:
        response.delete_cookie(COOKIE, path="/api/admin")
        return {"dentro": False}

    def estado() -> dict:
        a = mundo.aldea
        jev = mundo.jev if mundo.jev is not None and hasattr(mundo.jev, "llamadas") else None
        hoy = mundo.gasto.get(time.strftime("%Y-%m-%d"), {"llamadas": 0, "coste": 0.0})
        decisiones: dict[str, int] = {}
        for aldea in mundo.aldeas.values():
            for quien, n in aldea.decisiones.items():
                decisiones[quien] = decisiones.get(quien, 0) + n
        bases = []
        for fichero in sorted(os.listdir(mundo.carpeta)):
            if fichero.endswith(".db"):
                bases.append(os.path.getsize(os.path.join(mundo.carpeta, fichero)))
        spt = mundo.segundos_por_turno
        return {
            "ajustes": mundo.ajustes,
            "velocidades": VELOCIDADES,
            "usd_dia_maximo": USD_DIA_MAXIMO,
            "tiempo": {
                "ano": a.ano, "estacion": a.estacion, "dia": a.dia % m.DIAS_POR_ANO + 1, "hora": a.hora,
                "turno": a.turno, "segundos_por_turno": spt,
                "turnos_por_segundo": round(mundo.turnos_por_segundo(), 2),
                "pedidos_por_segundo": round(1 / spt, 2) if spt else None,
                "ms_por_turno": round(mundo.ms_por_turno, 1),
                "minutos_por_dia": round(m.TURNOS_POR_DIA * spt / 60, 1),
                "horas_por_ano": round(m.TURNOS_POR_ANO * spt / 3600, 1),
            },
            "jev": {
                "conectado": jev is not None,
                "llamadas": jev.llamadas if jev else 0,
                "errores": jev.errores if jev else 0,
                "coste_total": round(jev.coste, 4) if jev else 0.0,
                "coste_llamada": round(jev.coste / jev.llamadas, 6) if jev and jev.llamadas else COSTE_LLAMADA,
                "hoy": {"llamadas": hoy["llamadas"], "coste": round(hoy["coste"], 4)},
                "fallos_seguidos": a.fallos_seguidos,
                "decisiones": decisiones,
            },
            "presupuesto": mundo.presupuesto.resumen(),
            "gasto": [{"dia": d, "llamadas": g["llamadas"], "coste": round(g["coste"], 4)}
                      for d, g in sorted(mundo.gasto.items())[-30:]],
            "servidor": {
                "arrancado_hace": round(time.time() - mundo.arrancado),
                "guardado_hace": round(time.time() - mundo.guardado_en) if mundo.guardado_en else None,
                "bases": len(bases), "bases_kb": round(sum(bases) / 1024),
                "asentamientos": len(mundo.meta), "aldeas": len(mundo.aldeas), "grandes": len(mundo.grandes),
                "poblacion": sum(mundo.poblacion(n) for n in mundo.meta),
                "conectados": conectados(),
            },
        }

    @r.get("/estado")
    def ver(request: Request) -> dict:
        exigir(request)
        with mundo.cerrojo:
            return estado()

    @r.post("/ajustes")
    def ajustar(datos: Ajustes, request: Request) -> dict:
        exigir(request)
        if datos.velocidad is not None and datos.velocidad not in VELOCIDADES:
            raise HTTPException(422, "Esa velocidad no está entre las que se pueden elegir.")
        if datos.usd_dia is not None and not 0 <= datos.usd_dia <= USD_DIA_MAXIMO:
            raise HTTPException(422, f"El gasto al día tiene que estar entre 0 y {USD_DIA_MAXIMO:.2f} USD.")
        with mundo.cerrojo:
            for campo, valor in datos.model_dump(exclude_none=True).items():
                mundo.ajustes[campo] = round(valor, 2) if campo == "usd_dia" else valor
            mundo.aplicar_ajustes()
            mundo.guardar()
            return estado()

    @r.post("/guardar")
    def guardar(request: Request) -> dict:
        exigir(request)
        with mundo.cerrojo:
            mundo.guardar()
            return estado()

    return r
