// Dibuja la aldea con PixiJS: suelo con adornos, árboles, casas, muralla, campos vallados, puente,
// molino y habitantes.
// El servidor manda un estado cada turno (10 segundos). Entre dos estados, cada habitante anda
// desde donde estaba hasta su nueva posición, para que el movimiento se vea continuo.

import {
  AnimatedSprite, Application, Assets, Container, Graphics, Rectangle, Sprite, Text, Texture, TextureStyle,
} from "pixi.js";
import * as A from "./atlas.js";
import { Clima, Luces, climaDe } from "./efectos.js";
import { iconoDeAccion } from "./iconos.js";
import { Ataques } from "./monstruos.js";
import { Multitud } from "./multitud.js";
import { Vecindad, camaraPendiente } from "./vecindad.js";

TextureStyle.defaultOptions.scaleMode = "nearest";

const C = A.CASILLA;
const TIERRA = new Set(["m", "p", "c", "k"]);   // camino, plaza, campo y cantera usan la misma tierra

// Número pseudoaleatorio fijo por casilla, para que los detalles no cambien al recargar.
const azar = (x, y) => {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
};

const elegir = (lista, r) => lista[Math.floor(r * lista.length) % lista.length];

// Objetos fijos alrededor de la plaza, en casillas desde su centro. Evitan los caminos.
const PLAZA = [
  ["elementos", A.PUESTO, -3, 2], ["elementos", A.PUESTO, -4, -1], ["elementos", A.BARRILES[2], -3, -1],
  ["elementos", A.BARRILES[0], 3, -2], ["elementos", A.BARRILES[1], 4, -2], ["elementos", A.CAJA, 4, -1],
  ["elementos", A.FAROL, 3, 3], ["elementos", A.FAROL, -3, -3],
];

// Oscuridad de la noche según la hora: de 0 (día) a 0,55 (noche cerrada).
function oscuridad(hora) {
  if (hora >= 22 || hora < 5) return 0.55;
  if (hora < 7) return 0.55 * (1 - (hora - 5) / 2);
  if (hora >= 19) return 0.55 * ((hora - 19) / 3);
  return 0;
}

// La escena dibuja un asentamiento. La principal tiene su propia aplicación de PixiJS, la cámara y
// el minimapa, y alrededor carga el resto del mundo (ver vecindad.js). Los vecinos que se ven son
// escenas «embebidas»: comparten la aplicación de la principal y dibujan dentro de un contenedor
// suyo, sin cámara, sin minimapa, sin clima y sin noche propia (los cubre la de la principal).
export class Escena {
  constructor(elemento, { alSeleccionar, alDejarDeSeguir, alEntrar, app, contenedor, capaLuces } = {}) {
    this.elemento = elemento;
    this.alSeleccionar = alSeleccionar || (() => {});
    this.alDejarDeSeguir = alDejarDeSeguir || (() => {});
    this.alEntrar = alEntrar || (() => {});
    this.embebida = !!app;
    this.appCompartida = app;
    this.contenedor = contenedor;
    this.capaLuces = capaLuces;
    this.texturas = new Map();
    this.habitantes = new Map();
    this.casas = new Map();
    this.estacion = null;
  }

  async iniciar(mapa) {
    this.mapa = mapa;
    this.bioma = mapa.bioma ?? "pradera";
    this.suelo = A.suelo(this.bioma);
    if (this.embebida) {
      this.app = this.appCompartida;
    } else {
      this.app = new Application();
      await this.app.init({ resizeTo: this.elemento, backgroundAlpha: 0, antialias: false, roundPixels: true });
    }
    this.listo = true;
    if (this.destruido) { this._cerrar(); return; }
    if (!this.embebida) this.elemento.appendChild(this.app.canvas);

    await Assets.load([...Object.values(A.IMAGENES), ...Object.values(A.ICONOS)]);
    if (this.destruido) { this._cerrar(); return; }
    this.imagenes = Object.fromEntries(Object.entries(A.IMAGENES).map(([k, url]) => [k, Assets.get(url)]));

    this.mundo = new Container();
    (this.embebida ? this.contenedor : this.app.stage).addChild(this.mundo);
    // Debajo de todo, el resto del mundo: el terreno de las zonas de alrededor y los vecinos.
    if (!this.embebida) {
      this.fondo = new Container();
      this.mundo.addChild(this.fondo);
    }
    this._marcarOcupadas();
    this._dibujarSuelo();
    this.ondas = new Container();
    this.mundo.addChild(this.ondas);
    this._dibujarAgua();
    this.cultivos = new Container();
    this.rocas = new Container();
    this.objetos = new Container();
    this.objetos.sortableChildren = true;
    // La noche cubre todo el mundo que se ve, también a los vecinos (las embebidas no tienen).
    this.noche = new Graphics().rect(-1e6, -1e6, 2e6, 2e6).fill(0x0b1235);
    this.noche.alpha = 0;
    this.noche.visible = !this.embebida;
    this.lucesVecinos = new Container();
    // Por encima de la noche: la luz de las ventanas y los iconos de lo que hace cada uno.
    this.luces = new Luces(this._lucesFijas());
    this.iconos = new Container();
    // Los ataques son de noche: los monstruos van por encima de la oscuridad para que se vean.
    const capaAtaque = new Container();
    capaAtaque.sortableChildren = true;
    this.ataques = new Ataques(mapa, capaAtaque);
    this.mundo.addChild(this.cultivos, this.rocas, this.objetos, this.noche, this.lucesVecinos,
      this.embebida ? new Container() : this.luces.contenedor, capaAtaque, this.ataques.efectos, this.iconos);
    // Las luces de una embebida van por encima de la noche de la principal.
    if (this.embebida) this.capaLuces.addChild(this.luces.contenedor);
    this._dibujarFijos();
    this.multitud = new Multitud(this);
    this.clima = new Clima();
    if (!this.embebida) this.app.stage.addChild(this.clima.contenedor);

    this.etiqueta = new Text({ text: "", style: { fontFamily: "Inter, sans-serif", fontSize: 24, fill: 0xffffff,
      stroke: { color: 0x1a1208, width: 5 }, fontWeight: "600" } });
    this.etiqueta.scale.set(0.25);
    this.etiqueta.anchor.set(0.5, 1);
    this.etiqueta.visible = false;
    this.etiqueta.zIndex = 1e6;
    this.objetos.addChild(this.etiqueta);

    // Marca bajo el habitante elegido: un anillo del color de acento de la web.
    this.anillo = new Graphics().ellipse(0, 0, 8, 4).stroke({ color: 0x4fb3e8, width: 1.5 });
    this.anillo.visible = false;
    this.objetos.addChild(this.anillo);
    this.marcado = null;
    this.siguiendo = false;

    this._tic = () => this._animar();
    this.app.ticker.add(this._tic);
    if (this.embebida) return;
    this._prepararCamara();
    this._crearMinimapa();
    this.vecindad = new Vecindad(this);
    this._observador = new ResizeObserver(() => this._encajar());
    this._observador.observe(this.elemento);
    this._encajar();
  }

  // ---- cámara: zoom y arrastre ----

  // Al entrar se ve la aldea a doble tamaño, centrada en la plaza. Se puede arrastrar con el
  // ratón o el dedo, acercar y alejar con la rueda, pellizcando o con los botones.
  _prepararCamara() {
    const [ax, ay] = this.mapa.almacen;
    this.camara = { x: (ax + 0.5) * C, y: (ay + 0.5) * C, zoom: null };
    // Si se llega pulsando un vecino en el mapa continuo, la cámara se queda donde estaba.
    const p = camaraPendiente.valor;
    if (p && this.mapa.origen) {
      this.camara = { x: p.x - this.mapa.origen[0] * C, y: p.y - this.mapa.origen[1] * C, zoom: p.zoom };
      camaraPendiente.valor = null;
    }
    const lienzo = this.app.canvas;
    lienzo.style.touchAction = "none";
    const punteros = new Map();
    let pellizco = null;
    this.arrastrado = false;

    // Pulsar sobre un habitante lo elige; pulsar en un sitio sin nadie (sin arrastrar y fuera del
    // minimapa) quita la selección. Quién hay bajo el ratón lo calcula `_habitanteEn` con la cámara:
    // la búsqueda de PixiJS no sirve aquí porque los habitantes se mueven en cada fotograma y su
    // posición para esa búsqueda se queda atrasada (devolvía a otro habitante o a nadie).
    this.app.stage.eventMode = "static";
    this.app.stage.hitArea = this.app.screen;
    this.app.stage.on("pointertap", (e) => {
      if (this.arrastrado || this.enMinimapa) return;
      const id = this._habitanteEn(e.client.x, e.client.y);
      // Sin nadie debajo, pulsar en otro asentamiento del mapa continuo lleva a él.
      const otro = id === null ? this.vecindad?.asentamientoEn(...this._aMundo(e.client.x, e.client.y)) : null;
      if (otro != null) {
        camaraPendiente.valor = { x: this.camara.x + this.mapa.origen[0] * C, y: this.camara.y + this.mapa.origen[1] * C,
          zoom: this.camara.zoom };
        this.alEntrar(otro);
        return;
      }
      this.alSeleccionar(id);
    });
    // Al pasar el ratón por encima de alguien se ve su nombre y el cursor cambia.
    lienzo.addEventListener("pointermove", (e) => {
      if (e.buttons) return;
      const id = this._habitanteEn(e.clientX, e.clientY);
      this.sobre = id;
      this.etiqueta.visible = id !== null;
      lienzo.style.cursor = id !== null ? "pointer" : "";
    });
    lienzo.addEventListener("pointerleave", () => { this.sobre = null; lienzo.style.cursor = ""; });

    lienzo.addEventListener("pointerdown", (e) => {
      this.enMinimapa = this._pulsarMinimapa(e);
      if (this.enMinimapa) return;
      punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
      this.arrastrado = false;
      lienzo.setPointerCapture(e.pointerId);
    });
    lienzo.addEventListener("pointermove", (e) => {
      const antes = punteros.get(e.pointerId);
      if (!antes) return;
      punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (punteros.size === 2) {
        const [a, b] = [...punteros.values()];
        const distancia = Math.hypot(a.x - b.x, a.y - b.y);
        if (pellizco) this._zoomEn(this.camara.zoom * (distancia / pellizco), (a.x + b.x) / 2, (a.y + b.y) / 2);
        pellizco = distancia;
        this.arrastrado = true;
        return;
      }
      const dx = e.clientX - antes.x;
      const dy = e.clientY - antes.y;
      if (Math.abs(dx) + Math.abs(dy) > 0) {
        if (this.siguiendo) { this.siguiendo = false; this.alDejarDeSeguir(); }
        this.camara.x -= dx / this.camara.zoom;
        this.camara.y -= dy / this.camara.zoom;
        this.arrastrado ||= Math.abs(dx) + Math.abs(dy) > 3;
        this._aplicarCamara();
      }
    });
    const soltar = (e) => { punteros.delete(e.pointerId); if (punteros.size < 2) pellizco = null; };
    lienzo.addEventListener("pointerup", soltar);
    lienzo.addEventListener("pointercancel", soltar);
    lienzo.addEventListener("wheel", (e) => {
      e.preventDefault();
      this._zoomEn(this.camara.zoom * (e.deltaY < 0 ? 1.25 : 0.8), e.clientX, e.clientY);
    }, { passive: false });
  }

  // El mapa siempre llena la caja, aunque al alejarlo del todo se recorte un poco por un lado.
  // Se puede alejar hasta ver varias zonas del mundo (no más: habría que cargar demasiadas).
  _zoomMinimo() {
    if (!this.mapa.mundo) {
      return Math.max(this.elemento.clientWidth / (this.mapa.ancho * C), this.elemento.clientHeight / (this.mapa.alto * C));
    }
    return 0.15;
  }

  // Zoom para ver entero el asentamiento principal.
  _zoomTodo() {
    return Math.min(this.elemento.clientWidth / (this.mapa.ancho * C), this.elemento.clientHeight / (this.mapa.alto * C));
  }

  // Un punto de la pantalla en píxeles del mundo de esta escena (los de su mapa).
  _aMundo(clienteX, clienteY) {
    const caja = this.app.canvas.getBoundingClientRect();
    const z = this.camara.zoom;
    return [(clienteX - caja.left - this.mundo.x) / z, (clienteY - caja.top - this.mundo.y) / z];
  }

  // Cambia el zoom manteniendo quieto el punto de la pantalla que está bajo el cursor.
  _zoomEn(zoom, clienteX, clienteY) {
    const caja = this.app.canvas.getBoundingClientRect();
    const px = clienteX - caja.left;
    const py = clienteY - caja.top;
    const antes = this.camara.zoom;
    const nuevo = Math.max(this._zoomMinimo(), Math.min(5, zoom));
    const w = this.elemento.clientWidth;
    const h = this.elemento.clientHeight;
    this.camara.x += (px - w / 2) * (1 / antes - 1 / nuevo);
    this.camara.y += (py - h / 2) * (1 / antes - 1 / nuevo);
    this.camara.zoom = nuevo;
    this._aplicarCamara();
  }

  // Marca a un habitante (o a nadie con null). Si `seguir` es verdadero, la cámara lo acompaña.
  marcar(id, seguir = false) {
    this.marcado = id;
    this.siguiendo = !!(id && seguir);
    if (this.siguiendo && this.camara.zoom < 2) this.camara.zoom = Math.max(2, this._zoomMinimo());
  }

  acercar() { this._zoomEn(this.camara.zoom * 1.5, ...this._centroPantalla()); }
  alejar() { this._zoomEn(this.camara.zoom / 1.5, ...this._centroPantalla()); }
  verTodo() {
    this.camara.zoom = Math.max(this._zoomMinimo(), this._zoomTodo());
    this.camara.x = (this.mapa.ancho * C) / 2;
    this.camara.y = (this.mapa.alto * C) / 2;
    this._aplicarCamara();
  }

  _centroPantalla() {
    const caja = this.app.canvas.getBoundingClientRect();
    return [caja.left + caja.width / 2, caja.top + caja.height / 2];
  }

  _aplicarCamara() {
    const w = this.elemento.clientWidth;
    const h = this.elemento.clientHeight;
    const z = this.camara.zoom;
    // La cámara no deja salir del mundo (con el mapa continuo) o del mapa (sin él).
    const [ox, oy] = this.mapa.origen ?? [0, 0];
    const [MW, MH] = this.mapa.mundo ?? [this.mapa.ancho, this.mapa.alto];
    const x0 = -ox * C; const x1 = (MW - ox) * C;
    const y0 = -oy * C; const y1 = (MH - oy) * C;
    const mitadW = w / 2 / z;
    const mitadH = h / 2 / z;
    this.camara.x = x1 - x0 <= 2 * mitadW ? (x0 + x1) / 2 : Math.max(x0 + mitadW, Math.min(x1 - mitadW, this.camara.x));
    this.camara.y = y1 - y0 <= 2 * mitadH ? (y0 + y1) / 2 : Math.max(y0 + mitadH, Math.min(y1 - mitadH, this.camara.y));
    this.mundo.scale.set(z);
    this.mundo.position.set(Math.round(w / 2 - this.camara.x * z), Math.round(h / 2 - this.camara.y * z));
    this._colocarMinimapa();
    this.vecindad?.alMover();
  }

  // Si se destruye mientras PixiJS aún arranca (al cambiar de asentamiento enseguida), se espera a
  // que termine el arranque y se cierra entonces: cerrarlo antes da error.
  destruir() {
    this.destruido = true;
    this._observador?.disconnect();
    this.vecindad?.destruir();
    if (this.listo) this._cerrar();
  }

  _cerrar() {
    if (this.cerrado) return;
    this.cerrado = true;
    if (this.embebida) {
      this.app.ticker.remove(this._tic);
      this.luces?.contenedor.destroy({ children: true });
      this.mundo?.destroy({ children: true });
      return;
    }
    this.app.destroy(true, { children: true });
  }

  // ---- texturas ----

  _recorte(imagen, [x, y, w, h]) {
    const clave = `${imagen}:${x},${y},${w},${h}`;
    if (!this.texturas.has(clave)) {
      const fuente = typeof imagen === "string" && this.imagenes[imagen] ? this.imagenes[imagen] : Assets.get(imagen);
      this.texturas.set(clave, new Texture({ source: fuente.source, frame: new Rectangle(x, y, w, h) }));
    }
    return this.texturas.get(clave);
  }

  _pieza(conjunto, mascara) {
    const [cx, cy] = A.PIEZA_POR_VECINOS[mascara];
    const [ox, oy] = conjunto.origen;
    return this._recorte(conjunto.imagen, [(ox + cx) * C, (oy + cy) * C, C, C]);
  }

  // ---- suelo y elementos fijos ----

  // Casillas donde no se ponen adornos: solares, muralla, almacén, molino, puente y objetos de
  // la plaza y de los campos.
  // Luces que no dependen de las casas: la puerta del almacén, los faroles de la plaza y el molino.
  _lucesFijas() {
    const m = this.mapa;
    const [ax, ay] = m.almacen;
    const faroles = PLAZA.filter(([, pieza]) => pieza === A.FAROL)
      .map(([, , dx, dy]) => ({ x: (ax + dx + 0.5) * C, y: (ay + dy - 0.6) * C, radio: 26 }));
    const molino = m.molino ? [{ x: (m.molino[0] - 1.5) * C, y: (m.molino[1] + 0.2) * C, radio: 24 }] : [];
    return [{ x: (ax + 0.5) * C, y: (ay - 1.6) * C, radio: 34 }, ...faroles, ...molino];
  }

  _marcarOcupadas() {
    const m = this.mapa;
    const o = new Set();
    const zona = (x0, y0, x1, y1) => {
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) o.add(`${x},${y}`);
    };
    for (const [x, y] of m.solares) zona(x - 2, y - 2, x + 2, y + 1);
    for (const t of m.tramos) for (const [x, y] of t) o.add(`${x},${y}`);
    const [ax, ay] = m.almacen;
    zona(ax - 2, ay - 8, ax + 2, ay - 2);
    if (m.molino) zona(m.molino[0] - 4, m.molino[1] - 4, m.molino[0] + 1, m.molino[1]);
    for (const [px, py] of this._listaPuentes()) zona(px - 4, py - 1, px + 4, py + 2);
    for (const [x, y] of m.muros_fijos ?? []) o.add(`${x},${y}`);
    for (const [, , dx, dy] of PLAZA) zona(ax + dx - 1, ay + dy - 1, ax + dx + 1, ay + dy);
    const [[cx0], [cx1, cy1]] = m.campos;
    zona(cx0, cy1 + 1, cx1, cy1 + 2);
    this.ocupadas = o;
  }

  _libre(x, y) { return !this.ocupadas.has(`${x},${y}`); }

  // Los mapas de siempre tienen un puente; los formatos nuevos, varios o ninguno.
  _listaPuentes() { return this.mapa.puentes ?? (this.mapa.puente ? [this.mapa.puente] : []); }

  _dibujarSuelo() {
    const { casillas, ancho, alto } = this.mapa;
    const tipo = (x, y) => (x < 0 || y < 0 || x >= ancho || y >= alto ? null : casillas[y][x]);
    const mascara = (x, y, es) => {
      const igual = (nx, ny) => { const t = tipo(nx, ny); return t === null || es(t); };
      return (igual(x, y - 1) ? 1 : 0) | (igual(x + 1, y) ? 2 : 0) | (igual(x, y + 1) ? 4 : 0) | (igual(x - 1, y) ? 8 : 0);
    };
    const suelo = new Container();
    for (let y = 0; y < alto; y++) {
      for (let x = 0; x < ancho; x++) {
        const t = casillas[y][x];
        const r = azar(x, y);
        const hierba = r < 0.18 && t !== "a" ? this.suelo.detalle[Math.floor(r * 50) % this.suelo.detalle.length] : this.suelo.hierba;
        this._poner(suelo, this._recorte("suelo", [...hierba, C, C]), x, y);
        if (TIERRA.has(t)) this._poner(suelo, this._pieza(this.suelo.conjunto, mascara(x, y, (o) => TIERRA.has(o))), x, y);
        if (t === "a") this._poner(suelo, this._pieza(this.suelo.agua, mascara(x, y, (o) => o === "a")), x, y);
        // Adornos pequeños: flores, arbustos y piedras en la hierba, y matorral bajo los árboles.
        const r2 = azar(x + 17, y + 31);
        let adorno = null;
        if (t === "h" && this._libre(x, y)) {
          if (r2 < 0.035) adorno = elegir(A.FLORES, r2 / 0.035);
          else if (r2 < 0.055) adorno = elegir(A.ARBUSTOS, (r2 - 0.035) / 0.02);
          else if (r2 < 0.059) adorno = elegir(A.PIEDRAS, (r2 - 0.055) / 0.004);
        } else if (t === "b" && r2 < 0.25) {
          adorno = elegir(A.ARBUSTOS, r2 / 0.25);
        }
        if (adorno) this._poner(suelo, this._recorte("naturaleza", adorno), x, y);
      }
    }
    this.puentes = this._listaPuentes().map((p) => this._dibujarPuente(suelo, p)).filter(Boolean);
    // El suelo no cambia: se pinta una vez, por trozos de 64 × 64 casillas (una ciudad mide más de
    // lo que cabe en una sola textura), y otra vez en pequeño para el minimapa.
    const TROZO = 64 * C;
    const W = ancho * C;
    const H = alto * C;
    for (let y = 0; y < H; y += TROZO) {
      for (let x = 0; x < W; x += TROZO) {
        const frame = new Rectangle(x, y, Math.min(TROZO, W - x), Math.min(TROZO, H - y));
        const trozo = new Sprite(this.app.renderer.generateTexture({ target: suelo, frame, resolution: 1 }));
        trozo.position.set(x, y);
        this.mundo.addChild(trozo);
      }
    }
    this.texturaSuelo = this.app.renderer.generateTexture({ target: suelo, resolution: Math.min(1, 176 / W) });
    this.escalaSuelo = Math.min(1, 176 / W);
    suelo.destroy({ children: true });
  }

  // Tablones sobre el río, de la orilla oeste a la este, en las dos filas del camino.
  _dibujarPuente(suelo, [px, y]) {
    const { casillas } = this.mapa;
    // El agua de esas dos filas cerca del puente (un mapa puede tener lagos en la misma fila).
    const agua = [y, y + 1].flatMap((f) => [...(casillas[f] ?? "")].map((t, x) => (t === "a" && Math.abs(x - px) <= 4 ? x : null))
      .filter((x) => x !== null));
    if (!agua.length) return null;
    const x0 = Math.min(...agua) - 1;
    const x1 = Math.max(...agua) + 1;
    const [ox, oy] = A.TABLONES.origen;
    for (let x = x0; x <= x1; x++) {
      const col = x === x0 ? 0 : x === x1 ? 2 : 1;
      // Los tablones del paquete son muy naranjas; se oscurecen para que parezcan madera vieja.
      this._poner(suelo, this._recorte("agua", [ox + col * C, oy, C, C]), x, y).tint = A.TINTE_TABLONES;
      this._poner(suelo, this._recorte("agua", [ox + col * C, oy + 2 * C, C, C]), x, y + 1).tint = A.TINTE_TABLONES;
    }
    return { x0, x1, y };
  }

  // Ondas animadas en algunas casillas del río.
  _dibujarAgua() {
    const { casillas, ancho, alto } = this.mapa;
    const marcos = [...Array(A.ONDAS.fotogramas).keys()].map((i) => this._recorte("ondas", [i * C, 0, C, C]));
    for (let y = 0; y < alto; y++) {
      for (let x = 0; x < ancho; x++) {
        // Las ondas traen su propio fondo de agua: solo van donde no tapan la orilla.
        const agua = (nx, ny) => casillas[ny]?.[nx] === "a";
        if (!agua(x, y) || !agua(x - 1, y) || !agua(x + 1, y) || azar(x + 5, y + 9) > 0.3) continue;
        if (this.puentes?.some((p) => y >= p.y && y <= p.y + 1 && x >= p.x0 && x <= p.x1)) continue;
        const onda = new AnimatedSprite(marcos);
        onda.position.set(x * C, y * C);
        onda.animationSpeed = 0.05 + 0.03 * azar(y, x);
        onda.gotoAndPlay(Math.floor(azar(x, y + 3) * A.ONDAS.fotogramas));
        this.ondas.addChild(onda);
      }
    }
  }

  _poner(contenedor, textura, x, y) {
    const s = new Sprite(textura);
    s.position.set(x * C, y * C);
    contenedor.addChild(s);
    return s;
  }

  // Sprite apoyado en el borde de abajo de una casilla, ordenado por profundidad.
  _objeto(textura, x, y) {
    const s = new Sprite(textura);
    s.anchor.set(0.5, 1);
    s.position.set((x + 0.5) * C, (y + 1) * C);
    s.zIndex = (y + 1) * C;
    this.objetos.addChild(s);
    return s;
  }

  _dibujarFijos() {
    const m = this.mapa;
    // Los campos se dibujan como tres huertos vallados, con un paso de tierra entre ellos. El del
    // centro es de trigo. La valla se abre donde llega el camino.
    const [[cx0, cy0], [cx1, cy1]] = m.campos;
    // Se parten a lo largo del lado más largo (en los mapas nuevos los campos pueden ir tumbados).
    const tumbados = cx1 - cx0 > cy1 - cy0;
    const largo = Math.floor(((tumbados ? cx1 - cx0 : cy1 - cy0) - 1) / 3);
    const huertos = [0, 1, 2].map((k) => tumbados
      ? [[cx0 + k * (largo + 1), cy0], [k === 2 ? cx1 : cx0 + k * (largo + 1) + largo - 1, cy1]]
      : [[cx0, cy0 + k * (largo + 1)], [cx1, k === 2 ? cy1 : cy0 + k * (largo + 1) + largo - 1]]);
    huertos.forEach(([[x0, y0], [x1, y1]], k) => {
      for (let y = y0 + 1; y < y1; y += 2) {
        for (let x = x0 + 1; x < x1; x++) {
          this._poner(this.cultivos, this._recorte("naturaleza", A.CULTIVO), x, y).trigo = k === 1;
        }
      }
      this._vallar([[x0, y0], [x1, y1]], "casas", A.VALLA, (x, y) => !(x === cx0 && m.casillas[y][x - 1] === "m"));
    });
    [[0, 0], [1, 0], [3, 0]].forEach(([dx, dy]) => this._objeto(this._recorte("elementos", A.PAJA), cx0 + 1 + dx, cy1 + 2 + dy));
    this._objeto(this._recorte("elementos", A.CARRO), cx0 + 6, cy1 + 2);

    m.cantera.forEach(([x, y], i) => { if (i % 2 === 0) this._poner(this.rocas, this._recorte("naturaleza", A.ROCA), x, y); });

    // Cada árbol tiene una forma fija: redondo (la mayoría), pino o grande.
    this.arboles = m.arboles.map(([x, y]) => {
      const r = azar(x + 11, y + 7);
      // El terreno cambia qué árboles hay: más pinos en el bosque, árboles secos en el pantano.
      const pinos = { bosque: 0.45 }[this.bioma] ?? 0.15;
      const forma = this.bioma === "pantano" && r < 0.5 ? "muerto" : r < pinos ? "pino" : r < pinos + 0.12 ? "grande" : "redondo";
      return { x, y, forma, variante: Math.floor(azar(y, x) * 3), sprite: this._objeto(Texture.EMPTY, x, y), clave: null };
    });
    const [ax, ay] = m.almacen;
    this._objeto(this._recorte("casas", A.ALMACEN), ax, ay - 2);
    for (const [imagen, pieza, dx, dy] of PLAZA) this._objeto(this._recorte(imagen, pieza), ax + dx, ay + dy);

    // Barandillas del puente: la de arriba queda detrás de quien cruza y la de abajo, delante.
    for (const p of this.puentes) {
      for (let x = p.x0; x <= p.x1; x++) {
        this._objeto(this._recorte("casas", A.VALLA.frente), x, p.y - 1).position.y += 5;
        this._objeto(this._recorte("casas", A.VALLA.frente), x, p.y + 1).position.y += 5;
      }
    }

    // El molino: un edificio en la orilla y la rueda pegada a él, sobre el agua.
    if (m.molino) this._dibujarMolino(m);
    this._dibujarMuralla(m);
    this.obra = this._objeto(this._recorte("casas", A.CASAS[0]), 0, 0);
    this.obra.visible = false;
    this.obra.alpha = 0.4;
  }

  _dibujarMolino(m) {
    const edificio = this._objeto(this._recorte("casas", A.EDIFICIO_MOLINO), m.molino[0] - 2, m.molino[1]);
    edificio.position.x = (m.molino[0] - 1.5) * C;
    const marcos = [0, 1, 2].map((i) => this._recorte("molino", [i * A.MOLINO.ancho, 0, A.MOLINO.ancho, A.MOLINO.alto]));
    const molino = new AnimatedSprite(marcos);
    molino.anchor.set(0.5, 1);
    molino.position.set((m.molino[0] + 1) * C, (m.molino[1] + 1) * C);
    molino.zIndex = (m.molino[1] + 1) * C + 1;
    molino.animationSpeed = 0.08;
    molino.play();
    this.objetos.addChild(molino);
  }

  // Muralla: cada tramo es una fila de casillas de muro de piedra; se enseñan los construidos. La
  // pieza de cada casilla (esquina, frente o lado) sale de sus vecinas, para que valga cualquier
  // forma: cuadrada, alargada u octógono. La muralla interior de las ciudades está siempre entera.
  _dibujarMuralla(m) {
    const muro = new Set([...m.tramos.flat(), ...(m.muros_fijos ?? [])].map(([x, y]) => `${x},${y}`));
    const hay = (x, y) => muro.has(`${x},${y}`);
    const pieza = (x, y) => {
      const n = hay(x, y - 1); const s = hay(x, y + 1); const e = hay(x + 1, y); const o = hay(x - 1, y);
      if (s && e && !n && !o) return A.MURO.arribaIzquierda;
      if (s && o && !n && !e) return A.MURO.arribaDerecha;
      if (n && e && !s && !o) return A.MURO.abajoIzquierda;
      if (n && o && !s && !e) return A.MURO.abajoDerecha;
      return (n || s) && !(e || o) ? A.MURO.lado : A.MURO.frente;
    };
    this.tramos = m.tramos.map((casillas) => casillas.map(([x, y]) => this._objeto(this._recorte("muralla", pieza(x, y)), x, y)));
    for (const [x, y] of m.muros_fijos ?? []) this._objeto(this._recorte("muralla", pieza(x, y)), x, y);
  }

  // Devuelve, para una casilla del borde de un rectángulo, la pieza que le toca: esquina, tramo de
  // frente (lados de arriba y abajo) o tramo de lado (izquierdo y derecho).
  _piezaDeBorde([[x0, y0], [x1, y1]], piezas) {
    return (x, y) => {
      if (y === y0) return x === x0 ? piezas.arribaIzquierda : x === x1 ? piezas.arribaDerecha : piezas.frente;
      if (y === y1) return x === x0 ? piezas.abajoIzquierda : x === x1 ? piezas.abajoDerecha : piezas.frente;
      return piezas.lado;
    };
  }

  // Pone una valla por el borde de un rectángulo, en las casillas donde `poner(x, y)` lo permite.
  _vallar(rect, imagen, piezas, poner) {
    const [[x0, y0], [x1, y1]] = rect;
    const pieza = this._piezaDeBorde(rect, piezas);
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const borde = x === x0 || x === x1 || y === y0 || y === y1;
        if (borde && poner(x, y)) this._objeto(this._recorte(imagen, pieza(x, y)), x, y);
      }
    }
  }

  _encajar() {
    if (!this.app || !this.mapa) return;
    this.clima?.medir(this.elemento.clientWidth, this.elemento.clientHeight);
    // La primera vez, doble tamaño en pantallas grandes y tamaño real en el móvil (o el que haga
    // falta para llenar la pantalla).
    if (this.camara.zoom === null) {
      // Un asentamiento grande se ve al principio entero o casi; uno pequeño, a doble tamaño.
      this.camara.zoom = Math.max(Math.min(this.elemento.clientWidth < 600 ? 1 : 2, Math.max(this._zoomTodo(), 0.5)),
        this._zoomMinimo());
    }
    this.camara.zoom = Math.max(this.camara.zoom, this._zoomMinimo());
    this._aplicarCamara();
  }

  // ---- minimapa ----

  // La aldea entera en pequeño, abajo a la derecha: suelo, árboles y casas, los habitantes como
  // puntos y un rectángulo con la parte que se está viendo. Al pulsarlo, la cámara salta allí.
  _crearMinimapa() {
    const ANCHO_MINI = 176;
    const W = this.mapa.ancho * C;
    const H = this.mapa.alto * C;
    const e = ANCHO_MINI / W;
    this.mini = new Container();
    this.mini.escala = e;
    this.mini.ancho = ANCHO_MINI;
    this.mini.alto = Math.round(H * e);
    const marco = new Graphics().roundRect(-4, -4, this.mini.ancho + 8, this.mini.alto + 8, 10).fill({ color: 0x15281f, alpha: 0.85 });
    const suelo = new Sprite(this.texturaSuelo);        // ya hecha en pequeño (ver _dibujarSuelo)
    suelo.scale.set(e / this.escalaSuelo);
    const arboles = new Graphics();
    for (const [x, y] of this.mapa.arboles) arboles.circle((x + 0.5) * C * e, (y + 0.5) * C * e, 1.6);
    arboles.fill(0x2e6b35);
    this.mini.casas = new Graphics();
    this.mini.puntos = new Graphics();
    this.mini.vista = new Graphics();
    const recorte = new Graphics().roundRect(0, 0, this.mini.ancho, this.mini.alto, 6).fill(0xffffff);
    const contenido = new Container();
    contenido.addChild(suelo, arboles, this.mini.casas, this.mini.puntos, this.mini.vista, recorte);
    contenido.mask = recorte;
    this.mini.addChild(marco, contenido);
    this.app.stage.addChild(this.mini);
    this.mini.visible = this.minimapaVisible ?? true;
  }

  mostrarMinimapa(visible) {
    this.minimapaVisible = visible;
    if (this.mini) this.mini.visible = visible;
  }

  _colocarMinimapa() {
    if (!this.mini) return;
    this.mini.position.set(this.elemento.clientWidth - this.mini.ancho - 20, this.elemento.clientHeight - this.mini.alto - 20);
    const e = this.mini.escala;
    const z = this.camara.zoom;
    const w = this.elemento.clientWidth / z;
    const h = this.elemento.clientHeight / z;
    this.mini.vista.clear()
      .rect((this.camara.x - w / 2) * e, (this.camara.y - h / 2) * e, w * e, h * e)
      .stroke({ color: 0xffffff, width: 1.5 });
  }

  _actualizarMinimapa(estado) {
    if (!this.mini) return;
    const e = this.mini.escala;
    this.mini.casas.clear();
    for (const c of estado.casas) this.mini.casas.rect((c.x - 1.5) * C * e, (c.y - 2) * C * e, 4 * C * e, 3 * C * e);
    this.mini.casas.fill(0xe0703a);
    this.mini.puntos.clear();
    for (const h of estado.habitantes) {
      if (!h.fuera) this.mini.puntos.circle((h.x + 0.5) * C * e, (h.y + 0.5) * C * e, h.id === this.marcado ? 3 : 2);
    }
    this.mini.puntos.fill(0xf5d36b);
  }

  _pulsarMinimapa(evento) {
    if (!this.mini?.visible) return false;
    const caja = this.app.canvas.getBoundingClientRect();
    const x = evento.clientX - caja.left - this.mini.x;
    const y = evento.clientY - caja.top - this.mini.y;
    if (x < 0 || y < 0 || x > this.mini.ancho || y > this.mini.alto) return false;
    if (this.siguiendo) { this.siguiendo = false; this.alDejarDeSeguir(); }
    this.camara.x = x / this.mini.escala;
    this.camara.y = y / this.mini.escala;
    this._aplicarCamara();
    return true;
  }

  // ---- estado de cada turno ----

  async actualizar(estado) {
    this.ultimo = estado;
    // Con lluvia o nieve el día se ve algo más apagado; las luces solo dependen de la hora.
    const clima = climaDe(estado);
    const oscuro = oscuridad(estado.hora);
    this.noche.alpha = Math.max(oscuro, { lluvia: 0.16, nieve: 0.08 }[clima] ?? 0);
    const faroles = (estado.evolucion?.faroles ?? []).map(([x, y], k) => ({ id: `farol${k}`, x, y: y - 1 }));
    this.luces.actualizar([...estado.casas, ...faroles], oscuro);
    this.ataques.actualizar(estado.ataque, estado);
    if (!this.embebida) this.clima.poner(clima, this.elemento.clientWidth, this.elemento.clientHeight);
    this._actualizarArboles(estado);
    this._actualizarCultivos(estado.estacion);
    this._actualizarCasas(estado);
    this._actualizarMuralla(estado);
    this._actualizarEvolucion(estado.evolucion);
    await this._actualizarHabitantes(estado);
    if (!this.embebida) this._actualizarMinimapa(estado);
  }

  _actualizarArboles(estado) {
    const cortados = estado.arboles_cortados;
    const quitados = new Set(estado.evolucion?.arboles_quitados ?? []);
    const e = this.bioma === "nieve" ? "invierno" : estado.estacion;   // en la nieve, siempre nevados
    for (let i = 0; i < this.arboles.length; i++) {
      const a = this.arboles[i];
      a.sprite.visible = !quitados.has(i);
      const crecido = cortados[i] ?? 1;
      let pieza;
      let tinte = 0xffffff;
      if (crecido < 0.5) pieza = A.TOCON;
      else if (crecido < 1) pieza = A.BROTE;
      else if (a.forma === "muerto") pieza = A.ARBOL.muerto;
      else if (a.forma === "pino") pieza = e === "invierno" ? A.ARBOL.pinoNieve : A.ARBOL.pino;
      else if (a.forma === "grande") {
        pieza = { invierno: A.ARBOL.grandeNieve, "otoño": A.ARBOL.grandeOtono }[e]
          ?? (e === "primavera" && azar(a.x, a.y) < 0.35 ? A.ARBOL.grandeRosa : A.ARBOL.grande);
      } else if (e === "invierno") pieza = A.ARBOL.nieve;
      else if (e === "primavera" && azar(a.x, a.y) < 0.35) pieza = A.ARBOL.rosa;
      else {
        pieza = A.ARBOL.redondo[a.variante];
        if (e === "otoño") tinte = azar(a.x + 3, a.y) < 0.5 ? 0xf0a040 : 0xe07038;
      }
      const clave = `${pieza}:${tinte}`;
      if (clave === a.clave) continue;
      a.clave = clave;
      a.sprite.texture = this._recorte("naturaleza", pieza);
      a.sprite.tint = tinte;
    }
  }

  _actualizarCultivos(estacion) {
    if (estacion === this.estacion) return;
    this.estacion = estacion;
    this.cultivos.visible = estacion !== "invierno";
    // En primavera todo son brotes. En verano el huerto de trigo ya está dorado y en otoño, todos.
    const brote = this._recorte("naturaleza", A.SEMILLA);
    const verde = this._recorte("naturaleza", A.CULTIVO);
    const dorado = this._recorte("trigo", A.TRIGO);
    for (const s of this.cultivos.children) {
      s.texture = estacion === "primavera" ? brote : estacion === "otoño" || s.trigo ? dorado : verde;
    }
  }

  // Casas y, en pueblos, villas y ciudades, edificios (`modelo`: mercado, templo, dojo…).
  _actualizarCasas(estado) {
    const vistas = new Set();
    for (const c of estado.casas) {
      vistas.add(c.id);
      let [imagen, recorte] = A.EDIFICIOS[c.modelo] ?? ["casas", A.CASAS[c.id % A.CASAS.length]];
      if (c.modelo === "vigia" && c.estado != null && c.estado < 50) recorte = A.VIGIA_GASTADA[c.estado > 0 ? 0 : 1];
      const clave = `${c.modelo ?? "casa"}:${c.x},${c.y}:${recorte}`;
      let s = this.casas.get(c.id);
      if (!s) {
        s = this._objeto(this._recorte(imagen, recorte), c.x, c.y);
        this.casas.set(c.id, s);
      } else if (s.clave !== clave) {
        s.texture = this._recorte(imagen, recorte);
        s.position.set((c.x + 0.5) * C, (c.y + 1) * C);
        s.zIndex = (c.y + 1) * C;
      }
      s.clave = clave;
      s.visible = true;
      // Quemada o en ruinas, oscura; estropeada, apagada; de piedra, gris.
      const ruinas = c.quemada || c.estado === 0;
      s.tint = ruinas ? A.TINTE_RUINAS : c.estado != null && c.estado < 50 ? A.TINTE_ESTROPEADO
        : c.modelo === "casa_piedra" ? A.TINTE_PIEDRA : A.TINTE_MODELO[c.modelo] ?? 0xffffff;
      s.alpha = ruinas ? 0.75 : 1;
    }
    for (const [id, s] of this.casas) if (!vistas.has(id)) s.visible = false;   // p. ej., una casa quemada del todo
    this.multitud?.poner(estado.multitud ?? 0);
    const o = estado.obra;
    this.obra.visible = !!o && o.tipo !== "muralla";
    if (this.obra.visible) {
      // La casa en obra se dibuja con el mismo modelo que tendrá al acabarse.
      if (o.tipo === "casa") this.obra.texture = this._recorte("casas", A.CASAS[(estado.casas.length + 1) % A.CASAS.length]);
      else if (o.modelo && A.EDIFICIOS[o.modelo]) this.obra.texture = this._recorte(...A.EDIFICIOS[o.modelo]);
      // Una reparación o una casa de piedra se ven sobre lo que ya hay: no hace falta el fantasma.
      if (o.tipo === "reparar" || o.tipo === "casa_piedra" || o.tipo === "reforzar" || o.tipo === "faroles"
          || (o.tipo === "edificio" && !o.modelo)) this.obra.visible = false;
      this.obra.position.set((o.x + 0.5) * C, (o.y + 1) * C);
      this.obra.zIndex = (o.y + 1) * C;
      this.obra.alpha = 0.25 + 0.5 * (o.progreso / o.total);
    }
  }

  _actualizarMuralla(estado) {
    const enObra = estado.obra?.tipo === "muralla" ? estado.obra : null;
    this.tramos.forEach((sprites, k) => {
      const hecho = k < estado.muralla;
      const obra = enObra && k === estado.muralla;
      for (const s of sprites) {
        s.tint = k < (estado.evolucion?.reforzados ?? 0) ? A.TINTE_REFORZADO : 0xffffff;
        s.visible = hecho || !!obra;
        s.alpha = hecho ? 1 : 0.25 + 0.5 * (obra ? enObra.progreso / enObra.total : 0);
      }
    });
  }

  // Faroles junto a las puertas y huertos nuevos junto a los campos (evolución de la aldea).
  _actualizarEvolucion(evo) {
    if (!evo) return;
    this.faroles ??= [];
    while (this.faroles.length < evo.faroles.length) {
      const [x, y] = evo.faroles[this.faroles.length];
      this.faroles.push(this._objeto(this._recorte("elementos", A.FAROL), x, y));
    }
    if (evo.huertos && !this.huertos) {
      const [[x0, y0], [x1, y1]] = evo.huertos;
      this.huertos = true;
      for (let y = y0 + 1; y < y1; y += 2) {
        for (let x = x0 + 1; x < x1; x++) this._poner(this.cultivos, this._recorte("naturaleza", A.CULTIVO), x, y);
      }
      this._vallar([[x0, y0], [x1, y1]], "casas", A.VALLA, () => true);
      this.estacion = null;            // que los cultivos nuevos tomen el dibujo de la estación
    }
  }

  async _texturasPersonaje(nombre) {
    const url = A.personajeUrl(nombre);
    if (!Assets.cache.has(url)) await Assets.load(url);
    const hoja = Assets.get(url);
    const filas = Math.min(4, Math.floor(hoja.height / C));
    const porDireccion = {};
    for (const [dir, col] of Object.entries(A.DIRECCIONES)) {
      porDireccion[dir] = Array.from({ length: filas }, (_, f) => this._recorte(url, [col * C, f * C, C, C]));
    }
    return porDireccion;
  }

  async _actualizarHabitantes(estado) {
    const ahora = performance.now();
    const duracion = estado.segundos_por_turno * 1000 * 0.95;
    const vivos = new Set(estado.habitantes.map((h) => h.id));
    for (const [id, p] of this.habitantes) {
      if (!vivos.has(id)) { p.contenedor.destroy({ children: true }); p.marca.destroy({ children: true }); this.habitantes.delete(id); }
    }
    for (const h of estado.habitantes) {
      let p = this.habitantes.get(h.id);
      if (!p) {
        p = await this._crearHabitante(h);
        this.habitantes.set(h.id, p);
      } else if (p.personaje !== h.personaje) {
        p.personaje = h.personaje;
        p.texturas = await this._texturasPersonaje(h.personaje);
        p.anim.textures = p.texturas[p.dir];
      }
      p.datos = h;
      p.desde = { x: p.x, y: p.y };
      p.hasta = { x: h.x, y: h.y };
      p.t0 = ahora;
      p.duracion = duracion;
      p.contenedor.visible = !h.fuera;
      this._ponerIcono(p, iconoDeAccion(h));
    }
  }

  // Icono sobre la cabeza: una imagen del paquete o una "z" que sube si duerme.
  _ponerIcono(p, clave) {
    if (clave === p.clave) return;
    p.clave = clave;
    p.marca.visible = !!clave;
    p.zeta.visible = clave === "z";
    p.dibujo.visible = !!clave && clave !== "z";
    if (p.dibujo.visible) p.dibujo.texture = Assets.get(A.ICONOS[clave]);
  }

  async _crearHabitante(h) {
    const texturas = await this._texturasPersonaje(h.personaje);
    const contenedor = new Container();
    const sombra = new Sprite(Assets.get(A.IMAGENES.sombra));
    sombra.anchor.set(0.5, 0.5);
    sombra.position.set(0, -1);
    sombra.alpha = 0.5;
    const anim = new AnimatedSprite(texturas.abajo);
    anim.anchor.set(0.5, 1);
    anim.animationSpeed = 0.12;
    contenedor.addChild(sombra, anim);
    this.objetos.addChild(contenedor);
    // El icono va en su propia capa, por encima de la noche, para que se vea también de noche.
    const marca = new Container();
    const dibujo = new Sprite(Texture.EMPTY);
    dibujo.anchor.set(0.5, 1);
    const zeta = new Text({ text: "z", style: { fontFamily: "Pixelify Sans, monospace", fontSize: 40, fill: 0xffffff,
      stroke: { color: 0x1a1208, width: 8 }, fontWeight: "700" } });
    zeta.scale.set(0.2);
    zeta.anchor.set(0.5, 1);
    marca.addChild(dibujo, zeta);
    marca.visible = false;
    this.iconos.addChild(marca);
    return { contenedor, anim, marca, dibujo, zeta, clave: null, texturas, personaje: h.personaje, dir: "abajo", x: h.x, y: h.y,
      desde: { x: h.x, y: h.y }, hasta: { x: h.x, y: h.y }, t0: 0, duracion: 1, datos: h };
  }

  // El habitante visible más cercano a un punto de la pantalla, a menos de media casilla de su
  // cuerpo (o null). Se mide en píxeles del mundo, con la misma cámara que dibuja el mapa.
  _habitanteEn(clienteX, clienteY) {
    const caja = this.app.canvas.getBoundingClientRect();
    const z = this.camara.zoom;
    const x = (clienteX - caja.left - this.mundo.x) / z;
    const y = (clienteY - caja.top - this.mundo.y) / z;
    let mejor = null;
    let distancia = 11;
    for (const [id, p] of this.habitantes) {
      if (!p.contenedor.visible) continue;
      const d = Math.hypot(x - p.contenedor.x, y - (p.contenedor.y - 8));   // el centro del cuerpo
      if (d < distancia) { distancia = d; mejor = id; }
    }
    return mejor;
  }

  _animar() {
    const ahora = performance.now();
    if (!this.embebida) this.clima.animar(this.camara.zoom);
    this.ataques.animar(ahora);
    this.multitud.animar(ahora);
    for (const p of this.habitantes.values()) {
      const t = Math.min(1, (ahora - p.t0) / p.duracion);
      const dx = p.hasta.x - p.desde.x;
      const dy = p.hasta.y - p.desde.y;
      p.x = p.desde.x + dx * t;
      p.y = p.desde.y + dy * t;
      const andando = t < 1 && Math.hypot(dx, dy) > 0.05;
      if (andando) {
        const dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "derecha" : "izquierda") : (dy > 0 ? "abajo" : "arriba");
        if (dir !== p.dir) { p.dir = dir; p.anim.textures = p.texturas[dir]; }
        if (!p.anim.playing) p.anim.play();
      } else if (p.anim.playing) {
        p.anim.gotoAndStop(0);
      }
      // Las posiciones del motor son casillas; el habitante se apoya en el centro de la casilla.
      p.contenedor.position.set((p.x + 0.5) * C, (p.y + 0.5) * C + 4);
      p.contenedor.zIndex = p.contenedor.y;
      // El icono flota un poco sobre la cabeza; la "z" sube y se apaga poco a poco.
      const fase = (ahora / 1000 + p.datos.id * 0.37) % 2;
      p.marca.position.set(p.contenedor.x, p.contenedor.y - 18 + Math.sin(fase * Math.PI) * 1.2);
      p.marca.visible = !!p.clave && p.contenedor.visible && !(this.sobre === p.datos.id || (this.sobre == null && this.marcado === p.datos.id));
      if (p.zeta.visible) { p.zeta.position.set(3 + fase * 2, -fase * 4); p.zeta.alpha = 1 - fase / 2; }
      if (this.sobre === p.datos.id || (this.sobre == null && this.marcado === p.datos.id)) {
        this.etiqueta.visible = p.contenedor.visible;
        this.etiqueta.text = p.datos.nombre;
        this.etiqueta.position.set(p.contenedor.x, p.contenedor.y - 17);
      }
      if (this.marcado === p.datos.id) {
        this.anillo.visible = p.contenedor.visible;
        this.anillo.position.set(p.contenedor.x, p.contenedor.y - 1);
        this.anillo.zIndex = p.contenedor.zIndex - 0.5;
        if (this.siguiendo) {
          this.camara.x = p.contenedor.x;
          this.camara.y = p.contenedor.y;
          this._aplicarCamara();
        }
      }
    }
    if (this.marcado == null || !this.habitantes.has(this.marcado)) {
      this.anillo.visible = false;
      if (this.sobre == null) this.etiqueta.visible = false;
    }
  }
}
