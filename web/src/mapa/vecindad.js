// El resto del mundo alrededor del asentamiento que se está mirando: el mapa continuo.
//
// El mundo es un solo mapa de 48 × 48 zonas de 96 × 72 casillas. Al mover la cámara se piden al
// servidor las zonas que se ven (y una más alrededor) y se sueltan las que quedan lejos:
// - una zona vacía (o el bosque alrededor de una aldea) se pinta una vez en una imagen: hierba,
//   bosque, agua y los caminos que unen los asentamientos;
// - un asentamiento vecino se dibuja con una escena «embebida», con su gente moviéndose; su estado
//   se pide cada pocos segundos (no llega por el websocket, que es solo del principal).
// Todo se coloca en píxeles de la escena principal: la casilla (x, y) del mundo está en
// ((x − origen.x) × 16, (y − origen.y) × 16), siendo `origen` donde empieza el mapa principal.

import { Container, Sprite } from "pixi.js";
import * as A from "./atlas.js";
import { CASILLA as C } from "./atlas.js";

// Para que la cámara siga donde estaba al entrar en un vecino (lo lee la escena nueva al empezar).
export const camaraPendiente = { valor: null };

const MARGEN = 1;               // zonas de más alrededor de lo que se ve
const SOLTAR = 3;               // a cuántas zonas de lo que se ve se sueltan
const CADA_VISTAZO = 3000;      // ms entre estados de los vecinos
const RESOLUCION = 0.5;         // de las imágenes del terreno de relleno (en el zoom más cercano se ve algo blando)

const azar = (x, y) => {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
};

export class Vecindad {
  constructor(escena) {
    this.escena = escena;
    this.mapa = escena.mapa;
    [this.zx, this.zy] = this.mapa.zona_casillas ?? [96, 72];
    this.zonas = new Map();       // "x,y" → { sprite } o { cargando }
    this.vecinos = new Map();     // id → { escena, contenedor, luces, rect, estado }
    this.rellenos = new Container();
    this.capaVecinos = new Container();
    escena.fondo.addChild(this.rellenos, this.capaVecinos);
    this.activa = !!this.mapa.origen;
    this.reloj = setInterval(() => this._vistazo(), CADA_VISTAZO);
  }

  destruir() {
    this.destruida = true;
    clearInterval(this.reloj);
    for (const v of this.vecinos.values()) v.escena.destruir();
    this.vecinos.clear();
  }

  // ---- qué se ve ----

  // Las zonas del mundo que caen en pantalla (con margen), en coordenadas de zona.
  _zonasVisibles() {
    const e = this.escena;
    const [ox, oy] = this.mapa.origen;
    const z = e.camara.zoom;
    const mitadW = e.elemento.clientWidth / 2 / z;
    const mitadH = e.elemento.clientHeight / 2 / z;
    const wx0 = (e.camara.x - mitadW) / C + ox;
    const wx1 = (e.camara.x + mitadW) / C + ox;
    const wy0 = (e.camara.y - mitadH) / C + oy;
    const wy1 = (e.camara.y + mitadH) / C + oy;
    return {
      x0: Math.floor(wx0 / this.zx) - MARGEN, x1: Math.floor(wx1 / this.zx) + MARGEN,
      y0: Math.floor(wy0 / this.zy) - MARGEN, y1: Math.floor(wy1 / this.zy) + MARGEN,
    };
  }

  alMover() {
    if (!this.activa || this.destruida || this.pendiente) return;
    this.pendiente = true;
    // Como mucho cinco veces por segundo: al arrastrar llegan muchos movimientos seguidos.
    setTimeout(() => { this.pendiente = false; this._cargar(); }, 200);
  }

  _cargar() {
    if (this.destruida) return;
    const v = this._zonasVisibles();
    this.vista = v;
    for (let y = v.y0; y <= v.y1; y++) {
      for (let x = v.x0; x <= v.x1; x++) {
        const clave = `${x},${y}`;
        if (!this.zonas.has(clave)) this._pedirZona(x, y, clave);
      }
    }
    // Lo que queda lejos se suelta.
    for (const [clave, zona] of this.zonas) {
      const [x, y] = clave.split(",").map(Number);
      if (x < v.x0 - SOLTAR || x > v.x1 + SOLTAR || y < v.y0 - SOLTAR || y > v.y1 + SOLTAR) {
        zona.sprite?.destroy({ texture: true, textureSource: true });
        this.zonas.delete(clave);
      }
    }
    for (const [id, vec] of this.vecinos) {
      const [zx, zy, h] = vec.zona;
      if (zx + h - 1 < v.x0 - SOLTAR || zx > v.x1 + SOLTAR || zy + h - 1 < v.y0 - SOLTAR || zy > v.y1 + SOLTAR) {
        vec.escena.destruir();
        vec.contenedor.destroy({ children: true });
        vec.luces.destroy({ children: true });
        this.vecinos.delete(id);
      }
    }
  }

  async _pedirZona(x, y, clave) {
    this.zonas.set(clave, { cargando: true });
    try {
      const r = await fetch(`/api/zona?x=${x}&y=${y}`);
      const z = await r.json();
      if (this.destruida || !this.zonas.has(clave)) return;
      if (z.fuera) { this.zonas.set(clave, {}); return; }
      const zona = {};
      if (z.relleno) zona.sprite = this._pintarRelleno(z.relleno);
      this.zonas.set(clave, zona);
      if (z.asentamiento != null && z.asentamiento !== this.mapa.id && !this.vecinos.has(z.asentamiento)) {
        this._cargarVecino(z.asentamiento);
      }
    } catch {
      this.zonas.delete(clave);        // se vuelve a intentar en el próximo movimiento
    }
  }

  // ---- relleno: el terreno de las zonas vacías, en una imagen ----

  _pintarRelleno(r) {
    const e = this.escena;
    const suelo = A.suelo(r.bioma);
    const cont = new Container();
    const tipo = (x, y) => r.casillas[y]?.[x] ?? null;
    const mascara = (x, y, es) => {
      const igual = (nx, ny) => { const t = tipo(nx, ny); return t === null || es(t); };
      return (igual(x, y - 1) ? 1 : 0) | (igual(x + 1, y) ? 2 : 0) | (igual(x, y + 1) ? 4 : 0) | (igual(x - 1, y) ? 8 : 0);
    };
    const poner = (textura, x, y) => { const s = new Sprite(textura); s.position.set(x * C, y * C); cont.addChild(s); return s; };
    for (let y = 0; y < r.alto; y++) {
      for (let x = 0; x < r.ancho; x++) {
        const t = r.casillas[y][x];
        const a = azar(x + r.origen[0], y + r.origen[1]);
        const hierba = a < 0.18 ? suelo.detalle[Math.floor(a * 50) % suelo.detalle.length] : suelo.hierba;
        poner(e._recorte("suelo", [...hierba, C, C]), x, y);
        if (t === "m") poner(e._pieza(suelo.conjunto, mascara(x, y, (o) => o === "m")), x, y);
        if (t === "a") poner(e._pieza(suelo.agua, mascara(x, y, (o) => o === "a")), x, y);
      }
    }
    // Los árboles, ordenados de arriba abajo para que los de delante tapen a los de detrás.
    const nevado = r.bioma === "nieve";
    for (const [x, y] of r.arboles) {
      const a = azar(x + r.origen[0] + 11, y + r.origen[1] + 7);
      const pieza = r.bioma === "pantano" && a < 0.5 ? A.ARBOL.muerto
        : a < (r.bioma === "bosque" ? 0.45 : 0.15) ? (nevado ? A.ARBOL.pinoNieve : A.ARBOL.pino)
        : nevado ? A.ARBOL.nieve : A.ARBOL.redondo[Math.floor(a * 30) % 3];
      const s = new Sprite(e._recorte("naturaleza", pieza));
      s.anchor.set(0.5, 1);
      s.position.set((x + 0.5) * C, (y + 1) * C);
      cont.addChild(s);
    }
    // La imagen empieza donde empiezan los dibujos: los árboles de la primera fila sobresalen hacia arriba.
    const limites = cont.getLocalBounds();
    const textura = e.app.renderer.generateTexture({ target: cont, resolution: RESOLUCION });
    cont.destroy({ children: true });
    const sprite = new Sprite(textura);
    const [ox, oy] = this.mapa.origen;
    sprite.position.set((r.origen[0] - ox) * C + limites.x, (r.origen[1] - oy) * C + limites.y);
    sprite.scale.set(1 / RESOLUCION);
    this.rellenos.addChild(sprite);
    return sprite;
  }

  // ---- vecinos: otros asentamientos, con su gente ----

  async _cargarVecino(id) {
    this.vecinos.set(id, { cargando: true, escena: { destruir() {} }, contenedor: new Container(), luces: new Container(), zona: [0, 0, 1] });
    try {
      const mapa = await (await fetch(`/api/mapa?aldea=${id}`)).json();
      if (this.destruida || !this.vecinos.has(id)) return;
      const [ox, oy] = this.mapa.origen;
      const contenedor = new Container();
      contenedor.position.set((mapa.origen[0] - ox) * C, (mapa.origen[1] - oy) * C);
      const luces = new Container();
      luces.position.copyFrom(contenedor.position);
      this.capaVecinos.addChild(contenedor);
      this.escena.lucesVecinos.addChild(luces);
      const { Escena } = await import("./escena.js");
      const escena = new Escena(null, { app: this.escena.app, contenedor, capaLuces: luces });
      const zx = Math.floor(mapa.origen[0] / this.zx);
      const zy = Math.floor(mapa.origen[1] / this.zy);
      const huella = Math.max(1, Math.round(mapa.ancho / this.zx));
      this.vecinos.set(id, { escena, contenedor, luces, zona: [zx, zy, huella], estado: null,
        rect: [contenedor.x, contenedor.y, contenedor.x + mapa.ancho * C, contenedor.y + mapa.alto * C] });
      await escena.iniciar(mapa);
      this._vistazo([id]);
    } catch {
      this.vecinos.delete(id);
    }
  }

  async _vistazo(solo) {
    if (this.destruida || document.hidden) return;
    const ids = solo ?? [...this.vecinos.keys()].filter((i) => this.vecinos.get(i).escena.listo);
    if (!ids.length) return;
    try {
      const estados = await (await fetch(`/api/vistazo?ids=${ids.join(",")}`)).json();
      for (const [id, estado] of Object.entries(estados)) {
        const v = this.vecinos.get(Number(id));
        if (!v?.escena.listo || v.escena.destruido) continue;
        // Llega cada pocos segundos: la gente anda de un sitio a otro en ese tiempo.
        await v.escena.actualizar({ ...estado, segundos_por_turno: CADA_VISTAZO / 1000 });
      }
    } catch {
      // Sin estado nuevo: los vecinos se quedan como estaban hasta el siguiente.
    }
  }

  // ¿Hay otro asentamiento en este punto (en píxeles de la escena principal)? Su número o null.
  asentamientoEn(x, y) {
    for (const [id, v] of this.vecinos) {
      if (!v.rect) continue;
      const [x0, y0, x1, y1] = v.rect;
      if (x >= x0 && x < x1 && y >= y0 && y < y1) return id;
    }
    return null;
  }
}
