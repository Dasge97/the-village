// Textos para enseñar los datos del motor en palabras normales.

export const caraUrl = (personaje) => `/sprites/Actor/Character/${personaje}/Faceset.png`;

export const mayuscula = (t) => (t ? t[0].toUpperCase() + t.slice(1) : "");

// Qué está haciendo un habitante ahora, en una frase corta.
export function accionEnTexto(h) {
  const a = h.sexo === "m" ? "a" : "o";
  switch (h.accion) {
    case "trabajar": return h.oficio === "guardia" ? "Vigilando la muralla" : `Trabajando de ${h.oficio}`;
    case "construir": return "Construyendo";
    case "dormir": return "Durmiendo";
    case "descansar": return "Descansando en casa";
    case "comer": return "Comiendo";
    case "quitar": return "Cogiendo comida a escondidas";
    case "jugar": return "Jugando";
    case "hablar": return h.con ? `Hablando con ${h.con}` : "Charlando";
    case "ayudar": return h.con ? `Ayudando a ${h.con}` : "Echando una mano";
    case "discutir": return h.con ? `Discutiendo con ${h.con}` : "Discutiendo";
    case "proponer_pareja": return h.con ? `Declarándose a ${h.con}` : "Declarándose";
    case "explorar": return h.fuera ? "Fuera, explorando" : "Saliendo a explorar";
    case "marcharse": return "Marchándose de la aldea";
    default: return h.accion;
  }
}

export const CARACTER = {
  trabajador: "Trabajador", perezoso: "Perezoso", sociable: "Sociable",
  solitario: "Solitario", valiente: "Valiente", prudente: "Prudente",
};

export function caracterEnTexto(caracter, sexo) {
  const t = CARACTER[caracter] || caracter;
  return sexo === "m" ? t.replace(/o$/, "a").replace("Trabajador", "Trabajadora") : t;
}

export const QUIEN_DECIDE = {
  jev: "Lo decidió Jev",
  reglas: "Lo decidieron las reglas",
  respaldo: "Jev no respondió y decidieron las reglas",
  urgencia: "Era urgente: lo decidieron las reglas",
  presupuesto: "Jev estaba ocupado; decidieron las reglas",
};

export const CAUSA = {
  vejez: "murió de vejez", hambre: "murió de hambre", enfermedad: "murió por una enfermedad",
  agotamiento: "murió de agotamiento", monstruos: "murió en un ataque de monstruos",
  marcha: "se marchó de la aldea",
};

export const LLEGADA = {
  fundador: (s) => (s === "m" ? "Fundadora de la aldea" : "Fundador de la aldea"),
  nacimiento: (s) => (s === "m" ? "Nacida en la aldea" : "Nacido en la aldea"),
  forastero: (s) => (s === "m" ? "Llegó de fuera" : "Llegó de fuera"),
  colono: () => "Llegó desde otra aldea",
  cargo: () => "Ocupa un cargo",
};

const TURNOS_POR_DIA = 360;
const TURNOS_POR_HORA = 15;
const DIAS_POR_ANO = 24;
const ESTACIONES = ["primavera", "verano", "otoño", "invierno"];

export function horaDelTurno(turno) {
  const minutos = Math.round(((turno % TURNOS_POR_DIA) / TURNOS_POR_HORA) * 60);
  return `${String(Math.floor(minutos / 60) % 24).padStart(2, "0")}:${String(minutos % 60).padStart(2, "0")}`;
}

export function fechaDelTurno(turno) {
  const dia = Math.floor(turno / TURNOS_POR_DIA);
  const delAno = dia % DIAS_POR_ANO;
  return { ano: Math.floor(dia / DIAS_POR_ANO) + 1, estacion: ESTACIONES[Math.floor(delAno / 6)], dia: delAno + 1 };
}

export const anoDelTurno = (turno) => Math.floor(turno / (TURNOS_POR_DIA * DIAS_POR_ANO)) + 1;

// Grupos de sucesos de la crónica, con su icono. Cada tipo del motor va a un grupo.
export const GRUPOS_SUCESO = [
  { id: "vida", texto: "Vida", icono: "corazon", tipos: ["nacimiento", "muerte", "pareja", "rechazo", "forastero", "colono", "marcha"] },
  { id: "obras", texto: "Obras", icono: "casa", tipos: ["casa", "muralla", "oficio"] },
  { id: "peligros", texto: "Peligros", icono: "alerta", tipos: ["ataque", "incendio", "robo", "enfermedad", "sequia", "frio", "discusion"] },
  { id: "fuera", texto: "Fuera", icono: "brujula", tipos: ["explora", "hallazgo"] },
];
export const grupoDeSuceso = (tipo) => GRUPOS_SUCESO.find((g) => g.tipos.includes(tipo)) ?? { id: "otros", icono: "sol" };

// Sucesos de casi todos los días que no aportan nada a la crónica.
export const SUCESOS_RUTINA = new Set(["pesca"]);

// Cuánto hace que pasó algo, en horas y días del mundo.
export function haceCuanto(turno, ahora) {
  const horas = Math.floor((ahora - turno) / TURNOS_POR_HORA);
  if (horas < 1) return "Ahora mismo";
  if (horas < 24) return `Hace ${horas} h`;
  const dias = Math.floor(horas / 24);
  return dias === 1 ? "Ayer" : `Hace ${dias} días`;
}

export function tituloDelDia(turno) {
  const f = fechaDelTurno(turno);
  return `${mayuscula(f.estacion)}, día ${f.dia} del año ${f.ano}`;
}

export const diaDelTurno = (turno) => Math.floor(turno / TURNOS_POR_DIA);
