// La pantalla en la que está el usuario va en la dirección, para poder recargar, volver atrás y
// compartir el enlace. El mapa está siempre debajo; cada sección es un panel encima de él:
//   #/                   solo el mapa
//   #/habitantes         lista de habitantes        #/habitantes/12   ficha del habitante 12
//   #/habitantes/ninos   lista con la subpestaña Niños   #/habitantes/12/familia   ficha, subpestaña Familia
//   #/historia           cifras de hoy y sucesos    #/historia/peligros   solo los peligros
//   #/historia/grande    en grande, con la historia año a año   #/historia/grande/vida   en grande, solo vida
//   #/familias           árbol genealógico          #/familias/12     árbol con la persona 12 elegida
//   #/mundo              mapa del mundo con todos los asentamientos
//   #/info               qué es La aldea y cómo funciona
//   #/novedades          versiones y sus cambios
//   #/admin              panel de administración (con contraseña)   #/admin/gasto   subpestaña Gasto
// Las direcciones antiguas #/cronica… llevan a #/historia…. La segunda aldea añade ?aldea=2 al final.

import { reactive } from "vue";

export const PANELES = [
  { id: "mundo", texto: "Mapa del mundo", icono: "mapa" },
  { id: "habitantes", texto: "Habitantes", icono: "personas" },
  { id: "historia", texto: "Historia", icono: "historial" },
  { id: "familias", texto: "Familias", icono: "familia" },
  { id: "info", texto: "Qué es La aldea", icono: "info" },
  { id: "novedades", texto: "Novedades", icono: "chispa", oculto: true },   // se abre desde la barra de estado
  { id: "admin", texto: "Administración", icono: "candado", oculto: true },  // también desde la barra de estado
];

const GRANDE = "grande";

function leer() {
  const [camino, consulta] = location.hash.replace(/^#\/?/, "").split("?");
  const aldea = Number(new URLSearchParams(consulta).get("aldea")) || 1;
  const [nombre, ...resto] = camino.split("/").filter(Boolean);
  const panel = nombre === "cronica" ? "historia" : nombre;
  const numero = resto.find((s) => /^\d+$/.test(s));
  return {
    aldea,
    panel: PANELES.some((p) => p.id === panel) ? panel : null,
    id: numero ? Number(numero) : null,
    grande: resto.includes(GRANDE) || resto.includes("completa"),   // el panel maximizado
    pestana: resto.find((s) => !/^\d+$/.test(s) && s !== GRANDE && s !== "completa") ?? null,   // subpestaña
  };
}

export const ruta = reactive(leer());

window.addEventListener("hashchange", () => Object.assign(ruta, leer()));

const direccion = (panel, id, grande, pestana, aldea = ruta.aldea) =>
  "#/" + [panel, id, grande ? GRANDE : null, pestana].filter((x) => x !== null && x !== undefined).join("/")
  + (aldea !== 1 ? `?aldea=${aldea}` : "");

export function ir(panel = null, id = null, pestana = null, grande = false) {
  location.hash = direccion(panel, id, grande, pestana).slice(1);
}

// Cambia la subpestaña sin añadir un paso al historial del navegador.
export function irPestana(pestana) {
  history.replaceState(null, "", direccion(ruta.panel, ruta.id, ruta.grande, pestana));
  ruta.pestana = pestana;
}

// Pasa a mirar otra aldea: se cierran los paneles, porque cada aldea tiene sus propios habitantes.
export function cambiarAldea(n) {
  location.hash = direccion(null, null, false, null, n).slice(1);
}

// Para las peticiones a la API: añade la aldea que se está mirando.
export const api = (camino) => camino + (camino.includes("?") ? "&" : "?") + `aldea=${ruta.aldea}`;

// Maximiza o reduce el panel abierto, conservando la subpestaña.
export function alternarGrande() {
  ir(ruta.panel, ruta.id, ruta.pestana, !ruta.grande);
}
