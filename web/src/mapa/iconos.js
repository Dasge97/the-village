// Qué icono lleva cada habitante sobre la cabeza según lo que hace. Devuelve la clave de
// `ICONOS` en atlas.js, "z" para dormir (se dibuja como texto) o null si no lleva ninguno.

const HERRAMIENTA = [
  ["campesin", "azada"], ["leñador", "hacha"], ["pescador", "cana"], ["canter", "pico"], ["guardia", "katana"],
];

export function iconoDeAccion(h) {
  if (h.fuera) return null;
  switch (h.accion) {
    case "trabajar": {
      const oficio = (h.oficio || "").toLowerCase();
      return HERRAMIENTA.find(([prefijo]) => oficio.startsWith(prefijo))?.[1] ?? null;
    }
    case "construir": return "martillo";
    case "comer": return "comida";
    case "quitar": return "verguenza";
    case "dormir": return "z";
    case "descansar": return "neutro";
    case "hablar": case "ayudar": case "jugar": return "alegria";
    case "discutir": return "enfado";
    case "proponer_pareja": return "corazon";
    case "explorar": case "marcharse": return "bolsa";
    default: return null;
  }
}
