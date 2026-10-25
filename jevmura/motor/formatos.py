"""Mapas con formatos y tamaños distintos para las aldeas, pueblos, villas y ciudades nuevos.

`mapa.generar_mapa` hace el mapa de siempre («clásica»: plaza en el centro, muralla cuadrada y río
al este), y se queda así para las partidas guardadas, que guardan sus árboles por orden. Este
módulo hace los demás formatos. En vez de poner cada cosa en una casilla fija, la busca: primero
el agua, la plaza, los caminos y la muralla; después los campos y la cantera, en un sitio libre
junto a la muralla; luego los solares de las casas y los sitios de los edificios de la evolución,
de la plaza hacia fuera; y al final los árboles en lo que queda libre.

Formatos de aldea: «rio» (el río cruza por el medio, con dos puentes), «camino» (una calle larga
de punta a punta y la muralla alargada), «lago» (un lago junto a la plaza; en el desierto, un
oasis) y «claro» (un claro en el bosque con la muralla redonda y los campos dentro).
Pueblos, villas y ciudades: «pueblo» (calles que salen de la plaza en varias direcciones),
«villa» (dos plazas unidas por una calle y muralla más grande) y «ciudad» (calles en cuadrícula,
barrios y doble muralla).

Importante: una vez publicado, el generador de un formato no se puede cambiar. Las aldeas guardan
el crecimiento de sus árboles por orden y el mapa se vuelve a generar al cargar la partida: si el
mapa cambia, la partida se estropea. Para cambiar un formato, se añade otro con otro nombre
(«claro2») y el viejo se queda como está. Los pueblos, villas y ciudades no guardan nada del mapa
y sí se pueden cambiar.
"""

from __future__ import annotations

import math
import random

from .mapa import DENSIDAD_BOSQUE, Mapa, _ondulacion
from .modelos import TRAMOS_MURALLA

FORMATOS_ALDEA = ["rio", "camino", "lago", "claro"]
# Con qué probabilidad sale cada formato según el terreno (el resto, a partes iguales).
PREFERENCIAS = {"desierto": {"lago": 3}, "bosque": {"claro": 3}, "pantano": {"lago": 2}, "nieve": {"claro": 2}}
TAMANOS = {"aldea": ((60, 72), (44, 54))}
ZONA = (96, 72)          # casillas de una zona del mundo; un pueblo la llena, una villa ocupa 2 × 2
SOLARES = {"aldea": 12, "pueblo": 0, "villa": 0, "ciudad": 0}
# Lo que ocupa cada edificio de la evolución (ancho, alto) en casillas, contando desde su casilla
# de abajo en el centro.
HUELLAS = {"pozo": (1, 2), "granero": (3, 3), "taller": (4, 3), "vigia": (2, 2), "templo": (3, 3),
           "dojo": (4, 6), "mercado": (3, 3), "almacen": (4, 3)}
PLAZA_OBJETOS = [(-3, 2), (-4, -1), (-3, -1), (3, -2), (4, -2), (4, -1), (3, 3), (-3, -3)]   # como en la web


def elegir_formato(rng: random.Random, bioma: str) -> str:
    pesos = [PREFERENCIAS.get(bioma, {}).get(f, 1) for f in FORMATOS_ALDEA]
    return rng.choices(FORMATOS_ALDEA, weights=pesos)[0]


def formato_de_tipo(tipo: str) -> str:
    return {"pueblo": "pueblo", "villa": "villa", "ciudad": "ciudad"}[tipo]


class _Plano:
    """El mapa mientras se construye: casillas, lo reservado y lo que se va añadiendo."""

    def __init__(self, rng: random.Random, ancho: int, alto: int):
        self.rng, self.ancho, self.alto = rng, ancho, alto
        self.c = [["hierba"] * ancho for _ in range(alto)]
        self.reservado: set[tuple[int, int]] = set()
        self.puentes: list[tuple[int, int]] = []
        self.salidas: list[tuple[int, int]] = []

    def dentro(self, x: int, y: int) -> bool:
        return 0 <= x < self.ancho and 0 <= y < self.alto

    def es(self, x: int, y: int, *tipos: str) -> bool:
        return self.dentro(x, y) and self.c[y][x] in tipos

    def pintar(self, x: int, y: int, tipo: str, sobre: tuple[str, ...] = ("hierba",)) -> None:
        if self.dentro(x, y) and self.c[y][x] in sobre:
            self.c[y][x] = tipo

    def libre(self, casillas, tipos=("hierba",)) -> bool:
        return all(self.dentro(x, y) and self.c[y][x] in tipos and (x, y) not in self.reservado for x, y in casillas)


# ---- agua ----

def _rio_vertical(p: _Plano, x_centro: int) -> list[int]:
    """Río de 3 casillas de ancho de arriba abajo, con curvas suaves. Devuelve su primera casilla por fila."""
    fase = p.rng.uniform(0, 2 * math.pi)
    xs = []
    for y in range(p.alto):
        x0 = x_centro + round(2 * math.sin(y / 6 + fase))
        xs.append(x0)
        for x in range(x0, x0 + 3):
            p.pintar(x, y, "agua", ("hierba",))
    return xs


def _lago(p: _Plano, cx: int, cy: int, rx: int, ry: int) -> None:
    for y in range(cy - ry - 1, cy + ry + 2):
        for x in range(cx - rx - 1, cx + rx + 2):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + p.rng.uniform(-0.08, 0.08)
            if d <= 1:
                p.pintar(x, y, "agua")
    # Sin picos de una casilla: se quita el agua con una sola vecina de agua.
    for y in range(cy - ry - 1, cy + ry + 2):
        for x in range(cx - rx - 1, cx + rx + 2):
            if p.es(x, y, "agua") and sum(p.es(x + dx, y + dy, "agua") for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1:
                p.c[y][x] = "hierba"


# ---- muralla ----

def _anillo(p: _Plano, cx: int, cy: int, dentro_de) -> list[tuple[int, int]]:
    """Casillas del borde de una figura (las de dentro con alguna vecina fuera), en orden alrededor
    del centro. Sirve para cualquier figura convexa: rectángulo, octógono…"""
    borde = []
    for y in range(p.alto):
        for x in range(p.ancho):
            # Con las 8 vecinas, el borde sale seguido también en los lados en diagonal.
            if dentro_de(x - cx, y - cy) and any(not dentro_de(x + dx - cx, y + dy - cy)
                                                 for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                borde.append((x, y))
    borde.sort(key=lambda q: math.atan2(q[1] - cy, q[0] - cx))
    return borde


def _tramos(p: _Plano, borde: list[tuple[int, int]], n: int = TRAMOS_MURALLA) -> list[list[tuple[int, int]]]:
    """Reparte el borde (sin agua ni caminos, que son las puertas) en n tramos seguidos."""
    muro = [q for q in borde if p.es(*q, "hierba", "bosque")]
    total = len(muro)
    tramos = [muro[k * total // n:(k + 1) * total // n] for k in range(n)]
    return [t for t in tramos if t] or [[borde[0]]]


# ---- caminos ----

def _camino_recto(p: _Plano, x0: int, y0: int, x1: int, y1: int) -> None:
    """Camino de una casilla en línea recta (horizontal o vertical). Sobre el agua, puente."""
    pasos = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(pasos + 1):
        x = x0 + round((x1 - x0) * i / max(1, pasos))
        y = y0 + round((y1 - y0) * i / max(1, pasos))
        if p.es(x, y, "agua"):
            if y0 == y1 and not any(abs(b[0] - x) < 5 and b[1] == y for b in p.puentes):
                p.puentes.append((x, y))           # un camino que cruza el río por un puente
            continue
        p.pintar(x, y, "camino", ("hierba", "bosque"))


def _camino_fuera(p: _Plano, desde: tuple[int, int], direccion: tuple[int, int]) -> None:
    """Desde una puerta de la muralla hasta el borde del mapa: dos casillas de ancho y con curvas.
    Si cruza un río (de arriba abajo), deja un puente."""
    dx, dy = direccion
    x, y = desde
    if dx:
        n = (p.ancho - 1 - x) if dx > 0 else x
        onda = _ondulacion(p.rng, n + 1)
        for i in range(n + 1):
            xx, yy = x + dx * i, y + onda[i]
            for k in (0, 1):
                if p.es(xx, yy + k, "agua"):
                    if k == 0 and (xx - dx, yy) not in p.puentes and not any(abs(b[0] - xx) < 4 and b[1] == yy for b in p.puentes):
                        p.puentes.append((xx, yy))
                    continue
                p.pintar(xx, yy + k, "camino", ("hierba", "bosque"))
        p.salidas.append((x + dx * n, y))
    else:
        n = (p.alto - 1 - y) if dy > 0 else y
        onda = _ondulacion(p.rng, n + 1)
        for i in range(n + 1):
            xx, yy = x + onda[i], y + dy * i
            for k in (0, 1):
                if not p.es(xx + k, yy, "agua"):
                    p.pintar(xx + k, yy, "camino", ("hierba", "bosque"))
        p.salidas.append((x, y + dy * n))


def _plaza(p: _Plano, cx: int, cy: int, radio: int = 3) -> None:
    for y in range(cy - radio, cy + radio + 1):
        for x in range(cx - radio, cx + radio + 1):
            if abs(x - cx) + abs(y - cy) < 2 * radio:
                p.pintar(x, y, "plaza", ("hierba", "camino"))
    # El almacén (alto, encima de la plaza) y los puestos de alrededor no pueden quedar tapados.
    p.reservado.update((x, y) for x in range(cx - 2, cx + 3) for y in range(cy - 8, cy))
    for ox, oy in PLAZA_OBJETOS:
        p.reservado.update((cx + ox + dx, cy + oy + dy) for dx in (-1, 0, 1) for dy in (-1, 0))


# ---- zonas: campos, cantera, solares y edificios ----

def _rect_libre(p: _Plano, ancho: int, alto: int, cerca: tuple[int, int], fuera_de=None, tipos=("hierba",)):
    """El rectángulo libre de ancho × alto más cercano a `cerca`, que no toque lo de `fuera_de`."""
    candidatos = sorted(((x, y) for y in range(2, p.alto - alto - 2) for x in range(2, p.ancho - ancho - 2)),
                        key=lambda q: math.dist((q[0] + ancho / 2, q[1] + alto / 2), cerca))
    for x0, y0 in candidatos:
        casillas = [(x, y) for y in range(y0 - 1, y0 + alto + 1) for x in range(x0 - 1, x0 + ancho + 1)]
        if p.libre(casillas, tipos) and not (fuera_de and any(fuera_de(x, y) for x, y in casillas)):
            return (x0, y0), (x0 + ancho - 1, y0 + alto - 1)
    return None


def _huella(x: int, y: int, ancho: int, alto: int) -> list[tuple[int, int]]:
    """Casillas que ocupa algo apoyado en (x, y): centrado en x y hacia arriba desde y."""
    x0 = x - (ancho - 1) // 2
    return [(xx, yy) for xx in range(x0, x0 + ancho) for yy in range(y - alto + 1, y + 1)]


def _sitio(p: _Plano, ancho: int, alto: int, cerca: tuple[int, int], dentro=None, margen: int = 1):
    """La casilla libre más cercana a `cerca` donde cabe algo de ancho × alto (con margen alrededor)."""
    candidatos = sorted(((x, y) for y in range(3, p.alto - 2) for x in range(3, p.ancho - 3)),
                        key=lambda q: (math.dist(q, cerca), q))
    for x, y in candidatos:
        if dentro and not dentro(x, y):
            continue
        casillas = _huella(x, y + margen, ancho + 2 * margen, alto + 2 * margen)
        if p.libre(casillas, ("hierba", "bosque")):
            p.reservado.update(_huella(x, y, ancho, alto))
            p.reservado.update(casillas)
            return (x, y)
    return None


# ---- árboles, orillas y molino ----

def _arboles(p: _Plano, bioma: str, dentro_muralla) -> dict[tuple[int, int], float]:
    arboles = {}
    banda = max(6, p.ancho // 6)
    for y in range(p.alto):
        for x in range(p.ancho):
            if p.c[y][x] != "hierba" or (x, y) in p.reservado or dentro_muralla(x, y):
                continue
            if any(p.es(x + dx, y + dy, "agua") for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue                             # la orilla queda libre para pescar
            borde = min(x, y, p.ancho - 1 - x, p.alto - 1 - y)
            if borde < 3:
                prob = 0.8
            elif borde < banda:
                prob = 0.55
            elif all(p.es(xx, yy, "hierba") for xx in range(x - 1, x + 2) for yy in range(y - 1, y + 2)):
                prob = 0.05
            else:
                prob = 0
            if p.rng.random() < prob * DENSIDAD_BOSQUE[bioma]:
                p.c[y][x] = "bosque"
                arboles[(x, y)] = 1.0
    return arboles


def _orillas(p: _Plano) -> list[tuple[int, int]]:
    orillas = [(x, y) for y in range(2, p.alto - 2) for x in range(1, p.ancho - 1)
               if p.c[y][x] in ("hierba", "camino") and (x, y) not in p.reservado
               and any(p.es(x + dx, y + dy, "agua") for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    return orillas[::3] or orillas


def _molino(p: _Plano, cerca: tuple[int, int]) -> tuple[int, int] | None:
    """Una casilla de hierba con agua justo a su derecha y sitio a su izquierda para el edificio."""
    candidatos = [(x, y) for y in range(5, p.alto - 3) for x in range(5, p.ancho - 2)
                  if p.es(x + 1, y, "agua") and p.libre([(x - k, y - j) for k in range(4) for j in range(4)], ("hierba",))]
    if not candidatos:
        return None
    x, y = min(candidatos, key=lambda q: math.dist(q, cerca))
    p.reservado.update((x - k, y - j) for k in range(5) for j in range(5))
    return x, y


# ---- el mapa ----

def generar(semilla: int, bioma: str, formato: str, tipo: str = "aldea", huella: int = 1) -> Mapa:
    """`huella`: lado en zonas de un pueblo, villa o ciudad; su mapa mide huella × una zona."""
    rng = random.Random(semilla * 104729 + sum(map(ord, formato)))
    if tipo == "aldea":
        (a0, a1), (h0, h1) = TAMANOS[tipo]
        ancho, alto = rng.randint(a0, a1), rng.randint(h0, h1)
    else:
        ancho, alto = ZONA[0] * huella, ZONA[1] * huella
    p = _Plano(rng, ancho, alto)
    espejo = rng.random() < 0.5                       # muchos formatos salen al revés que otros
    cx, cy = ancho // 2, alto // 2

    # 1. Agua, plaza y forma de la muralla de cada formato.
    figura_interior = None                            # segunda muralla, siempre entera (ciudad)
    if formato == "rio":
        # El río cruza la aldea por dentro de la muralla, a un lado de la plaza; dos calles lo cruzan.
        _rio_vertical(p, cx + (6 if not espejo else -9))
        rx, ry = 18, 12
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry
        direcciones = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    elif formato == "camino":
        _rio_vertical(p, ancho - 9 if not espejo else 6)
        rx, ry = min(24, ancho // 2 - 8), 10
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry
        direcciones = [(1, 0), (-1, 0), (0, 1)] if espejo else [(1, 0), (-1, 0), (0, -1)]
    elif formato == "lago":
        lx = cx + (14 if espejo else -14)
        _lago(p, lx, cy, 7, 6)
        cx = cx + (-2 if espejo else 2)
        rx, ry = 15, 12
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry
        direcciones = [(-1, 0), (0, 1), (0, -1)] if espejo else [(1, 0), (0, 1), (0, -1)]
    elif formato == "claro":
        lx, ly = cx + (9 if espejo else -9), cy + 7
        _lago(p, lx, ly, 3, 2)
        r = 16
        figura = lambda dx, dy: abs(dx) <= r and abs(dy) <= r - 2 and abs(dx) + abs(dy) <= 1.45 * r
        rx, ry = r, r - 2
        direcciones = [(0, 1), (-1, 0)] if espejo else [(0, -1), (1, 0)]
    elif formato == "pueblo":
        _rio_vertical(p, ancho - 10 if not espejo else 7)
        rx, ry = round(ancho * 0.3), round(alto * 0.3)
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry and abs(dx) + abs(dy) <= 1.5 * rx
        direcciones = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    elif formato == "villa":
        _rio_vertical(p, ancho - 12 if not espejo else 9)
        rx, ry = round(ancho * 0.32), round(alto * 0.32)
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry
        direcciones = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    else:  # ciudad
        _rio_vertical(p, ancho - 14 if not espejo else 11)
        rx, ry = round(ancho * 0.33), round(alto * 0.33)
        figura = lambda dx, dy: abs(dx) <= rx and abs(dy) <= ry
        ri, rj = round(rx * 0.45), round(ry * 0.45)
        figura_interior = lambda dx, dy: abs(dx) <= ri and abs(dy) <= rj
        direcciones = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    cx = max(rx + 3, min(ancho - rx - 4, cx))
    cy = max(ry + 3, min(alto - ry - 4, cy))

    def dentro_muralla(x, y, margen=1):
        return figura(x - cx, y - cy) or any(figura(x - cx + dx, y - cy + dy) for dx in (-margen, margen) for dy in (-margen, margen))

    # 2. Caminos: rectos dentro de la muralla y con curvas fuera, hasta el borde del mapa.
    for dx, dy in direcciones:
        x, y = cx, cy
        while figura(x - cx, y - cy):
            x, y = x + dx, y + dy
        _camino_recto(p, cx, cy, x, y)
        _camino_fuera(p, (x, y), (dx, dy))
    if formato == "rio":                              # segunda calle con su puente
        _camino_recto(p, cx - rx + 2, cy + 6, cx + rx - 2, cy + 6)
    if formato == "villa":                            # segunda plaza, unida a la primera
        segunda = (cx + rx // 2, cy + ry // 2)
        _camino_recto(p, cx, segunda[1], segunda[0], segunda[1])
        _camino_recto(p, segunda[0], cy, segunda[0], segunda[1])
    if formato == "ciudad":                           # calles en cuadrícula, cada 9 casillas
        for x in range(cx - rx + 4, cx + rx - 3, 9):
            _camino_recto(p, x, cy - ry + 2, x, cy + ry - 2)
        for y in range(cy - ry + 4, cy + ry - 3, 9):
            _camino_recto(p, cx - rx + 2, y, cx + rx - 2, y)
    if formato == "pueblo":                           # calles en diagonal, que dan forma irregular
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            x, y = cx, cy
            for _ in range(rx - 4):
                x, y = x + sx, y + (sy if rng.random() < 0.6 else 0)
                p.pintar(x, y, "camino", ("hierba",))

    # 3. Plaza (y la segunda de la villa), muralla y puertas.
    _plaza(p, cx, cy, 4 if tipo != "aldea" else 3)
    if formato == "villa":
        _plaza(p, *segunda, 3)
    borde = _anillo(p, cx, cy, figura)
    tramos = _tramos(p, borde)
    for t in tramos:
        p.reservado.update(t)
    muros_fijos = []
    if figura_interior:
        # Entera salvo en las cuatro calles principales, que son sus puertas.
        muros_fijos = [q for q in _anillo(p, cx, cy, figura_interior)
                       if not p.es(*q, "agua", "plaza") and abs(q[0] - cx) > 1 and abs(q[1] - cy) > 1]
        for x, y in muros_fijos:
            p.c[y][x] = "hierba"
        p.reservado.update(muros_fijos)

    # 4. Campos y cantera, fuera de la muralla (en el claro, dentro).
    en_muralla = lambda x, y: dentro_muralla(x, y)
    lado = 1 if not espejo else -1
    if formato == "claro":
        campos_rect = _rect_libre(p, 7, 10, (cx + lado * (rx // 2), cy), tipos=("hierba",))
    else:
        largo = 19 if tipo == "aldea" else 24 if tipo == "pueblo" else 30
        cerca = (cx + lado * (rx + 8), cy)
        campos_rect = (_rect_libre(p, 8, largo, cerca, fuera_de=en_muralla)
                       or _rect_libre(p, largo, 8, (cx, cy - ry - 7), fuera_de=en_muralla)
                       or _rect_libre(p, 8, 8, cerca, fuera_de=en_muralla))
    campos = []
    if campos_rect:
        (x0, y0), (x1, y1) = campos_rect
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                p.c[y][x] = "campo"
                campos.append((x, y))
        p.reservado.update((x, y) for y in range(y0 - 1, y1 + 4) for x in range(x0 - 1, x1 + 2))
    cantera_rect = _rect_libre(p, 9, 7, (cx - lado * (rx // 2), cy + ry + 8), fuera_de=en_muralla) or \
        _rect_libre(p, 9, 7, (cx - lado * (rx + 8), cy), fuera_de=en_muralla)
    cantera = []
    if cantera_rect:
        (x0, y0), (x1, y1) = cantera_rect
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                p.c[y][x] = "cantera"
                if (x + y) % 2 == 0:
                    cantera.append((x, y))
        p.reservado.update((x, y) for y in range(y0 - 1, y1 + 2) for x in range(x0 - 1, x1 + 2))

    # 5. Molino junto al agua, solares de las casas y sitios de los edificios de la evolución.
    molino = _molino(p, (cx, cy))
    dentro_estricto = lambda x, y: figura(x - cx, y - cy) and not any(
        not figura(x - cx + dx, y - cy + dy) for dx in (-2, 2) for dy in (-3, 1))
    solares = []
    for _ in range(SOLARES[tipo]):
        s = _sitio(p, 5, 3, (cx, cy), dentro_estricto, margen=0)
        if s is None:
            break
        solares.append(s)
    sitios = {}
    if tipo == "aldea":
        for nombre, (w, h) in HUELLAS.items():
            cerca = (cx, cy) if nombre != "vigia" else (cx + rx - 1, cy - ry + 1)
            s = _sitio(p, w, h, cerca, dentro_estricto) or _sitio(p, w, h, (cx, cy))
            if s:
                sitios[nombre] = s
    puertas = [q for q in borde if p.es(*q, "camino")]
    faroles = []
    for q in puertas[:: max(1, len(puertas) // 4)][:4]:
        s = _sitio(p, 1, 2, q, lambda x, y: figura(x - cx, y - cy), margen=0)
        if s:
            faroles.append(s)
    huertos = None
    if tipo == "aldea" and campos_rect:
        (x0, y0), (x1, y1) = campos_rect
        rh = _rect_libre(p, 8, 6, (x0 + 4, y1 + 6), fuera_de=None, tipos=("hierba",))
        if rh:
            huertos = rh
            p.reservado.update((x, y) for y in range(rh[0][1] - 1, rh[1][1] + 2) for x in range(rh[0][0] - 1, rh[1][0] + 2))

    # 6. Árboles en lo que queda, orillas para pescar y salidas.
    arboles = _arboles(p, bioma, lambda x, y: dentro_muralla(x, y, 1))
    orillas = _orillas(p)
    salidas = p.salidas or [(0, cy)]
    puentes = sorted(p.puentes)
    return Mapa(
        casillas=p.c, arboles=arboles, almacen=(cx, cy), molino=molino, solares=solares,
        muralla=[t[len(t) // 2] for t in tramos], tramos=tramos, campos=campos or [(cx + 1, cy + 1)],
        orillas=orillas or [(cx, cy)], cantera=cantera or [(cx - 1, cy + 1)], salidas=salidas,
        puente=puentes[0] if puentes else None, bioma=bioma, formato=formato, sitios=sitios,
        faroles=faroles, huertos=huertos, puentes=puentes, muros_fijos=muros_fijos,
    )
