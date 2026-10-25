"""El mapa del mundo: 48 × 48 zonas, cada una con un terreno fijo que sale de la semilla, y los
nombres de los asentamientos nuevos."""

from __future__ import annotations

import math
import random

LADO = 48                                   # antes de la 3.3, 24 (se migra al cargar)
CENTRO = (24, 24)

# Nombres japoneses de sitio para los asentamientos nuevos («Aldea de Mizuno»).
NOMBRES = [
    "Mizuno", "Takada", "Kawaguchi", "Yamamura", "Ishida", "Hayashi", "Matsuda", "Hoshino", "Kitamura",
    "Minami", "Nishida", "Higashi", "Okada", "Fujita", "Sakamoto", "Morita", "Hirano", "Ueda", "Kubota",
    "Iwata", "Tanaka", "Koike", "Sugiura", "Asano", "Kuroda", "Shiraishi", "Aoyama", "Nakano", "Ogawa",
    "Hamada", "Kanai", "Tsuchiya", "Nomura", "Ishikawa", "Yoshida", "Kinoshita", "Murakami", "Arai",
    "Ikeda", "Sasaki", "Hara", "Komatsu", "Inoue", "Shimizu", "Takeda", "Kojima", "Maeda", "Sawada",
    "Kondo", "Mori", "Endo", "Kato", "Otsuka", "Hosokawa", "Uchida", "Hattori", "Miyake", "Ono",
    "Kikuchi", "Yano", "Noda", "Matsumoto", "Wada", "Sato", "Abe", "Ito", "Hashimoto", "Kimura",
]
# Para cuando ya se han usado todos los nombres: «Mizuno del Norte», «Takada Alto»…
COLETILLAS = [" del Norte", " del Sur", " del Este", " del Oeste", " Alto", " Bajo", " Nuevo", " Viejo",
              " del Río", " del Monte", " del Valle", " del Lago", " del Bosque", " del Llano"]


def _ruido(semilla: int, x: float, y: float) -> float:
    """Ruido suave entre 0 y 1: interpola valores al azar fijos de una rejilla gruesa."""
    def valor(ix: int, iy: int) -> float:
        return random.Random(semilla * 1_000_003 + ix * 7919 + iy * 104_729).random()
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = x - x0, y - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = valor(x0, y0) + (valor(x0 + 1, y0) - valor(x0, y0)) * sx
    b = valor(x0, y0 + 1) + (valor(x0 + 1, y0 + 1) - valor(x0, y0 + 1)) * sx
    return a + (b - a) * sy


def bioma(semilla: int, x: int, y: int) -> str:
    """Terreno de una zona. Cerca del centro, pradera; más lejos, de todo, en manchas grandes."""
    d = math.dist((x, y), CENTRO)
    if d < 2.5:
        return "pradera"
    frio = _ruido(semilla + 1, x / 5, y / 5)        # frío y humedad en manchas de unas 5 zonas
    humedo = _ruido(semilla + 2, x / 5, y / 5)
    lejos = min(1.0, d / 10)                         # cuanto más lejos, más terrenos extremos
    if frio > 1 - 0.3 * lejos:
        return "nieve"
    if humedo < 0.3 * lejos:
        return "desierto"
    if humedo > 1 - 0.25 * lejos:
        return "pantano"
    if humedo > 0.55:
        return "bosque"
    return "pradera"


def vecinas(x: int, y: int) -> list[tuple[int, int]]:
    return [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (dx or dy) and 0 <= x + dx < LADO and 0 <= y + dy < LADO]
