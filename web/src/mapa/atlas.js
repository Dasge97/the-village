// Dónde está cada gráfico dentro de las imágenes del paquete Ninja Adventure.
// Coordenadas en píxeles: [x, y, ancho, alto]. Las casillas miden 16 × 16.
// Suelo, agua, naturaleza y muralla son copias con otros colores que crea `copiar_sprites.py`.

export const CASILLA = 16;
const T = "/sprites/Backgrounds/Tilesets/";
const ALDEA = "/sprites/Aldea/";

export const IMAGENES = {
  suelo: ALDEA + "Suelo.png",
  agua: ALDEA + "Agua.png",
  naturaleza: ALDEA + "Naturaleza.png",
  muralla: ALDEA + "Muralla.png",
  trigo: ALDEA + "Trigo.png",
  casas: T + "TilesetHouse.png",
  elementos: T + "TilesetElement.png",
  torres: T + "TilesetTowers.png",
  molino: "/sprites/Backgrounds/Animated/WaterMill/Watermill_A_34x36.png",
  ondas: "/sprites/Backgrounds/Animated/Water Ripples/SpriteSheet16x16.png",
  sombra: "/sprites/Actor/Character/Shadow.png",
};

export const personajeUrl = (nombre) => `/sprites/Actor/Character/${nombre}/SpriteSheet.png`;
export const caraUrl = (nombre) => `/sprites/Actor/Character/${nombre}/Faceset.png`;

// Suelo de cada terreno, en Suelo. Todos los bloques de TilesetFloor tienen la misma forma: el
// conjunto de 16 piezas del camino empieza en `origen` (en casillas), la hierba lisa está 5 filas
// más abajo y las matas, a su lado. Pradera es el de siempre.
// Solo la pradera tiene matas también en la fila de encima; en los otros bloques ese hueco está vacío.
// El río usa el bloque de agua con la orilla del mismo terreno (en Agua): arena, nieve o hierba.
const SUELOS = { pradera: [0, 7], bosque: [11, 7], desierto: [0, 0], nieve: [0, 14], pantano: [11, 14] };
const AGUAS = { desierto: [0, 0], nieve: [13, 0] };
export function suelo(bioma) {
  const [cx, cy] = SUELOS[bioma] ?? SUELOS.pradera;
  const detalle = [1, 2, 3, 4].map((i) => [(cx + i) * 16, (cy + 5) * 16]);
  if (!SUELOS[bioma] || bioma === "pradera") detalle.push([(cx + 2) * 16, (cy + 4) * 16], [(cx + 3) * 16, (cy + 4) * 16]);
  return {
    conjunto: { imagen: "suelo", origen: [cx, cy] },
    agua: { imagen: "agua", origen: AGUAS[bioma] ?? [0, 6] },
    hierba: [cx * 16, (cy + 5) * 16],
    detalle,
  };
}

// Conjuntos de 16 piezas que se eligen según qué vecinos (norte, este, sur, oeste) son del
// mismo tipo. `origen` es la casilla de arriba a la izquierda del conjunto, en casillas.
// Forma del conjunto: un bloque de 3 × 3, una columna de 3 a su derecha, una fila de 3 debajo
// y una pieza suelta en la esquina.
export const CONJUNTO_AGUA = { imagen: "agua", origen: [0, 6] };

// Bits: norte 1, este 2, sur 4, oeste 8. Valor: casilla dentro del conjunto.
export const PIEZA_POR_VECINOS = {
  0: [3, 3], 1: [3, 2], 4: [3, 0], 5: [3, 1],
  2: [0, 3], 8: [2, 3], 10: [1, 3],
  6: [0, 0], 14: [1, 0], 12: [2, 0],
  7: [0, 1], 15: [1, 1], 13: [2, 1],
  3: [0, 2], 11: [1, 2], 9: [2, 2],
};

// Árboles, en Naturaleza. Cada árbol tiene una forma fija y cambia de gráfico con la estación.
export const ARBOL = {
  redondo: [[256, 0, 32, 32], [288, 0, 32, 32], [96, 128, 32, 32]],
  pino: [32, 0, 32, 32],
  grande: [48, 288, 48, 48],
  rosa: [224, 0, 32, 32],
  nieve: [192, 0, 32, 32],
  pinoNieve: [128, 0, 32, 32],
  grandeRosa: [0, 288, 48, 48],
  grandeNieve: [96, 288, 48, 48],
  grandeOtono: [144, 288, 48, 48],
  muerto: [64, 0, 32, 32],          // árbol seco, para el pantano
};
export const TOCON = [64, 128, 16, 16];
export const BROTE = [16, 160, 16, 16];
export const ROCA = [288, 144, 16, 16];
export const CULTIVO = [128, 176, 16, 16];   // planta crecida, en verano y otoño
export const SEMILLA = [208, 176, 16, 16];   // brote, en primavera
export const TRIGO = [0, 0, 16, 16];         // en Trigo: la planta crecida, dorada

// Adornos sueltos por la hierba, en Naturaleza: arbustos, flores y piedras.
export const ARBUSTOS = [[0, 160, 16, 16], [16, 160, 16, 16], [32, 160, 16, 16]];
export const FLORES = [[0, 176, 16, 16], [32, 176, 16, 16], [48, 176, 16, 16], [96, 176, 16, 16]];
export const PIEDRAS = [[240, 144, 16, 16], [288, 144, 16, 16]];
export const TRONCO_CORTADO = [192, 208, 16, 16];

// En TilesetHouse. Las casas se reparten entre cuatro modelos según su número.
export const CASAS = [[0, 0, 64, 48], [128, 0, 64, 48], [192, 0, 64, 48], [416, 0, 48, 48]];
export const ALMACEN = [400, 112, 64, 112];          // la nave alta de tejado de paja
export const EDIFICIO_MOLINO = [464, 0, 64, 64];
// Edificios de pueblos, villas y ciudades: imagen y recorte (en TilesetHouse salvo las torres).
export const EDIFICIOS = {
  mercado: ["casas", [256, 0, 48, 48]], taller: ["casas", [304, 0, 64, 48]], templo: ["casas", [368, 0, 48, 48]],
  dojo: ["casas", [400, 224, 64, 96]], posada: ["casas", [464, 0, 64, 64]], granero: ["casas", [48, 128, 48, 48]],
  torre: ["torres", [0, 32, 32, 32]],
};

// Valla baja de madera para los campos: esquinas, tramo de frente y tramo de lado.
export const VALLA = {
  arribaIzquierda: [128, 96, 16, 16], arribaDerecha: [144, 96, 16, 16],
  abajoIzquierda: [128, 112, 16, 16], abajoDerecha: [144, 112, 16, 16],
  frente: [176, 112, 16, 16], lado: [176, 96, 16, 16],
};

// Muralla de piedra, en Muralla (el muro de bloques de TilesetHouse pasado a gris).
export const MURO = {
  arribaIzquierda: [0, 0, 16, 16], arribaDerecha: [16, 0, 16, 16],
  abajoIzquierda: [0, 16, 16, 16], abajoDerecha: [16, 16, 16, 16],
  frente: [48, 16, 16, 16], lado: [48, 0, 16, 16],
};

// Puente: tablones de madera de Agua (un bloque de 3 × 3 con bordes) y la valla como barandilla.
export const TABLONES = { origen: [0, 192] };
export const TINTE_TABLONES = 0xc9a27a;

// En TilesetElement: objetos de la plaza y de los campos.
export const PUESTO = [112, 16, 16, 32];
export const BARRILES = [[64, 0, 16, 16], [80, 0, 16, 16], [16, 0, 16, 16]];
export const CAJA = [0, 0, 16, 16];
export const CARRO = [0, 48, 32, 32];
export const PAJA = [192, 64, 16, 32];
export const FAROL = [96, 48, 16, 32];

// Molino de agua: 3 fotogramas de 34 × 36.
export const MOLINO = { ancho: 34, alto: 36, fotogramas: 3 };
// Ondas en el agua: 4 fotogramas de 16 × 16.
export const ONDAS = { fotogramas: 4 };

// Iconos sobre la cabeza (imágenes sueltas del paquete) y partículas del clima.
const IT = "/sprites/Items/";
export const ICONOS = {
  azada: IT + "Tool/Hoe.png", hacha: IT + "Tool/Axe.png", pico: IT + "Tool/Pickaxe.png", martillo: IT + "Tool/Hammer.png",
  cana: IT + "Weapons/Fishing Rod/Sprite.png", katana: IT + "Weapons/Katana/Sprite.png",
  comida: IT + "Food/Onigiri.png", corazon: IT + "Potion/Heart.png", bolsa: IT + "Object/Bag.png",
  enfado: "/sprites/Ui/Emote/emote10.png", alegria: "/sprites/Ui/Emote/emote11.png",
  verguenza: "/sprites/Ui/Emote/emote12.png", neutro: "/sprites/Ui/Emote/emote14.png",
};
// Partículas: imagen y ancho de cada fotograma (todas son una tira horizontal).
export const PARTICULAS = {
  lluvia: { url: "/sprites/FX/Particle/Rain.png", ancho: 8 },
  nieve: { url: "/sprites/FX/Particle/Snow.png", ancho: 8 },
  hoja: { url: "/sprites/FX/Particle/Leaf.png", ancho: 12 },
  petalo: { url: "/sprites/FX/Particle/LeafPink.png", ancho: 12 },
};

// Hojas de personaje: una columna por dirección (abajo, arriba, izquierda, derecha) y una fila
// por fotograma de la animación de andar. Algunas hojas solo tienen 2 filas.
export const DIRECCIONES = { abajo: 0, arriba: 1, izquierda: 2, derecha: 3 };
