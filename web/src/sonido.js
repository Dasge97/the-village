// Música y sonidos del paquete. Empiezan apagados: el navegador no deja sonar nada hasta que el
// usuario pulsa, y además así nadie se lleva un susto al entrar. Lo elegido se recuerda.
// Los audios solo se descargan la primera vez que se activa el sonido.

import { reactive } from "vue";

const A = "/sprites/Audio/";
const PISTAS = {
  dia: { url: A + "Musics/33 - Calm Village.ogg", volumen: 0.35 },
  noche: { url: A + "Musics/22 - Dream.ogg", volumen: 0.3 },
  rio: { url: A + "Sounds/Ambient/River.wav", volumen: 0.12 },
  lluvia: { url: A + "Sounds/Ambient/Rain.wav", volumen: 0.35 },
  viento: { url: A + "Sounds/Ambient/Wind.wav", volumen: 0.25 },
};
const EFECTOS = {
  pajaro: { url: A + "Sounds/Creature/Bird.wav", volumen: 0.25 },
  alerta: { url: A + "Sounds/Alert/Alert2.wav", volumen: 0.4 },
  tajo: { url: A + "Sounds/Whoosh & Slash/Slash.wav", volumen: 0.3 },
  alegria: { url: A + "Jingles/Success1.wav", volumen: 0.35 },
};
const ALEGRES = new Set(["nacimiento", "pareja"]);

const leer = () => { try { return localStorage.getItem("sonido") === "1"; } catch { return false; } };

export const sonido = reactive({ activo: leer() });

const pistas = {};
let ultimoTurnoVisto = null;
let ultimoAtaque = null;

function pista(clave) {
  if (!pistas[clave]) {
    const a = new Audio(PISTAS[clave].url);
    a.loop = true;
    a.volume = 0;
    pistas[clave] = a;
  }
  return pistas[clave];
}

// Sube o baja una pista poco a poco hasta su volumen (o hasta 0, y entonces la para).
function fundir(clave, encendida) {
  if (!encendida && !pistas[clave]) return;      // nunca ha sonado: nada que apagar ni que descargar
  const a = pista(clave);
  const destino = encendida ? PISTAS[clave].volumen : 0;
  clearInterval(a.fundido);
  if (encendida && a.paused) a.play().catch(() => {});
  a.fundido = setInterval(() => {
    const paso = 0.02;
    a.volume = Math.abs(a.volume - destino) <= paso ? destino : a.volume + Math.sign(destino - a.volume) * paso;
    if (a.volume === destino) {
      clearInterval(a.fundido);
      if (!encendida) a.pause();
    }
  }, 80);
}

export function efecto(clave) {
  if (!sonido.activo) return;
  const a = new Audio(EFECTOS[clave].url);
  a.volume = EFECTOS[clave].volumen;
  a.play().catch(() => {});
}

export function alternarSonido() {
  sonido.activo = !sonido.activo;
  try { localStorage.setItem("sonido", sonido.activo ? "1" : "0"); } catch { /* sin almacenamiento */ }
  if (!sonido.activo) for (const clave of Object.keys(pistas)) fundir(clave, false);
  else if (ultimo) actualizarSonido(ultimo.estado, ultimo.clima);
}

let ultimo = null;

// Al primer clic en la página: si el sonido estaba activo de otra visita, ya puede empezar a sonar.
window.addEventListener("pointerdown", () => { if (sonido.activo && ultimo) actualizarSonido(ultimo.estado, ultimo.clima); }, { once: true });

// Se llama con cada estado de la aldea: elige la música, el ambiente y los avisos de lo nuevo.
export function actualizarSonido(estado, clima) {
  ultimo = { estado, clima };
  if (!sonido.activo) { ultimoTurnoVisto = estado.turno; return; }
  fundir("dia", !estado.de_noche);
  fundir("noche", estado.de_noche);
  fundir("rio", true);
  fundir("lluvia", clima === "lluvia");
  fundir("viento", clima === "nieve");
  if (!estado.de_noche && clima !== "lluvia" && Math.random() < 0.08) efecto("pajaro");
  // Sucesos nuevos desde el último estado: un ataque suena a alerta y un nacimiento o pareja, a alegría.
  if (ultimoTurnoVisto !== null) {
    const nuevos = estado.sucesos.filter((s) => s.turno > ultimoTurnoVisto);
    if (nuevos.some((s) => ALEGRES.has(s.tipo))) efecto("alegria");
  }
  if (estado.ataque && estado.ataque.turno !== ultimoAtaque) {
    ultimoAtaque = estado.ataque.turno;
    efecto("alerta");
  }
  ultimoTurnoVisto = estado.turno;
}
