// Gente por la calle en pueblos, villas y ciudades: solo dibujo, sin ficha. Cada uno anda de una
// casilla de camino o plaza a otra elegida al azar y, al llegar, se para un momento y sigue.
// Cuánta gente hay lo dice el servidor (`multitud`, menos de noche).

import { AnimatedSprite } from "pixi.js";
import { CASILLA as C } from "./atlas.js";

const PERSONAJES = ["Villager", "Villager2", "Villager3", "Villager4", "Villager5", "Villager6", "Woman",
  "ManGreen", "Hunter", "Monk", "OldMan", "OldWoman", "Child", "Princess"];
const VELOCIDAD = 1.4;     // casillas por segundo

export class Multitud {
  constructor(escena) {
    this.escena = escena;
    this.gente = [];
    this.calles = [];
    const { casillas } = escena.mapa;
    casillas.forEach((fila, y) => [...fila].forEach((t, x) => { if (t === "m" || t === "p") this.calles.push([x, y]); }));
  }

  _calle() { return this.calles[Math.floor(Math.random() * this.calles.length)]; }

  async poner(cuantos) {
    if (!this.calles.length || this.cambiando) return;
    this.cambiando = true;
    while (this.gente.length > cuantos) this.gente.pop().sprite.destroy();
    while (this.gente.length < cuantos) {
      const texturas = await this.escena._texturasPersonaje(PERSONAJES[Math.floor(Math.random() * PERSONAJES.length)]);
      const sprite = new AnimatedSprite(texturas.abajo);
      sprite.anchor.set(0.5, 1);
      sprite.animationSpeed = 0.12;
      sprite.play();
      const [x, y] = this._calle();
      this.escena.objetos.addChild(sprite);
      this.gente.push({ sprite, texturas, x, y, destino: this._calle(), espera: 0, dir: "abajo" });
    }
    this.cambiando = false;
  }

  animar(ahora) {
    const pasado = Math.min(0.1, (ahora - (this.antes ?? ahora)) / 1000);
    this.antes = ahora;
    for (const p of this.gente) {
      if (p.espera > 0) {
        p.espera -= pasado;
        if (p.sprite.playing) p.sprite.gotoAndStop(0);
      } else {
        const dx = p.destino[0] - p.x;
        const dy = p.destino[1] - p.y;
        const d = Math.hypot(dx, dy);
        if (d < 0.05) {
          p.destino = this._calle();
          p.espera = 1 + Math.random() * 4;
        } else {
          const paso = Math.min(d, VELOCIDAD * pasado);
          p.x += (dx / d) * paso;
          p.y += (dy / d) * paso;
          const dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "derecha" : "izquierda") : (dy > 0 ? "abajo" : "arriba");
          if (dir !== p.dir) { p.dir = dir; p.sprite.textures = p.texturas[dir]; }
          if (!p.sprite.playing) p.sprite.play();
        }
      }
      p.sprite.position.set((p.x + 0.5) * C, (p.y + 0.5) * C + 4);
      p.sprite.zIndex = p.sprite.y;
    }
  }
}
