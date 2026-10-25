"""Quién decide qué hace cada habitante adulto.

El motor prepara una situación con las opciones ya calculadas y el decisor solo elige una. Nunca
se acepta texto libre: la opción elegida tiene que estar en la lista. Cada decisión lleva un motivo
corto que la web enseña en la ficha del habitante.

`DecisorReglas` es el decisor sin Jev: sirve para probar el motor con años de simulación en pocos
minutos y como alternativa cuando Jev falla.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Protocol

from .modelos import PLURAL_OFICIO, RECURSO_OFICIO


@dataclass(frozen=True)
class Opcion:
    id: str              # "trabajar", "oficio:pescador", "construir:casa", "hablar:7"…
    tipo: str            # el id sin lo que va detrás de los dos puntos
    descripcion: str     # frase para Jev
    otro: int | None = None
    nombre_otro: str = ""
    relacion: float = 0.0


@dataclass(frozen=True)
class EstadoAldea:
    poblacion: int
    comida: int
    madera: int
    piedra: int
    dias_comida: float               # días que dura la comida guardada
    plazas_libres: int               # sitios libres en las casas
    oficios: dict[str, int]          # adultos en cada oficio
    oficios_necesarios: tuple[str, ...]   # oficios que faltan ahora, del más urgente al menos
    guardias_necesarios: int
    llenos: tuple[str, ...]          # recursos con el almacén lleno: trabajar en ellos no sirve
    muralla: int                     # tramos construidos de 20
    obra: str | None                 # obra en curso, en texto
    etapa: str = ""                  # etapa de la evolución de la aldea
    edificios: tuple[str, ...] = ()  # edificios que ya tiene (pozo, granero…)


@dataclass(frozen=True)
class Situacion:
    nombre: str
    edad: int
    sexo: str
    caracter: str
    oficio: str
    hambre: int
    energia: int
    salud: int
    animo: int
    pareja: str | None
    relaciones: tuple[tuple[str, int], ...]   # (nombre, puntos), las más fuertes primero
    aldea: EstadoAldea
    ano: int
    estacion: str
    hora: int
    sucesos: tuple[str, ...]         # lo último que ha pasado en la aldea
    opciones: tuple[Opcion, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Decision:
    opcion: Opcion
    motivo: str
    confianza: float | None = None   # la que da Jev, de 0 a 1; el decisor de reglas no la da


class Decisor(Protocol):
    nombre: str

    def decidir(self, situacion: Situacion) -> Decision: ...


# Cuánto suma cada carácter a cada tipo de opción.
SESGO_CARACTER: dict[str, dict[str, float]] = {
    "trabajador": {"trabajar": 0.4, "construir": 0.3, "descansar": -0.3},
    "perezoso": {"trabajar": -0.3, "descansar": 0.5, "hablar": 0.2},
    "sociable": {"hablar": 0.6, "ayudar": 0.3, "proponer_pareja": 0.3},
    "solitario": {"hablar": -0.3, "ayudar": -0.2, "explorar": 0.2},
    "valiente": {"explorar": 0.4, "discutir": 0.2},
    "prudente": {"explorar": -0.2, "quitar": -0.5, "discutir": -0.2},
}


class DecisorReglas:
    """Puntúa cada opción según las necesidades del habitante y de la aldea, y elige con algo de
    azar para que dos habitantes en la misma situación no hagan siempre lo mismo."""

    nombre = "reglas"

    def __init__(self, rng: random.Random | None = None, temperatura: float = 0.3):
        self.rng = rng or random.Random()
        self.temperatura = temperatura

    def decidir(self, situacion: Situacion) -> Decision:
        puntos = [self._puntuar(situacion, o) for o in situacion.opciones]
        mejor = max(puntos)
        pesos = [math.exp((p - mejor) / self.temperatura) for p in puntos]
        opcion = self.rng.choices(situacion.opciones, weights=pesos)[0]
        return Decision(opcion, motivo(situacion, opcion))

    def _puntuar(self, s: Situacion, o: Opcion) -> float:
        a = s.aldea
        necesarios = a.oficios_necesarios
        p = SESGO_CARACTER.get(s.caracter, {}).get(o.tipo, 0.0)
        if o.tipo == "trabajar":
            p += 1.0 + (0.5 if s.oficio in necesarios else 0.0)
            if RECURSO_OFICIO.get(s.oficio) in a.llenos:
                p -= 1.0
        elif o.tipo == "oficio":
            nuevo = o.id.split(":")[1]
            minimo = a.guardias_necesarios if s.oficio == "guardia" else 1
            sobra = s.oficio not in necesarios and (a.oficios.get(s.oficio, 0) > minimo
                                                    or RECURSO_OFICIO.get(s.oficio) in a.llenos)
            if nuevo in necesarios and sobra:
                p += 2.0 - 0.3 * necesarios.index(nuevo)
            else:
                p -= 2.0
        elif o.tipo == "construir":
            p += 1.6 if o.id != "construir:muralla" else 0.8
            if a.dias_comida < 5:
                p -= 1.5                      # con poca comida, primero hay que sacar comida
        elif o.tipo == "descansar":
            p += 1.5 if s.energia < 35 else 0.2 if s.energia < 60 else -1.0
        elif o.tipo == "comer":
            p += 1.2 if s.hambre > 40 else -1.0
        elif o.tipo == "hablar":
            p += -0.2 + o.relacion / 200 + (0.8 if s.animo < 40 else 0.0)
        elif o.tipo == "ayudar":
            p += 0.2 + o.relacion / 150
        elif o.tipo == "discutir":
            p += -0.3 + (0.4 if s.animo < 35 else 0.0) - o.relacion / 100
        elif o.tipo == "quitar":
            p += 0.8 if s.hambre > 60 else -2.0
        elif o.tipo == "proponer_pareja":
            p += 1.0 + o.relacion / 100
        elif o.tipo == "explorar":
            p += -0.6
        elif o.tipo == "marcharse":
            p += -0.2 if s.pareja is None else -3.0
        return p


def motivo(s: Situacion, o: Opcion) -> str:
    """Motivo corto en lenguaje llano para una decisión del decisor de reglas."""
    cansado = "cansada" if s.sexo == "m" else "cansado"
    if o.tipo == "trabajar":
        recurso = RECURSO_OFICIO.get(s.oficio)
        if s.oficio in s.aldea.oficios_necesarios:
            return f"A la aldea le hace falta {recurso}" if recurso else "Hacen falta más guardias"
        if recurso in s.aldea.llenos:
            return "No tiene nada mejor que hacer"
        return "Toca trabajar"
    if o.tipo == "oficio":
        return f"Faltan {PLURAL_OFICIO[o.id.split(':')[1]]} en la aldea"
    if o.tipo == "construir":
        if o.id.count(":") == 2:              # obras de la evolución: lo dice su descripción
            return o.descripcion.split(":")[0]
        return "Hay que reforzar la muralla" if o.id == "construir:muralla" else "La aldea necesita otra casa"
    if o.tipo == "descansar":
        return f"Está {cansado}"
    if o.tipo == "comer":
        return "Tiene hambre"
    if o.tipo == "hablar":
        return f"Quiere pasar un rato con {o.nombre_otro}"
    if o.tipo == "ayudar":
        return f"{o.nombre_otro} necesita una mano"
    if o.tipo == "discutir":
        return f"No soporta a {o.nombre_otro}"
    if o.tipo == "quitar":
        return "Tiene hambre y nadie mira"
    if o.tipo == "proponer_pareja":
        return f"Se ha enamorado de {o.nombre_otro}"
    if o.tipo == "explorar":
        return "Quiere ver qué hay más allá del bosque"
    if o.tipo == "marcharse":
        return "Quiere probar suerte en otra aldea"
    return ""
