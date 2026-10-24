// Efectos que no cambian nada del mundo, solo cómo se ve: la luz de las ventanas por la noche y el
// clima (lluvia, nieve, hojas en otoño y pétalos en primavera).

import { Assets, Container, Rectangle, Sprite, Texture } from "pixi.js";
import { CASILLA as C, PARTICULAS } from "./atlas.js";

// ---- luces ----

// Mancha de luz cálida, de opaca en el centro a transparente en el borde. Se dibuja una vez.
function texturaDeLuz() {
  const lado = 64;
  const lienzo = document.createElement("canvas");
  lienzo.width = lienzo.height = lado;
  const c = lienzo.getContext("2d");
  const g = c.createRadialGradient(lado / 2, lado / 2, 0, lado / 2, lado / 2, lado / 2);
  g.addColorStop(0, "rgba(255, 214, 140, 0.9)");
  g.addColorStop(0.4, "rgba(255, 170, 80, 0.35)");
  g.addColorStop(1, "rgba(255, 150, 60, 0)");
  c.fillStyle = g;
  c.fillRect(0, 0, lado, lado);
  return Texture.from(lienzo);
}

export class Luces {
  // `fijas`: [{ x, y, radio }] en píxeles del mundo (almacén, faroles, molino).
  constructor(fijas) {
    this.contenedor = new Container();
    this.contenedor.blendMode = "add";
    this.textura = texturaDeLuz();
    this.casas = new Map();
    for (const f of fijas) this._luz(f.x, f.y, f.radio);
  }

  _luz(x, y, radio) {
    const s = new Sprite(this.textura);
    s.anchor.set(0.5);
    s.position.set(x, y);
    s.width = s.height = radio * 2;
    this.contenedor.addChild(s);
    return s;
  }

  // Una luz por casa, delante de la puerta; las casas quemadas no tienen luz.
  actualizar(casas, oscuridad) {
    for (const c of casas) {
      if (!this.casas.has(c.id)) this.casas.set(c.id, this._luz((c.x + 0.5) * C, (c.y + 0.4) * C, 22));
      this.casas.get(c.id).visible = !c.quemada;
    }
    // Las luces se encienden al atardecer, a la vez que se oscurece el mapa.
    this.contenedor.alpha = Math.min(1, oscuridad / 0.45);
    this.contenedor.visible = oscuridad > 0.02;
  }
}

// ---- clima ----

// Número fijo entre 0 y 1 para cada trozo de 6 horas del mundo: todos los que miran ven lo mismo.
const azarDelTramo = (ano, dia, hora) => {
  const n = Math.sin(ano * 374.1 + dia * 91.7 + Math.floor(hora / 6) * 17.3) * 43758.5453;
  return n - Math.floor(n);
};

// Lluvia según la estación; nieve en invierno. Hojas en otoño y pétalos en primavera si no llueve.
export function climaDe(estado) {
  // Para probar: ?clima=lluvia (o nieve, hoja, petalo, ninguno) en la dirección fuerza ese clima.
  const forzado = new URLSearchParams(location.search).get("clima");
  if (forzado) return forzado in AJUSTES ? forzado : null;
  const r = azarDelTramo(estado.ano, estado.dia, estado.hora);
  // El terreno manda: en la nieve nieva a menudo todo el año y en el desierto casi nunca llueve.
  if (estado.bioma === "nieve") return r < 0.55 ? "nieve" : null;
  if (estado.bioma === "desierto") return r < 0.03 ? "lluvia" : null;
  const lluvia = { primavera: 0.3, verano: 0.12, "otoño": 0.35 }[estado.estacion] ?? 0;
  if (estado.estacion === "invierno") return r < 0.5 ? "nieve" : null;
  if (r < lluvia) return "lluvia";
  if (estado.estacion === "otoño") return "hoja";
  if (estado.estacion === "primavera") return "petalo";
  return null;
}

const AJUSTES = {
  lluvia: { cuantas: 1 / 900, vx: -0.6, vy: 5, giro: 0, oscilar: 0, alpha: 0.6 },
  nieve: { cuantas: 1 / 1400, vx: -0.15, vy: 0.45, giro: 0, oscilar: 0.4, alpha: 0.9 },
  hoja: { cuantas: 1 / 9000, vx: 0.35, vy: 0.5, giro: 0.02, oscilar: 0.8, alpha: 1 },
  petalo: { cuantas: 1 / 9000, vx: 0.3, vy: 0.4, giro: 0.02, oscilar: 0.8, alpha: 1 },
};

export class Clima {
  constructor() {
    this.contenedor = new Container();
    this.tipo = null;
    this.particulas = [];
    this.quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  medir(ancho, alto) { this.medidas = { ancho, alto }; }

  async poner(tipo, ancho, alto) {
    if (this.quieto) tipo = null;
    this.medir(ancho, alto);
    if (tipo === this.tipo) return;
    this.tipo = tipo;
    this.contenedor.removeChildren().forEach((s) => s.destroy());
    this.particulas = [];
    if (!tipo) return;
    const { url, ancho: paso } = PARTICULAS[tipo];
    const hoja = await Assets.load(url);
    const marcos = Array.from({ length: Math.floor(hoja.width / paso) },
      (_, i) => new Texture({ source: hoja.source, frame: new Rectangle(i * paso, 0, paso, hoja.height) }));
    const a = AJUSTES[tipo];
    const cuantas = Math.min(260, Math.round(ancho * alto * a.cuantas));
    for (let i = 0; i < cuantas; i++) {
      const s = new Sprite(marcos[Math.floor(Math.random() * marcos.length)]);
      s.anchor.set(0.5);
      s.alpha = a.alpha;
      s.position.set(Math.random() * ancho, Math.random() * alto);
      s.fase = Math.random() * Math.PI * 2;
      this.contenedor.addChild(s);
      this.particulas.push(s);
    }
  }

  // Mueve las partículas en píxeles de pantalla. El tamaño sigue al zoom, como el resto del mapa.
  animar(zoom) {
    if (!this.tipo || !this.medidas || !this.particulas.length) return;
    const { ancho, alto } = this.medidas;
    const a = AJUSTES[this.tipo];
    const escala = Math.max(1, Math.round(zoom));
    for (const s of this.particulas) {
      s.scale.set(escala);
      s.fase += 0.03;
      s.x += (a.vx + Math.sin(s.fase) * a.oscilar) * escala;
      s.y += a.vy * escala;
      s.rotation += a.giro;
      if (s.y > alto + 10) { s.y = -10; s.x = Math.random() * ancho; }
      if (s.x < -10) s.x = ancho + 10;
      if (s.x > ancho + 10) s.x = -10;
    }
  }
}
