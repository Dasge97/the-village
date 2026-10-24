// Conexión por websocket con el servidor. Se reconecta sola si se corta, y se rehace contra la
// otra aldea cuando se cambia de aldea en el selector.

import { reactive, watch } from "vue";
import { ruta } from "./ruta.js";

export function conectar() {
  const estado = reactive({ fase: "conectando", mapa: null, aldea: null, intentos: 0, numero: ruta.aldea });
  let ws;
  let espera = 1000;

  function abrir() {
    const protocolo = location.protocol === "https:" ? "wss" : "ws";
    const n = ruta.aldea;
    ws = new WebSocket(`${protocolo}://${location.host}/ws?aldea=${n}`);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.tipo === "inicio") { estado.mapa = msg.mapa; estado.numero = msg.aldea; }
      estado.aldea = msg.estado;
      estado.fase = "conectado";
      estado.intentos = 0;
      espera = 1000;
    };
    ws.onclose = (e) => {
      if (e.code === 4000) return;            // cerrada a propósito al cambiar de aldea
      estado.intentos += 1;
      estado.fase = estado.intentos >= 3 ? "error" : "conectando";
      setTimeout(abrir, espera);
      espera = Math.min(espera * 2, 15000);
    };
  }

  // Al cambiar de aldea se borra lo de la anterior (el mapa se vuelve a dibujar) y se conecta a la nueva.
  watch(() => ruta.aldea, () => {
    ws.close(4000);
    estado.mapa = null;
    estado.aldea = null;
    estado.fase = "conectando";
    abrir();
  });

  abrir();
  return estado;
}
