"""Genera los iconos de La aldea (favicon y los de la aplicación instalable) a partir de los
gráficos del juego: una casa de tejado naranja sobre hierba, con un camino de tierra.

Uso: python web/iconos.py   (necesita Pillow; escribe en web/public/iconos)
"""

from pathlib import Path

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
CASAS = AQUI / "public" / "sprites" / "Backgrounds" / "Tilesets" / "TilesetHouse.png"
DESTINO = AQUI / "public" / "iconos"
CASA = (0, 0, 64, 48)          # la casa de tejado naranja, la misma de las aldeas en el mapa del mundo
HIERBA = (138, 203, 74, 255)
HIERBA_OSCURA = (110, 178, 58, 255)
TIERRA = (214, 170, 110, 255)
LADO = 80                      # el dibujo se hace a 80 × 80 píxeles y se amplía sin suavizar


def escena(margen: int) -> Image.Image:
    """La casa sobre la hierba. `margen`: píxeles libres alrededor de la casa (para el icono
    adaptable de Android, que recorta los bordes)."""
    im = Image.new("RGBA", (LADO, LADO), HIERBA)
    d = ImageDraw.Draw(im)
    for x in range(0, LADO, 8):              # unas matas de hierba más oscura, a cuadros
        for y in range(0, LADO, 8):
            if (x // 8 + y // 8) % 3 == 0:
                d.rectangle([x + 2, y + 3, x + 3, y + 4], fill=HIERBA_OSCURA)
    casa = Image.open(CASAS).convert("RGBA").crop((CASA[0], CASA[1], CASA[0] + CASA[2], CASA[1] + CASA[3]))
    ancho = LADO - 2 * margen
    escala = ancho / casa.width
    casa = casa.resize((round(casa.width * escala), round(casa.height * escala)), Image.NEAREST)
    x = (LADO - casa.width) // 2
    y = (LADO - casa.height) // 2 - 2
    puerta = x + round(casa.width * 24 / 64)   # la puerta está a 24 de los 64 píxeles de ancho
    d.rectangle([puerta - 5, y + casa.height - 4, puerta + 4, LADO], fill=TIERRA)   # camino hasta la puerta
    im.alpha_composite(casa, (x, y))
    return im


def redondear(im: Image.Image, radio: float) -> Image.Image:
    mascara = Image.new("L", im.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=round(im.width * radio), fill=255)
    fuera = Image.new("RGBA", im.size, (0, 0, 0, 0))
    fuera.paste(im, (0, 0), mascara)
    return fuera


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    normal = escena(margen=8)
    adaptable = escena(margen=16)            # la zona segura de Android es el 80 % central
    for lado in (512, 192):
        redondear(normal.resize((lado, lado), Image.NEAREST), 0.18).save(DESTINO / f"icono-{lado}.png")
        adaptable.resize((lado, lado), Image.NEAREST).save(DESTINO / f"icono-adaptable-{lado}.png")
    normal.resize((180, 180), Image.NEAREST).save(DESTINO / "apple-touch-icon.png")   # iOS redondea solo
    pequeno = escena(margen=2)               # en 32 y 16 píxeles, la casa ocupa casi todo
    for lado in (32, 16):
        redondear(pequeno.resize((lado * 4, lado * 4), Image.NEAREST), 0.18).resize((lado, lado), Image.LANCZOS).save(DESTINO / f"favicon-{lado}.png")
    print("Iconos escritos en", DESTINO)


if __name__ == "__main__":
    main()
