// Dibuja el último ataque de monstruos mientras dura (unos 3 minutos reales). Los monstruos salen
// del borde del mapa y van a la puerta de la muralla de ese lado. Si los guardias los frenan, pelean
// allí (con tajos) y huyen entre humo; si no, entran hasta la plaza y luego se van.

import { AnimatedSprite, Assets, Container, Rectangle, Texture } from "pixi.js";
import { CASILLA as C, DIRECCIONES } from "./atlas.js";
import { efecto } from "../sonido.js";

const TURNOS = 20;   // igual que TURNOS_ATAQUE_VISIBLE en el motor
const hoja = (monstruo) => `/sprites/Actor/Monster/${monstruo}/SpriteSheet.png`;
const TAJO = "/sprites/FX/Attack/Cut/SpriteSheet.png";
const HUMO = "/sprites/FX/Smoke/Smoke/SpriteSheet.png";

const tira = (textura, ancho, alto) => Array.from({ length: Math.floor(textura.width / ancho) },
  (_, i) => new Texture({ source: textura.source, frame: new Rectangle(i * ancho, 0, ancho, alto) }));

// Punto de un recorrido de varios tramos, cada uno con su parte del tiempo: [[desde, hasta, inicio, fin]].
function enRecorrido(tramos, t) {
  for (const [a, b, t0, t1] of tramos) {
    if (t <= t1) {
      const f = t1 > t0 ? Math.max(0, Math.min(1, (t - t0) / (t1 - t0))) : 1;
      return { x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f };
    }
  }
  const ultimo = tramos[tramos.length - 1][1];
  return { x: ultimo.x, y: ultimo.y };
}

export class Ataques {
  // `capa`: contenedor ordenado por profundidad donde van los monstruos (el de los objetos del mapa).
  constructor(mapa, capa) {
    this.mapa = mapa;
    this.capa = capa;
    this.efectos = new Container();
    this.actual = null;
    const todas = mapa.tramos.flat();
    this.muro = {
      x0: Math.min(...todas.map(([x]) => x)), x1: Math.max(...todas.map(([x]) => x)),
      y0: Math.min(...todas.map(([, y]) => y)), y1: Math.max(...todas.map(([, y]) => y)),
    };
  }

  async actualizar(ataque, estado) {
    this.reloj = { turno: estado.turno, t0: performance.now(), ms: estado.segundos_por_turno * 1000 };
    const clave = ataque ? `${ataque.turno}` : null;
    if (clave === this.actual?.clave) return;
    this._quitar();
    if (!ataque) return;
    const textura = await Assets.load(hoja(ataque.monstruo));
    const porDireccion = {};
    for (const [dir, col] of Object.entries(DIRECCIONES)) {
      porDireccion[dir] = [0, 1, 2, 3].map((f) => new Texture({ source: textura.source, frame: new Rectangle(col * C, f * C, C, C) }));
    }
    const [tajo, humo] = await Promise.all([Assets.load(TAJO), Assets.load(HUMO)]);
    this.tajo = tira(tajo, 32, 32);
    this.humo = tira(humo, 32, 32);
    const [ex, ey] = ataque.entrada;
    const [ax, ay] = this.mapa.almacen;
    const entrada = { x: ex, y: ey };
    const puerta = ex === 0 ? { x: this.muro.x0 - 1, y: ay } : ey === 0 ? { x: ax, y: this.muro.y0 - 1 } : { x: ax, y: this.muro.y1 + 1 };
    const plaza = { x: ax, y: ay + 1 };
    const recorrido = ataque.frenado
      ? [[entrada, puerta, 0, 0.35], [puerta, puerta, 0.35, 0.6], [puerta, entrada, 0.6, 1]]
      : [[entrada, puerta, 0, 0.25], [puerta, plaza, 0.25, 0.45], [plaza, plaza, 0.45, 0.6], [plaza, entrada, 0.6, 1]];
    const monstruos = Array.from({ length: ataque.cuantos }, (_, i) => {
      const s = new AnimatedSprite(porDireccion.abajo);
      s.anchor.set(0.5, 1);
      s.animationSpeed = 0.14;
      s.play();
      this.capa.addChild(s);
      // Cada monstruo va un poco separado de los demás y sale un poco más tarde.
      const angulo = (i / ataque.cuantos) * Math.PI * 2;
      return { s, dx: Math.cos(angulo) * 1.3, dy: Math.sin(angulo) * 1.1, retraso: i * 0.015, dir: "abajo", x: ex, y: ey };
    });
    this.actual = { clave, ataque, recorrido, puerta, monstruos, porDireccion, ultimoTajo: 0, humoPuesto: false };
  }

  _quitar() {
    for (const m of this.actual?.monstruos ?? []) m.s.destroy();
    this.efectos.removeChildren().forEach((e) => e.destroy());
    this.actual = null;
  }

  _efecto(marcos, x, y) {
    const e = new AnimatedSprite(marcos);
    e.anchor.set(0.5);
    e.scale.set(1.4);
    e.position.set(x, y);
    e.animationSpeed = 0.3;
    e.loop = false;
    e.onComplete = () => e.destroy();
    e.play();
    this.efectos.addChild(e);
  }

  animar(ahora) {
    const a = this.actual;
    if (!a || !this.reloj) return;
    const t = (this.reloj.turno - a.ataque.turno + (ahora - this.reloj.t0) / this.reloj.ms) / TURNOS;
    if (t >= 1) { this._quitar(); return; }
    for (const m of a.monstruos) {
      const p = enRecorrido(a.recorrido, Math.max(0, t - m.retraso));
      const quieto = Math.hypot(p.x - m.x, p.y - m.y) < 0.002;
      // En la pelea o en la plaza se mueven un poco en el sitio.
      const vaiven = quieto ? Math.sin(ahora / 300 + m.dx * 5) * 0.25 : 0;
      const x = p.x + m.dx * Math.min(1, t * 6) + vaiven;
      const y = p.y + m.dy * Math.min(1, t * 6);
      if (!quieto) {
        const dx = p.x - m.x;
        const dy = p.y - m.y;
        const dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "derecha" : "izquierda") : (dy > 0 ? "abajo" : "arriba");
        if (dir !== m.dir) { m.dir = dir; m.s.textures = a.porDireccion[dir]; m.s.play(); }
      }
      m.x = p.x;
      m.y = p.y;
      m.s.position.set((x + 0.5) * C, (y + 1) * C);
      m.s.zIndex = m.s.y;
      // Al final se desvanecen en el bosque.
      m.s.alpha = t > 0.88 ? Math.max(0, (1 - t) / 0.12) : 1;
    }
    // Pelea en la puerta: tajos de los guardias cada poco; al huir, una nube de humo.
    const px = (a.puerta.x + 0.5) * C;
    const py = (a.puerta.y + 0.5) * C;
    if (a.ataque.frenado && t > 0.35 && t < 0.6 && ahora - a.ultimoTajo > 450) {
      a.ultimoTajo = ahora;
      this._efecto(this.tajo, px + (Math.random() - 0.5) * 32, py + (Math.random() - 0.5) * 24);
      if (Math.random() < 0.4) efecto("tajo");
    }
    if (a.ataque.frenado && t >= 0.6 && !a.humoPuesto) {
      a.humoPuesto = true;
      this._efecto(this.humo, px, py);
    }
  }
}
