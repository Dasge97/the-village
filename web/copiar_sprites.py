"""Copia del paquete Ninja Adventure (CC0) solo los gráficos que usa la web, a `web/public/sprites`.

Además crea en `sprites/Aldea` versiones con otros colores: hierba más viva, tierra arenosa,
árboles de un verde más oscuro que la hierba y una muralla de piedra gris.

Uso: python web/copiar_sprites.py ["ruta al paquete"]   (necesita Pillow)
"""

import shutil
import sys
from pathlib import Path

from PIL import Image

PAQUETE = Path(sys.argv[1] if len(sys.argv) > 1 else
               Path(__file__).resolve().parents[2] / "Ninja Adventure - Asset Pack" / "Ninja Adventure - Asset Pack")
DESTINO = Path(__file__).resolve().parent / "public" / "sprites"

PERSONAJES = ["Villager", "Villager2", "Villager3", "ManGreen", "Hunter", "Monk",
              "Woman", "Villager4", "Villager5", "Villager6", "Princess",
              "Child", "OldMan", "OldMan2", "OldWoman", "Samurai", "SamuraiBlue", "NinjaRed"]

FICHEROS = [
    "Backgrounds/Tilesets/TilesetHouse.png",
    "Backgrounds/Tilesets/TilesetElement.png",
    "Backgrounds/Tilesets/TilesetTowers.png",
    "Backgrounds/Animated/WaterMill/Watermill_A_34x36.png",
    "Backgrounds/Animated/Water Ripples/SpriteSheet16x16.png",
    "Actor/Character/Shadow.png",
    "Items/Food/Onigiri.png",
    "Items/Resource/Branch.png",
    "Items/Resource/Rock.png",
    # Iconos sobre la cabeza de cada habitante, según lo que hace.
    "Items/Tool/Hoe.png", "Items/Tool/Axe.png", "Items/Tool/Pickaxe.png", "Items/Tool/Hammer.png",
    "Items/Weapons/Fishing Rod/Sprite.png", "Items/Weapons/Katana/Sprite.png",
    "Items/Potion/Heart.png", "Items/Object/Bag.png",
    "Ui/Emote/emote10.png", "Ui/Emote/emote11.png", "Ui/Emote/emote12.png", "Ui/Emote/emote14.png",
    # Lluvia, nieve y hojas que caen.
    "FX/Particle/Rain.png", "FX/Particle/Snow.png", "FX/Particle/Leaf.png", "FX/Particle/LeafPink.png",
    # Ataques de monstruos: los monstruos, el tajo de los guardias y el humo al huir.
    "FX/Attack/Cut/SpriteSheet.png", "FX/Smoke/Smoke/SpriteSheet.png",
    # Sonido: música de día y de noche, ambiente y avisos. Empieza apagado en la web.
    "Audio/Musics/33 - Calm Village.ogg", "Audio/Musics/22 - Dream.ogg",
    "Audio/Sounds/Ambient/River.wav", "Audio/Sounds/Ambient/Rain.wav", "Audio/Sounds/Ambient/Wind.wav",
    "Audio/Sounds/Creature/Bird.wav", "Audio/Sounds/Alert/Alert2.wav", "Audio/Sounds/Whoosh & Slash/Slash.wav",
    "Audio/Jingles/Success1.wav",
    "LICENSE.txt",
]
MONSTRUOS = ["Slime", "Snake", "BlueBat", "SpiderRed", "Lizard", "Mole"]
FICHEROS += [f"Actor/Monster/{x}/SpriteSheet.png" for x in MONSTRUOS] + [f"Actor/Character/{p}/{f}" for p in PERSONAJES for f in ("SpriteSheet.png", "Faceset.png")]

# En el paquete, la cara de ManGreen se llama Faceset1.png.
ORIGEN = {"Actor/Character/ManGreen/Faceset.png": "Actor/Character/ManGreen/Faceset1.png"}
# Algunos monstruos tienen la hoja con su propio nombre; en la web todas se llaman SpriteSheet.png.
ORIGEN |= {f"Actor/Monster/{x}/SpriteSheet.png": f"Actor/Monster/{x}/{x}.png" for x in ("Slime", "Snake", "Lizard", "Mole")}

# Colores del paquete y por cuál se cambian.
HIERBA = {"adbc3a": "8acb4a", "a8a129": "73b544", "74a334": "5a9e3c", "56864c": "468a38"}
TIERRA = {"d3865f": "dcb472", "bd7959": "c79a58", "ad704b": "a87c44", "e6a578": "ecd294"}
ARBOLES = {"adbc3a": "5fae3e", "74a334": "3f8a36", "4a7f4b": "2f6b33", "7a7a3e": "4d6a2e",
           "546626": "355a28"}
DORADO = {"adbc3a": "f2cf5b", "74a334": "d9a33a", "4a7f4b": "a8742e", "7a7a3e": "9a6a2c"}

# El trigo: la planta crecida de TilesetNature con los verdes cambiados por dorados.
TRIGO = (128, 176, 16, 16)

# Gráficos con otros colores: origen en el paquete, destino y cambios de color.
RECOLOREADOS = [
    ("Backgrounds/Tilesets/TilesetFloor.png", "Aldea/Suelo.png", HIERBA | TIERRA),
    ("Backgrounds/Tilesets/TilesetWater.png", "Aldea/Agua.png", HIERBA),
    ("Backgrounds/Tilesets/TilesetNature.png", "Aldea/Naturaleza.png", ARBOLES),
]

# La muralla: el muro de bloques claros de TilesetHouse (7 × 2 casillas), pasado a gris.
MURALLA = (128, 128, 112, 32)


def _rgb(hexa: str) -> tuple[int, int, int]:
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def recolorear(imagen: Image.Image, cambios: dict[str, str]) -> Image.Image:
    tabla = {_rgb(a): _rgb(b) for a, b in cambios.items()}
    salida = imagen.convert("RGBA")
    px = salida.load()
    for y in range(salida.height):
        for x in range(salida.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in tabla:
                px[x, y] = (*tabla[(r, g, b)], a)
    return salida


def a_piedra(imagen: Image.Image) -> Image.Image:
    """Gris un poco azulado que conserva la luz de cada píxel."""
    salida = imagen.convert("RGBA")
    px = salida.load()
    for y in range(salida.height):
        for x in range(salida.width):
            r, g, b, a = px[x, y]
            luz = 0.3 * r + 0.59 * g + 0.11 * b
            px[x, y] = (round(luz * 0.86), round(luz * 0.88), round(luz * 0.94), a)
    return salida


def guardar(imagen: Image.Image, ruta: str) -> None:
    destino = DESTINO / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(destino)


for f in FICHEROS:
    destino = DESTINO / f
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PAQUETE / ORIGEN.get(f, f), destino)

for origen, destino, cambios in RECOLOREADOS:
    guardar(recolorear(Image.open(PAQUETE / origen), cambios), destino)

x, y, w, h = MURALLA
casas = Image.open(PAQUETE / "Backgrounds/Tilesets/TilesetHouse.png")
guardar(a_piedra(casas.crop((x, y, x + w, y + h))), "Aldea/Muralla.png")
x, y, w, h = TRIGO
naturaleza = Image.open(PAQUETE / "Backgrounds/Tilesets/TilesetNature.png")
guardar(recolorear(naturaleza.crop((x, y, x + w, y + h)), DORADO), "Aldea/Trigo.png")

print(f"{len(FICHEROS) + len(RECOLOREADOS) + 2} ficheros copiados o creados en {DESTINO}")
