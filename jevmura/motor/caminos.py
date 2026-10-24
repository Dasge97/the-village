"""Rutas por el mapa: por dónde va un habitante de un sitio a otro.

Cada casilla tiene un coste de paso: los caminos, la plaza y el puente son lo más barato, la
hierba y el bosque cuestan más, y el agua, las casas, el almacén y los tramos de muralla ya
construidos no se pueden pisar. La ruta es la más barata con pasos en 8 direcciones, sin cortar
esquinas de lo que no se puede pisar.

La búsqueda es A* y da un poco más de peso a la distancia que falta, para explorar menos casillas:
la ruta puede no ser la más barata de todas, pero va por los caminos y es casi igual de corta. Las
rutas se guardan, porque muchas se repiten, y se olvidan cuando cambian las casas o la muralla.
"""

from __future__ import annotations

import heapq
import math

from .mapa import Mapa

COSTE = {"camino": 1.0, "plaza": 1.0, "campo": 1.6, "cantera": 2.0, "hierba": 2.2, "bosque": 3.5}
BLOQUEADA = math.inf
DIAGONAL = 1.414
MAX_GUARDADAS = 4000
PESO_RESTO = 1.3             # más de 1: explora menos casillas a cambio de rutas algo menos exactas


class Caminos:
    def __init__(self, mapa: Mapa):
        self.mapa = mapa
        self.alto = len(mapa.casillas)
        self.ancho = len(mapa.casillas[0])
        self.clave = None
        self.coste: list[float] = []             # una fila detrás de otra: casilla (x, y) en y * ancho + x
        self.guardadas: dict[tuple[int, int], list[list[int]]] = {}

    def preparar(self, casas: list, muralla: int) -> None:
        """Rehace la tabla de costes si han cambiado las casas o la muralla."""
        clave = (tuple((c.x, c.y, c.quemada) for c in casas), muralla)
        if clave == self.clave:
            return
        self.clave = clave
        self.guardadas = {}
        m = self.mapa
        w = self.ancho
        self.coste = [COSTE.get(t, BLOQUEADA) for fila in m.casillas for t in fila]
        px, py = m.puente
        for y in (py, py + 1):                  # el puente: las casillas de agua bajo los tablones
            for x in range(px - 3, px + 4):
                if 0 <= x < w and m.casillas[y][x] == "agua":
                    self.coste[y * w + x] = COSTE["camino"]
        bloquear = []
        for c in casas:                          # la casa ocupa 4 × 3 casillas; se entra por delante
            bloquear += [(x, y) for x in range(c.x - 1, c.x + 3) for y in range(c.y - 2, c.y + 1)]
        ax, ay = m.almacen
        bloquear += [(x, y) for x in range(ax - 1, ax + 3) for y in range(ay - 7, ay - 1)]
        for tramo in m.tramos[:muralla]:
            bloquear += tramo
        for x, y in bloquear:
            if 0 <= x < w and 0 <= y < self.alto:
                self.coste[y * w + x] = BLOQUEADA

    def ruta(self, desde: tuple[float, float], hasta: tuple[float, float]) -> list[list[int]]:
        """Casillas por las que pasar de `desde` a `hasta`, sin la de salida. Si el destino no se
        puede pisar, se llega a la casilla libre más cercana. Si no hay ruta, lista vacía."""
        w, h = self.ancho, self.alto
        ix, iy = min(w - 1, max(0, round(desde[0]))), min(h - 1, max(0, round(desde[1])))
        fx, fy = min(w - 1, max(0, round(hasta[0]))), min(h - 1, max(0, round(hasta[1])))
        inicio, fin = iy * w + ix, fy * w + fx
        if self.coste[fin] == BLOQUEADA:
            fin = self._libre_cercana(fx, fy)
            if fin is None:
                return []
        if inicio == fin:
            return []
        if (inicio, fin) in self.guardadas:
            return [list(p) for p in self.guardadas[(inicio, fin)]]
        camino = self._buscar(inicio, fin)
        if len(self.guardadas) > MAX_GUARDADAS:
            self.guardadas = {}
        self.guardadas[(inicio, fin)] = camino
        return [list(p) for p in camino]

    def _buscar(self, inicio: int, fin: int) -> list[list[int]]:
        w, h = self.ancho, self.alto
        coste_casilla = self.coste
        fx, fy = fin % w, fin // w
        coste = {inicio: 0.0}
        de = {}
        abiertas = [(0.0, inicio)]
        cerradas = set()
        while abiertas:
            _, actual = heapq.heappop(abiertas)
            if actual == fin:
                break
            if actual in cerradas:
                continue
            cerradas.add(actual)
            x, y = actual % w, actual // w
            base = coste[actual]
            for dx in (-1, 0, 1):
                nx = x + dx
                if not 0 <= nx < w:
                    continue
                for dy in (-1, 0, 1):
                    ny = y + dy
                    if (dx == 0 and dy == 0) or not 0 <= ny < h:
                        continue
                    vecina = ny * w + nx
                    paso = coste_casilla[vecina]
                    if paso == BLOQUEADA:
                        continue
                    if dx and dy:
                        # No corta esquinas de casas ni muros.
                        if coste_casilla[y * w + nx] == BLOQUEADA or coste_casilla[ny * w + x] == BLOQUEADA:
                            continue
                        paso *= DIAGONAL
                    nuevo = base + paso
                    if nuevo < coste.get(vecina, math.inf):
                        coste[vecina] = nuevo
                        de[vecina] = actual
                        resto = max(abs(fx - nx), abs(fy - ny))   # cota por abajo: toda casilla cuesta al menos 1
                        heapq.heappush(abiertas, (nuevo + PESO_RESTO * resto, vecina))
        if fin not in de:
            return []
        camino = [fin]
        while de.get(camino[-1], inicio) != inicio:
            camino.append(de[camino[-1]])
        return [[p % w, p // w] for p in reversed(camino)]

    def _libre_cercana(self, x: int, y: int) -> int | None:
        w, h = self.ancho, self.alto
        for r in range(1, 5):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx, ny = x + dx, y + dy
                    if max(abs(dx), abs(dy)) == r and 0 <= nx < w and 0 <= ny < h and self.coste[ny * w + nx] != BLOQUEADA:
                        return ny * w + nx
        return None
