"""Mapa de la aldea: 64 × 48 casillas de 16 píxeles.

Se genera una sola vez a partir de la semilla del mundo y después no cambia de forma. Lo que sí
cambia (árboles cortados, casas nuevas, tramos de muralla) lo guarda la aldea.

Zonas: bosque en los bordes, aldea en el centro con el sitio de la muralla alrededor, campos al
este, río con molino y puente en el borde este y cantera al sur.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .modelos import TRAMOS_MURALLA

ANCHO = 64
ALTO = 48
CENTRO = (30, 24)
RADIO_MURALLA = 12               # la muralla es un cuadrado de 25 × 25 casillas alrededor de la plaza

# Sitios para casas alrededor de la plaza, del más cercano al más lejano. Evitan los caminos.
SOLARES = [(-5, -4), (5, -4), (-5, 4), (5, 4),
           (-9, -3), (9, -3), (-9, 3), (9, 3), (-3, -8), (3, -8), (-3, 8), (3, 8)]


@dataclass
class Mapa:
    casillas: list[list[str]]                # [y][x]: hierba, agua, bosque, campo, cantera, camino, plaza
    arboles: dict[tuple[int, int], float]    # crecimiento de 0 (tocón) a 1 (se puede cortar)
    almacen: tuple[int, int]
    molino: tuple[int, int] | None
    solares: list[tuple[int, int]]
    muralla: list[tuple[int, int]]           # casilla central de cada tramo, en orden alrededor de la aldea
    tramos: list[list[tuple[int, int]]]      # casillas que ocupa cada tramo, para dibujarlo
    campos: list[tuple[int, int]]
    orillas: list[tuple[int, int]]           # sitios de pesca
    cantera: list[tuple[int, int]]
    salidas: list[tuple[int, int]]           # bordes por donde se sale a explorar o a marcharse
    puente: tuple[int, int] | None           # centro del puente sobre el río
    bioma: str = "pradera"
    # Lo que añaden los formatos nuevos (motor/formatos.py). El mapa clásico no los usa.
    formato: str = "clasica"
    sitios: dict = field(default_factory=dict)        # edificio de la evolución → casilla
    faroles: list = field(default_factory=list)
    huertos: tuple | None = None
    puentes: list = field(default_factory=list)       # todos los puentes (el clásico solo tiene uno)
    muros_fijos: list = field(default_factory=list)   # muralla interior de las ciudades, siempre entera


def _tramos_muralla() -> list[list[tuple[int, int]]]:
    """Reparte el contorno del cuadrado en 20 tramos seguidos, dejando huecos para los caminos."""
    cx, cy = CENTRO
    r = RADIO_MURALLA
    x0, x1, y0, y1 = cx - r, cx + r, cy - r, cy + r
    contorno = ([(x, y0) for x in range(x0, x1)] + [(x1, y) for y in range(y0, y1)]
                + [(x, y1) for x in range(x1, x0, -1)] + [(x0, y) for y in range(y1, y0, -1)])
    puertas = {(cx, y0), (cx, y1), (x0, cy), (x1, cy)}
    contorno = [p for p in contorno if p not in puertas]
    n = len(contorno)
    return [contorno[k * n // TRAMOS_MURALLA:(k + 1) * n // TRAMOS_MURALLA] for k in range(TRAMOS_MURALLA)]


# Terrenos del mundo grande. Cambian cuántos árboles hay; el dibujo del suelo lo elige la web.
BIOMAS = ("pradera", "bosque", "desierto", "nieve", "pantano")
DENSIDAD_BOSQUE = {"pradera": 1.0, "bosque": 1.25, "desierto": 0.3, "nieve": 0.8, "pantano": 0.6}


def generar_mapa(semilla: int, bioma: str = "pradera") -> Mapa:
    rng = random.Random(semilla * 7919 + 1)
    c = [["hierba"] * ANCHO for _ in range(ALTO)]
    cx, cy = CENTRO

    fase = rng.uniform(0, 2 * math.pi)
    orillas = []
    rio = []                                 # primera casilla de agua de cada fila
    for y in range(ALTO):
        x0 = 55 + round(2 * math.sin(y / 6 + fase))
        rio.append(x0)
        for x in range(x0, min(ANCHO, x0 + 3)):
            c[y][x] = "agua"
        if 3 <= y < ALTO - 3 and y % 3 == 0 and y != cy:
            orillas.append((x0 - 1, y))
    molino = (55 + round(2 * math.sin(cy / 6 + fase)) - 1, cy)

    campos = []
    for y in range(15, 34):
        for x in range(43, 51):
            c[y][x] = "campo"
            campos.append((x, y))

    cantera = []
    for y in range(39, 46):
        for x in range(14, 23):
            c[y][x] = "cantera"
            if (x + y) % 2 == 0:
                cantera.append((x, y))

    # Dentro de la muralla, caminos rectos de una casilla, para que no pisen los solares. Fuera,
    # caminos de dos casillas que serpentean y llegan hasta el borde del mapa.
    r = RADIO_MURALLA
    for x in range(cx - r, cx + r + 1):
        c[cy][x] = "camino"                  # de la puerta oeste a la puerta este y los campos
    for y in range(cy - r, cy + r + 1):
        c[y][cx] = "camino"                  # de la puerta norte a la puerta sur
    oeste = _ondulacion(rng, cx - r)
    for x in range(cx - r):
        _pintar(c, x, cy + oeste[x], 1, 2)
    norte = _ondulacion(rng, cy - r)
    for y in range(cy - r):
        _pintar(c, cx + norte[y], y, 2, 1)
    sur = _ondulacion(rng, ALTO - (cy + r + 1))
    for i, y in enumerate(range(cy + r + 1, ALTO)):
        _pintar(c, cx + sur[-1 - i], y, 2, 1)
    cantera_camino = _ondulacion(rng, cx - 21, 1)
    for i, x in enumerate(range(22, cx + 1)):
        _pintar(c, x, 38 + cantera_camino[i], 1, 2)

    # Camino del noreste: sale del camino norte, cruza el río por un puente y sigue hasta el borde.
    yp = 9
    xr = rio[yp]
    este = _ondulacion(rng, xr - 2 - cx)
    for i, x in enumerate(range(cx, xr - 2)):
        _pintar(c, x, yp + este[i], 1, 2)
    for x in range(xr - 2, ANCHO):
        _pintar(c, x, yp, 1, 2)
    puente = (xr + 1, yp)

    for y in range(cy - 3, cy + 4):
        for x in range(cx - 3, cx + 4):
            if abs(x - cx) + abs(y - cy) < 6:  # plaza de 7 × 7 con las esquinas recortadas
                c[y][x] = "plaza"

    # Bosque espeso en los cuatro bordes, al otro lado del río y árboles sueltos por la hierba.
    x0, x1, y0, y1 = cx - r - 1, cx + r + 1, cy - r - 1, cy + r + 1
    arboles = {}
    for y in range(ALTO):
        for x in range(ANCHO):
            if c[y][x] != "hierba" or (x + 1 < ANCHO and c[y][x + 1] == "agua"):
                continue                     # la orilla queda libre para pescar
            borde = min(x, y, ALTO - 1 - y)
            if x > rio[y] + 3 or borde < 3:
                p = 0.8
            elif x < 12 or y < 7 or y > ALTO - 4:
                p = 0.55
            elif not (x0 <= x <= x1 and y0 <= y <= y1) and _rodeada_de_hierba(c, x, y):
                p = 0.05
            else:
                p = 0
            if rng.random() < p * DENSIDAD_BOSQUE[bioma]:
                c[y][x] = "bosque"
                arboles[(x, y)] = 1.0

    tramos = _tramos_muralla()

    return Mapa(
        casillas=c, arboles=arboles, almacen=CENTRO, molino=molino,
        solares=[(cx + dx, cy + dy) for dx, dy in SOLARES],
        muralla=[t[len(t) // 2] for t in tramos], tramos=tramos,
        campos=campos, orillas=orillas, cantera=cantera,
        salidas=[(0, cy), (cx, 0), (cx, ALTO - 1)], puente=puente, bioma=bioma,
    )


def _ondulacion(rng: random.Random, n: int, amplitud: float = 2) -> list[int]:
    """Desvío del camino en cada una de sus n casillas: suave y cero en los dos extremos."""
    fase = rng.uniform(0, 2 * math.pi)
    return [round(amplitud * math.sin(math.pi * i / max(1, n - 1)) * math.sin(i / 5 + fase)) for i in range(n)]


def _pintar(c: list[list[str]], x: int, y: int, ancho: int, alto: int) -> None:
    """Camino de ancho × alto casillas desde (x, y). Solo pisa hierba."""
    for yy in range(y, y + alto):
        for xx in range(x, x + ancho):
            if 0 <= xx < ANCHO and 0 <= yy < ALTO and c[yy][xx] in ("hierba", "camino"):
                c[yy][xx] = "camino"


def _rodeada_de_hierba(c: list[list[str]], x: int, y: int) -> bool:
    return all(c[yy][xx] == "hierba" for yy in range(max(0, y - 1), min(ALTO, y + 2))
               for xx in range(max(0, x - 1), min(ANCHO, x + 2)))
