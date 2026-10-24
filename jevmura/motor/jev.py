"""Decisor con Jev (`typesafe/jev-1.14`) por la API de decisiones de OpenRouter.

Se le manda la situación del habitante como datos y una pregunta de tipo "choice" con las
opciones que ha calculado el motor. Jev devuelve la opción elegida, la probabilidad de cada una
y su confianza. No escribe texto, así que el motivo sale de la misma plantilla que usa el
decisor de reglas.

Si Jev tarda, devuelve un error o elige algo que no está en la lista, se lanza una excepción y
la aldea decide con el decisor de reglas. El mundo nunca se para por Jev.

La clave se lee de la variable de entorno `OPENROUTER_API_KEY`.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict

import httpx

from .decisores import Decision, Situacion, motivo

URL = "https://openrouter.ai/api/alpha/decisions"
MODELO = "typesafe/jev-1.14"

OBJETIVO = (
    "Eres un habitante de una pequeña aldea de estilo Japón feudal. Quieres una vida buena y "
    "completa, y que la aldea dure para siempre. Eso no es solo trabajar: hace falta comida, leña "
    "para el invierno y guardias contra los monstruos, pero también casas para que las familias "
    "tengan hijos, amistades, pareja y buen ánimo. Con el ánimo bajo se trabaja peor, y trabajar "
    "sin parar baja el ánimo. Compórtate como una persona real con tu carácter."
)

INSTRUCCIONES = (
    "Elige lo que va a hacer este habitante durante las próximas dos horas. Cada opción explica lo "
    "que consigue. Ten en cuenta su carácter (un sociable habla más, un perezoso descansa más, un "
    "valiente se arriesga más), su hambre, energía, salud y ánimo, lo que le falta a la aldea "
    "(oficios_necesarios), si hay una obra que nadie termina y sus relaciones. Comer y descansar "
    "cuando es urgente ya lo hacen las reglas solas."
)


def clave_openrouter() -> str:
    clave = os.environ.get("OPENROUTER_API_KEY", "")
    if not clave:
        raise RuntimeError("falta la variable de entorno OPENROUTER_API_KEY con la clave de OpenRouter")
    return clave


def estado(s: Situacion) -> dict:
    """La situación como datos para Jev, sin las opciones (van en la pregunta)."""
    datos = asdict(s)
    datos.pop("opciones")
    datos["sexo"] = "mujer" if s.sexo == "m" else "hombre"
    datos["relaciones"] = [f"{nombre}: {puntos}" for nombre, puntos in s.relaciones]
    datos["sucesos"] = list(s.sucesos) or ["nada destacable"]
    datos["escala"] = ("necesidades de 0 a 100; en hambre más es peor, en el resto más es mejor; "
                       "relaciones de -100 (enemigos) a 100 (inseparables)")
    return {"objetivo": OBJETIVO, **datos}


class DecisorJev:
    nombre = "jev"

    def __init__(self, modelo: str = MODELO, timeout_s: float = 8.0):
        self.modelo = modelo
        self.timeout_s = timeout_s
        self.cliente = httpx.Client(timeout=timeout_s)
        self.llamadas = 0
        self.errores = 0
        self.coste = 0.0
        self.segundos = 0.0

    def elegir(self, estado: dict, opciones: dict[str, str], instrucciones: str) -> tuple[str, float | None]:
        """Una elección cualquiera entre `opciones` (id → qué consigue), por ejemplo la del consejo
        de un pueblo. Devuelve la opción elegida y la confianza de Jev."""
        cuerpo = {"model": self.modelo, "state": estado,
                  "questions": {"eleccion": {"type": "choice", "instructions": instrucciones, "criteria": opciones}}}
        inicio = time.perf_counter()
        try:
            r = self.cliente.post(URL, headers={"Authorization": f"Bearer {clave_openrouter()}"}, json=cuerpo)
            r.raise_for_status()
            datos = r.json()
        except Exception:
            self.errores += 1
            raise
        finally:
            self.segundos += time.perf_counter() - inicio
        self.llamadas += 1
        self.coste += datos.get("usage", {}).get("cost") or 0.0
        respuesta = datos.get("answers", {}).get("eleccion", {})
        if respuesta.get("choice") not in opciones:
            self.errores += 1
            raise ValueError(f"Jev ha elegido una opción que no existe: {respuesta.get('choice')!r}")
        return respuesta["choice"], respuesta.get("confidence")

    def decidir(self, situacion: Situacion) -> Decision:
        por_id = {o.id: o for o in situacion.opciones}
        cuerpo = {
            "model": self.modelo,
            "state": estado(situacion),
            "questions": {"accion": {
                "type": "choice",
                "instructions": INSTRUCCIONES,
                "criteria": {o.id: o.descripcion for o in situacion.opciones},
            }},
        }
        inicio = time.perf_counter()
        try:
            r = self.cliente.post(URL, headers={"Authorization": f"Bearer {clave_openrouter()}"}, json=cuerpo)
            r.raise_for_status()
            datos = r.json()
        except Exception:
            self.errores += 1
            raise
        finally:
            self.segundos += time.perf_counter() - inicio
        self.llamadas += 1
        self.coste += datos.get("usage", {}).get("cost") or 0.0
        respuesta = datos.get("answers", {}).get("accion", {})
        opcion = por_id.get(respuesta.get("choice"))
        if opcion is None:
            self.errores += 1
            raise ValueError(f"Jev ha elegido una opción que no existe: {respuesta.get('choice')!r}")
        return Decision(opcion, motivo(situacion, opcion), respuesta.get("confidence"))
