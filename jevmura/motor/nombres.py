"""Nombres y aspecto de los habitantes.

El aspecto es el nombre de la carpeta del personaje en `Actor/Character` del paquete de gráficos.
Es el aspecto de adulto. Los niños, los ancianos y los guardias se dibujan con otros personajes,
y eso lo decide la web según la edad y el oficio.
"""

from __future__ import annotations

import random

NOMBRES = {
    "h": ["Haruto", "Sota", "Yuto", "Riku", "Kaito", "Ren", "Daiki", "Takumi", "Kenji", "Hiroshi",
          "Shin", "Taro", "Jiro", "Isamu", "Kenta", "Masaru", "Noboru", "Ryo", "Satoshi", "Tadashi",
          "Akio", "Goro", "Hideo", "Ichiro", "Kazuo", "Makoto", "Osamu", "Saburo", "Tomio", "Yasuo"],
    "m": ["Hana", "Yui", "Aoi", "Sakura", "Mei", "Rin", "Akari", "Emi", "Kaori", "Nanami",
          "Ayame", "Chiyo", "Fumiko", "Haruka", "Izumi", "Kiku", "Midori", "Natsu", "Sayuri", "Tomoe",
          "Ume", "Yoko", "Asami", "Eri", "Hoshi", "Kana", "Mai", "Noriko", "Suzu", "Yuna"],
}

ASPECTOS = {
    "h": ["Villager", "Villager2", "Villager3", "ManGreen", "Hunter", "Monk"],
    "m": ["Woman", "Villager4", "Villager5", "Villager6", "Princess"],
}


def elegir_nombre(rng: random.Random, sexo: str, usados: set[str]) -> str:
    libres = [n for n in NOMBRES[sexo] if n not in usados]
    if libres:
        return rng.choice(libres)
    base = rng.choice(NOMBRES[sexo])
    n = 2
    while f"{base} {n}" in usados:
        n += 1
    return f"{base} {n}"


def elegir_aspecto(rng: random.Random, sexo: str) -> str:
    return rng.choice(ASPECTOS[sexo])
