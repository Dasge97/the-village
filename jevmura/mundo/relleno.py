"""Terreno de las zonas del mundo donde no hay nadie, para el mapa continuo de la web.

El mundo entero es un solo mapa: cada zona mide 96 × 72 casillas y en las ocupadas está el mapa de
su asentamiento. Las demás se rellenan aquí con su terreno (más o menos bosque según el bioma,
claros y alguna charca) y con los caminos que unen los asentamientos, que cruzan las zonas
vacías de un asentamiento a otro. Es solo para mirar: nadie vive ni trabaja en el relleno.

Todo sale de la semilla y de la posición, así que una zona se ve siempre igual.
"""

from __future__ import annotations

import math
import random

from ..motor.formatos import ZONA
from ..motor.mapa import DENSIDAD_BOSQUE

LETRA = {"hierba": "h", "bosque": "b", "agua": "a", "camino": "m"}
BOSQUE_BASE = {"pradera": 0.25, "bosque": 0.6, "desierto": 0.06, "nieve": 0.3, "pantano": 0.3}


class _Ruido:
    """El mismo ruido suave que `zonas._ruido`, pero guardando los valores de la rejilla: una zona
    pide 7.000 casillas y la rejilla solo tiene unas pocas decenas de puntos."""

    def __init__(self, semilla: int):
        self.semilla = semilla
        self.valores: dict[tuple[int, int], float] = {}

    def _valor(self, ix: int, iy: int) -> float:
        v = self.valores.get((ix, iy))
        if v is None:
            v = self.valores[(ix, iy)] = random.Random(self.semilla * 1_000_003 + ix * 7919 + iy * 104_729).random()
        return v

    def __call__(self, x: float, y: float) -> float:
        x0, y0 = math.floor(x), math.floor(y)
        fx, fy = x - x0, y - y0
        sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = self._valor(x0, y0) + (self._valor(x0 + 1, y0) - self._valor(x0, y0)) * sx
        b = self._valor(x0, y0 + 1) + (self._valor(x0 + 1, y0 + 1) - self._valor(x0, y0 + 1)) * sx
        return a + (b - a) * sy


def relleno(semilla: int, zx: int, zy: int, bioma: str, caminos: list[tuple[tuple[float, float], tuple[float, float]]],
            hueco: tuple[int, int, int, int] | None = None) -> dict:
    """Las casillas de la zona (zx, zy). `caminos`: tramos entre centros de asentamientos, en
    casillas del mundo. `hueco`: rectángulo (x0, y0, x1, y1) de la zona, en casillas de la zona,
    donde va el mapa de una aldea y no hace falta relleno."""
    ancho, alto = ZONA
    ox, oy = zx * ancho, zy * alto
    rng = random.Random(semilla * 7_919 + zx * 104_729 + zy * 1_299_709)
    c = [["hierba"] * ancho for _ in range(alto)]
    base = BOSQUE_BASE.get(bioma, 0.25)
    ruido = _Ruido(semilla + 5)
    for y in range(alto):
        for x in range(ancho):
            # Manchas de bosque y claros que siguen de una zona a la de al lado (el ruido va en
            # casillas del mundo).
            manchas = ruido((ox + x) / 14, (oy + y) / 14)
            p = base + (manchas - 0.5) * 0.9
            if rng.random() < max(0.0, min(0.9, p)) * DENSIDAD_BOSQUE.get(bioma, 1.0):
                c[y][x] = "bosque"
    # Alguna charca.
    if rng.random() < (0.5 if bioma in ("pantano", "pradera") else 0.2):
        cx, cy, rx, ry = rng.randint(10, ancho - 11), rng.randint(8, alto - 9), rng.randint(2, 5), rng.randint(2, 4)
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    c[y][x] = "agua"
    # Caminos entre asentamientos: rectos con alguna curva, de dos casillas de ancho.
    for (ax, ay), (bx, by) in caminos:
        if max(ax, bx) < ox - 2 or min(ax, bx) > ox + ancho + 2 or max(ay, by) < oy - 2 or min(ay, by) > oy + alto + 2:
            continue
        largo = max(1, int(math.dist((ax, ay), (bx, by))))
        fase = (ax * 7 + by * 13) % 6.28
        for i in range(largo + 1):
            t = i / largo
            curva = 3 * math.sin(t * math.pi) * math.sin(t * 9 + fase)
            nx, ny = -(by - ay) / largo, (bx - ax) / largo        # perpendicular, para la curva
            x = round(ax + (bx - ax) * t + nx * curva) - ox
            y = round(ay + (by - ay) * t + ny * curva) - oy
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if 0 <= x + dx < ancho and 0 <= y + dy < alto and c[y + dy][x + dx] != "agua":
                    c[y + dy][x + dx] = "camino"
    if hueco:
        x0, y0, x1, y1 = hueco
        for y in range(max(0, y0), min(alto, y1)):
            for x in range(max(0, x0), min(ancho, x1)):
                c[y][x] = "hierba"
    casillas = ["".join(LETRA[t] for t in fila) for fila in c]
    arboles = [(x, y) for y, fila in enumerate(casillas) for x, t in enumerate(fila) if t == "b"]
    return {"zona": [zx, zy], "origen": [ox, oy], "ancho": ancho, "alto": alto, "bioma": bioma,
            "casillas": casillas, "arboles": arboles}
