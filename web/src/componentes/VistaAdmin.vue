<script setup>
// Panel de administración, con contraseña. Subpestañas: Tiempo (velocidad y pausa), Gasto (lo que
// cuesta Jev, su límite al día y si decide) y Servidor (guardado, conexiones y bases de datos).
// Mientras está abierto se pone al día cada 5 segundos.
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Cifra from "./Cifra.vue";
import Subpestanas from "./Subpestanas.vue";
import { irPestana, ruta } from "../ruta.js";
import { mayuscula } from "../textos.js";

const fase = ref("cargando");     // cargando | cerrado | fuera | dentro | error
const datos = ref(null);
const clave = ref("");
const error = ref("");
const enviando = ref(false);
const limite = ref("");
const aviso = ref("");

async function pedir(camino, cuerpo) {
  const r = await fetch(`/api/admin/${camino}`, cuerpo === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(json.detail ?? "No hemos podido hablar con el servidor."), { estado: r.status });
  return json;
}

async function cargar() {
  try {
    datos.value = await pedir("estado");
    if (fase.value !== "dentro") limite.value = datos.value.ajustes.usd_dia.toFixed(2);
    fase.value = "dentro";
  } catch (e) {
    if (e.estado === 401) fase.value = "fuera";
    else if (fase.value !== "dentro") fase.value = "error";
  }
}

async function empezar() {
  try {
    const s = await pedir("sesion");
    if (!s.configurado) fase.value = "cerrado";
    else if (s.dentro) await cargar();
    else fase.value = "fuera";
  } catch {
    fase.value = "error";
  }
}

async function entrar() {
  if (!clave.value) { error.value = "Escribe la contraseña."; return; }
  enviando.value = true;
  error.value = "";
  try {
    await pedir("entrar", { clave: clave.value });
    clave.value = "";
    await cargar();
  } catch (e) {
    error.value = e.message;
  } finally {
    enviando.value = false;
  }
}

async function salir() {
  await pedir("salir", {}).catch(() => {});
  datos.value = null;
  fase.value = "fuera";
}

// Cambia un ajuste y enseña un aviso corto con lo que ha pasado.
async function ajustar(cambio, texto) {
  enviando.value = true;
  try {
    datos.value = await pedir("ajustes", cambio);
    aviso.value = texto;
    setTimeout(() => { if (aviso.value === texto) aviso.value = ""; }, 4000);
  } catch (e) {
    if (e.estado === 401) fase.value = "fuera";
    aviso.value = e.message;
  } finally {
    enviando.value = false;
  }
}

const errorLimite = computed(() => {
  const n = Number(String(limite.value).replace(",", "."));
  if (Number.isNaN(n) || n < 0) return "Escribe una cantidad en dólares, por ejemplo 0,30.";
  if (datos.value && n > datos.value.usd_dia_maximo) return `Como mucho ${dinero(datos.value.usd_dia_maximo)} al día.`;
  return "";
});
function guardarLimite() {
  if (errorLimite.value) return;
  const n = Number(String(limite.value).replace(",", "."));
  ajustar({ usd_dia: n }, `Límite guardado: ${dinero(n)} al día.`);
}

async function guardarAhora() {
  enviando.value = true;
  try {
    datos.value = await pedir("guardar", {});
    aviso.value = "Mundo guardado.";
  } catch (e) {
    aviso.value = e.message;
  } finally {
    enviando.value = false;
  }
}

let reloj;
onMounted(() => { empezar(); reloj = setInterval(() => { if (fase.value === "dentro") cargar(); }, 5000); });
onBeforeUnmount(() => clearInterval(reloj));

const PESTANAS = { tiempo: "Tiempo", gasto: "Gasto", servidor: "Servidor" };
const pestana = computed(() => (PESTANAS[ruta.pestana] ? ruta.pestana : "tiempo"));
const opciones = Object.entries(PESTANAS).map(([id, texto]) => ({ id, texto }));

const numero = (n) => n.toLocaleString("es-ES");
const dinero = (n) => `${n.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: n < 1 ? 4 : 2 })} USD`;
function hace(s) {
  if (s == null) return "todavía no";
  if (s < 60) return `hace ${s} s`;
  if (s < 3600) return `hace ${Math.round(s / 60)} min`;
  if (s < 86400) return `hace ${Math.round(s / 3600)} h`;
  return `hace ${Math.round(s / 86400)} días`;
}
function duracion(minutos) {
  if (minutos < 1) return `${Math.round(minutos * 60)} segundos`;
  if (minutos < 120) return `${numero(Math.round(minutos * 10) / 10)} minutos`;
  return `${numero(Math.round(minutos / 6) / 10)} horas`;
}
const hora = (h) => `${String(Math.floor(h)).padStart(2, "0")}:${String(Math.floor((h % 1) * 60)).padStart(2, "0")}`;

const t = computed(() => datos.value?.tiempo);
const turnos = (n) => `${numero(n)} ${n === 1 ? "turno" : "turnos"}`;
// Si el ordenador no llega a la velocidad pedida (menos del 90 %), se avisa.
const noLlega = computed(() => t.value && t.value.pedidos_por_segundo && t.value.turnos_por_segundo > 0
  && t.value.turnos_por_segundo < t.value.pedidos_por_segundo * 0.9);
const llamadasDia = computed(() => {
  const n = Number(String(limite.value).replace(",", "."));
  return Number.isNaN(n) || !datos.value ? 0 : Math.round(n / datos.value.jev.coste_llamada);
});
const QUIEN = { jev: "Jev", reglas: "Reglas (lo urgente)", presupuesto: "Reglas (sin presupuesto)", respaldo: "Reglas (Jev falló)" };
const decisiones = computed(() => {
  const d = datos.value?.jev.decisiones ?? {};
  const total = Object.values(d).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(d).sort((a, b) => b[1] - a[1]).map(([k, n]) => ({ k, texto: QUIEN[k] ?? mayuscula(k), n, parte: Math.round((n / total) * 100) }));
});
const BOLSAS = { vecinos: "Vecinos de las aldeas", consejos: "Consejos de pueblos, villas y ciudades" };
const maxGasto = computed(() => Math.max(0.0001, ...(datos.value?.gasto ?? []).map((g) => g.coste)));
const fechaCorta = (d) => d.split("-").reverse().slice(0, 2).join("/");
</script>

<template>
  <div class="admin">
    <div v-if="fase === 'cargando'" class="esqueleto" style="height: 160px"></div>

    <p v-else-if="fase === 'error'" class="vacia">No hemos podido hablar con el servidor. Comprueba la conexión y vuelve a abrir este panel.</p>

    <p v-else-if="fase === 'cerrado'" class="vacia">El panel está cerrado: el servidor no tiene contraseña de administración.
      Se configura con <code>ALDEA_ADMIN_CLAVE</code> en sus secretos.</p>

    <form v-else-if="fase === 'fuera'" class="entrar" @submit.prevent="entrar">
      <p class="intro">Entra para acelerar o pausar el mundo, ver cuánto gasta Jev y ponerle un límite.</p>
      <div class="campo">
        <label for="clave-admin">Contraseña</label>
        <input id="clave-admin" v-model="clave" type="password" autocomplete="current-password"
               :aria-invalid="!!error" aria-describedby="error-clave" />
        <span v-if="error" id="error-clave" class="error-campo" role="alert">{{ error }}</span>
      </div>
      <button class="boton" type="submit" :disabled="enviando">{{ enviando ? "Entrando…" : "Entrar" }}</button>
    </form>

    <template v-else-if="datos">
      <div class="cabecera">
        <p class="intro">Desde aquí manejas cómo va el mundo. Lo que cambies se guarda con la partida.</p>
        <button class="boton texto" type="button" @click="salir">Salir</button>
      </div>
      <Subpestanas :opciones="opciones" :activa="pestana" etiqueta="Partes del panel de administración" @elegir="irPestana" />
      <p v-if="aviso" class="aviso" role="status">{{ aviso }}</p>

      <!-- Tiempo -->
      <section v-if="pestana === 'tiempo'" class="seccion">
        <div class="cifras">
          <Cifra etiqueta="Fecha del mundo" :valor="`Año ${t.ano}`" compacta>
            <span class="pie">{{ mayuscula(t.estacion) }} · Día {{ t.dia }} · {{ hora(t.hora) }}</span>
          </Cifra>
          <Cifra etiqueta="Un día del mundo dura" :valor="duracion(t.minutos_por_dia)" compacta />
          <Cifra etiqueta="Un año del mundo dura" :valor="duracion(t.horas_por_ano * 60)" compacta />
        </div>

        <h3>Velocidad</h3>
        <div class="velocidades" role="radiogroup" aria-label="Velocidad del mundo">
          <button v-for="v in datos.velocidades" :key="v" type="button" role="radio" class="velocidad numero"
                  :class="{ on: datos.ajustes.velocidad === v }" :aria-checked="datos.ajustes.velocidad === v" :disabled="enviando"
                  @click="ajustar({ velocidad: v }, v === 1 ? 'El mundo vuelve a su velocidad normal.' : `El mundo va ahora ${v} veces más rápido.`)">×{{ v }}</button>
        </div>
        <p class="ayuda">Acelerar no gasta más en Jev: su límite es por día real. Con el mundo rápido, más decisiones las toman las reglas.</p>
        <p class="ayuda numero" :class="{ alerta: noLlega }">
          <template v-if="datos.ajustes.pausado">El mundo está en pausa.</template>
          <template v-else>Ahora calcula {{ turnos(t.turnos_por_segundo) }} por segundo; se han pedido {{ numero(t.pedidos_por_segundo) }}.
            Cada turno tarda {{ numero(t.ms_por_turno) }} ms.<template v-if="noLlega"> El servidor no llega a esta velocidad.</template></template>
        </p>

        <h3>Pausa</h3>
        <p class="ayuda">En pausa, nadie envejece ni se mueve y la web se queda quieta hasta que lo reanudes.</p>
        <div>
          <button class="boton" :class="{ secundario: !datos.ajustes.pausado }" type="button" :disabled="enviando"
                  @click="ajustar({ pausado: !datos.ajustes.pausado }, datos.ajustes.pausado ? 'El mundo sigue.' : 'El mundo está en pausa.')">
            {{ datos.ajustes.pausado ? "Reanudar el mundo" : "Pausar el mundo" }}</button>
        </div>
      </section>

      <!-- Gasto -->
      <section v-else-if="pestana === 'gasto'" class="seccion">
        <div class="cifras">
          <Cifra etiqueta="Gastado hoy" :valor="dinero(datos.jev.hoy.coste)" compacta>
            <span class="pie numero">{{ numero(datos.jev.hoy.llamadas) }} llamadas</span>
          </Cifra>
          <Cifra etiqueta="Límite al día" :valor="dinero(datos.ajustes.usd_dia)" compacta>
            <span class="pie numero">{{ datos.jev.hoy.coste > 0 ? Math.round((datos.jev.hoy.coste / Math.max(datos.ajustes.usd_dia, 0.0001)) * 100) : 0 }} % usado hoy</span>
          </Cifra>
          <Cifra etiqueta="Desde el principio" :valor="dinero(datos.jev.coste_total)" compacta>
            <span class="pie numero">{{ numero(datos.jev.llamadas) }} llamadas · {{ numero(datos.jev.errores) }} errores</span>
          </Cifra>
        </div>

        <h3>Jev</h3>
        <p class="ayuda">{{ !datos.jev.conectado ? "Este servidor arrancó sin Jev: decide todo las reglas."
          : datos.ajustes.jev ? "Jev decide mientras quede presupuesto. Si lo apagas, decide todo las reglas y no se gasta nada."
          : "Jev está apagado: decide todo las reglas y no se gasta nada." }}</p>
        <div v-if="datos.jev.conectado">
          <button class="boton" :class="{ secundario: datos.ajustes.jev }" type="button" :disabled="enviando"
                  @click="ajustar({ jev: !datos.ajustes.jev }, datos.ajustes.jev ? 'Jev apagado. Deciden las reglas.' : 'Jev vuelve a decidir.')">
            {{ datos.ajustes.jev ? "Apagar Jev" : "Encender Jev" }}</button>
        </div>

        <h3>Límite de gasto al día</h3>
        <form class="limite" @submit.prevent="guardarLimite">
          <div class="campo">
            <label for="limite-admin">Dólares al día como máximo</label>
            <input id="limite-admin" v-model="limite" inputmode="decimal" :aria-invalid="!!errorLimite" aria-describedby="ayuda-limite" />
            <span v-if="errorLimite" class="error-campo">{{ errorLimite }}</span>
            <span v-else id="ayuda-limite" class="ayuda-campo numero">Unas {{ numero(llamadasDia) }} llamadas al día: el 60 % para los vecinos y el 40 % para los consejos.</span>
          </div>
          <button class="boton" type="submit" :disabled="enviando || !!errorLimite">Guardar límite</button>
        </form>

        <h3>Presupuesto ahora</h3>
        <table class="tabla numero">
          <thead><tr><th>Para</th><th>Al día</th><th>Quedan ahora</th><th>Usadas</th><th>Sin presupuesto</th></tr></thead>
          <tbody>
            <tr v-for="(b, k) in datos.presupuesto" :key="k">
              <td>{{ BOLSAS[k] ?? k }}</td><td>{{ numero(b.por_dia) }}</td><td>{{ numero(Math.floor(b.quedan_ahora)) }}</td>
              <td>{{ numero(b.gastadas) }}</td><td>{{ numero(b.sin_presupuesto) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="ayuda">Desde que arrancó el servidor. «Sin presupuesto» son las veces que decidieron las reglas porque no quedaban llamadas.</p>

        <h3>Quién decide en las aldeas</h3>
        <ul class="barras">
          <li v-for="d in decisiones" :key="d.k">
            <span class="etiqueta-barra">{{ d.texto }}</span>
            <span class="pista"><span class="relleno" :style="{ width: d.parte + '%' }"></span></span>
            <span class="valor-barra numero">{{ d.parte }} %</span>
          </li>
        </ul>

        <h3>Gasto por día</h3>
        <p v-if="!datos.gasto.length" class="vacia">Todavía no hay ningún día con gasto. Aparecerá aquí en cuanto Jev decida algo.</p>
        <ul v-else class="barras">
          <li v-for="g in [...datos.gasto].reverse()" :key="g.dia">
            <span class="etiqueta-barra numero">{{ fechaCorta(g.dia) }}</span>
            <span class="pista"><span class="relleno" :style="{ width: (g.coste / maxGasto) * 100 + '%' }"></span></span>
            <span class="valor-barra numero">{{ dinero(g.coste) }}</span>
          </li>
        </ul>
      </section>

      <!-- Servidor -->
      <section v-else class="seccion">
        <div class="cifras">
          <Cifra etiqueta="Encendido" :valor="hace(datos.servidor.arrancado_hace).replace('hace ', '')" compacta>
            <span class="pie">desde el último reinicio</span>
          </Cifra>
          <Cifra etiqueta="Último guardado" :valor="hace(datos.servidor.guardado_hace)" compacta />
          <Cifra etiqueta="Mirando ahora" :valor="numero(datos.servidor.conectados)" compacta>
            <span class="pie">webs abiertas</span>
          </Cifra>
          <Cifra etiqueta="Asentamientos" :valor="numero(datos.servidor.asentamientos)" compacta>
            <span class="pie numero">{{ numero(datos.servidor.aldeas) }} aldeas · {{ numero(datos.servidor.grandes) }} más grandes</span>
          </Cifra>
          <Cifra etiqueta="Personas" :valor="numero(datos.servidor.poblacion)" compacta />
          <Cifra etiqueta="Bases de datos" :valor="`${numero(Math.round(datos.servidor.bases_kb / 102.4) / 10)} MB`" compacta>
            <span class="pie numero">{{ numero(datos.servidor.bases) }} ficheros</span>
          </Cifra>
        </div>
        <p class="ayuda numero" :class="{ alerta: datos.jev.fallos_seguidos > 0 }">
          {{ datos.jev.fallos_seguidos > 0 ? `Jev ha fallado ${datos.jev.fallos_seguidos} veces seguidas; mientras, deciden las reglas.` : "Jev responde con normalidad." }}</p>
        <p class="ayuda">El mundo se guarda solo cada 5 minutos (cada minuto como mucho si va acelerado) y al apagar el servidor.</p>
        <div><button class="boton secundario" type="button" :disabled="enviando" @click="guardarAhora">Guardar ahora</button></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.admin { display: flex; flex-direction: column; gap: var(--space-4); }
.intro { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.entrar { display: flex; flex-direction: column; gap: var(--space-4); max-width: 400px; }
.entrar .boton { align-self: flex-start; }
.cabecera { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.seccion { display: flex; flex-direction: column; gap: var(--space-3); }
.cifras { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--space-2); }
.pie { font-size: var(--text-xs); color: var(--color-text-muted); }
h3 { margin: var(--space-3) 0 0; font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.ayuda { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); max-width: 72ch; }
.ayuda.alerta { color: var(--color-text); padding-left: var(--space-3); border-left: 3px solid var(--warning); }
.aviso { margin: 0; padding: var(--space-2) var(--space-3); border-left: 3px solid var(--success); background: var(--color-surface); border-radius: var(--radius-sm); font-size: var(--text-sm); }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); }
.velocidades { display: flex; flex-wrap: wrap; border-bottom: 1px solid var(--color-border); }
.velocidad {
  min-width: 48px; height: 44px; padding: 0 var(--space-2); border: none; background: transparent;
  color: var(--color-text-muted); font: inherit; font-weight: 500; cursor: pointer;
}
.velocidad:hover { color: var(--color-text); }
.velocidad.on { color: var(--color-text); font-weight: 600; background: var(--active-line) bottom / 100% 2px no-repeat; }
.velocidad:focus-visible { outline: 2px solid var(--color-focus); outline-offset: -2px; }
.limite { display: flex; flex-wrap: wrap; align-items: flex-start; gap: var(--space-3); }
.limite .campo { flex: 1 1 260px; max-width: 400px; }
.limite .boton { margin-top: 26px; }
.tabla { width: 100%; border-collapse: collapse; font-size: var(--text-sm); display: block; overflow-x: auto; }
.tabla th, .tabla td { padding: var(--space-2); border-bottom: 1px solid var(--color-border); text-align: right; white-space: nowrap; }
.tabla th:first-child, .tabla td:first-child { text-align: left; white-space: normal; }
.tabla th { font-weight: 600; font-size: var(--text-xs); color: var(--color-text-muted); }
.barras { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2); }
.barras li { display: grid; grid-template-columns: minmax(80px, 200px) 1fr 96px; align-items: center; gap: var(--space-3); font-size: var(--text-sm); }
.pista { height: 8px; border-radius: 4px; background: var(--color-surface-muted); overflow: hidden; }
.relleno { display: block; height: 100%; border-radius: 4px; background: var(--color-primary); }
.valor-barra { text-align: right; color: var(--color-text-muted); }
code { font-size: var(--text-xs); }
@media (max-width: 600px) {
  .limite .boton { margin-top: 0; }
  .barras li { grid-template-columns: 72px 1fr 80px; }
}
</style>
