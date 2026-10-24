<script setup>
// Ficha de un habitante: cabecera con quién es y subpestañas (Ahora, Su vida, Familia, Decisiones).
import { computed, ref, watch } from "vue";
import Cara from "./Cara.vue";
import Icono from "./Icono.vue";
import Subpestanas from "./Subpestanas.vue";
import VidaPersona from "./VidaPersona.vue";
import { api, ir, irPestana, ruta } from "../ruta.js";
import { QUIEN_DECIDE, accionEnTexto, caracterEnTexto, fechaDelTurno, horaDelTurno, mayuscula, LLEGADA } from "../textos.js";

const props = defineProps({ id: Number, turno: Number, siguiendo: Boolean });
const emit = defineEmits(["seleccionar", "cerrar", "seguir"]);

const ficha = ref(null);
const fase = ref("cargando");   // cargando, datos, ausente, error

async function cargar(conEsqueleto) {
  if (conEsqueleto) fase.value = "cargando";
  try {
    const r = await fetch(api(`/api/habitante/${props.id}`));
    if (r.status === 404) { fase.value = "ausente"; return; }
    if (!r.ok) throw new Error();
    ficha.value = await r.json();
    fase.value = "datos";
  } catch {
    if (fase.value !== "datos") fase.value = "error";
  }
}

watch(() => props.id, () => cargar(true), { immediate: true });
watch(() => props.turno, () => { if (fase.value === "datos") cargar(false); });

// Necesidades: en hambre, más es peor; en el resto, más es mejor.
const NECESIDADES = [
  { clave: "hambre", texto: "Hambre", malo: (v) => v },
  { clave: "energia", texto: "Energía", malo: (v) => 100 - v },
  { clave: "salud", texto: "Salud", malo: (v) => 100 - v },
  { clave: "animo", texto: "Ánimo", malo: (v) => 100 - v },
];
const nivel = (malo) => (malo >= 70 ? "peligro" : malo >= 45 ? "aviso" : "bien");

function abrir(persona) {
  if (persona.vivo) emit("seleccionar", persona.id);
  else ir("familias", persona.id);
}

const pareja = computed(() => ficha.value?.parejas.slice(-1).filter((p) => p.vivo) ?? []);
const pestana = computed(() => (["ahora", "vida", "familia", "decisiones"].includes(ruta.pestana) ? ruta.pestana : "ahora"));
const opciones = computed(() => [
  { id: "ahora", texto: "Ahora" },
  { id: "vida", texto: "Su vida" },
  { id: "familia", texto: "Familia", cuenta: ficha.value ? ficha.value.padres.length + ficha.value.hijos.length + pareja.value.length : null },
  { id: "decisiones", texto: "Decisiones", cuenta: ficha.value?.historial.length ?? null },
]);

const cuando = (turno) => {
  const f = fechaDelTurno(turno);
  return `${mayuscula(f.estacion)} ${f.dia}, ${horaDelTurno(turno)}`;
};
</script>

<template>
  <section class="ficha">
    <template v-if="fase === 'cargando'">
      <div class="cabecera"><div class="esqueleto" style="width: 64px; height: 64px"></div>
        <div style="flex: 1"><div class="esqueleto" style="height: 20px; width: 60%"></div>
          <div class="esqueleto" style="height: 14px; width: 80%; margin-top: 8px"></div></div></div>
      <div class="esqueleto" style="height: 40px"></div>
      <div class="esqueleto" style="height: 160px"></div>
    </template>

    <p v-else-if="fase === 'ausente'" class="vacia">
      Esta persona ya no vive en la aldea. Su historia sigue en el árbol de familias.
      <button type="button" class="enlace" @click="ir('familias', id)">Ver su familia</button>
    </p>

    <p v-else-if="fase === 'error'" class="vacia">
      No hemos podido cargar esta ficha. Lo volveremos a intentar en el próximo turno.
    </p>

    <template v-else>
      <div class="cabecera">
        <Cara :personaje="ficha.personaje" :nombre="ficha.nombre" :tamano="64" />
        <div class="identidad">
          <div class="chips">
            <span class="chip numero">{{ ficha.edad }} años</span>
            <span class="chip">{{ ficha.oficio ? mayuscula(ficha.oficio) : (ficha.sexo === "m" ? "Niña" : "Niño") }}</span>
            <span class="chip">{{ caracterEnTexto(ficha.caracter, ficha.sexo) }}</span>
          </div>
          <p class="suave">{{ LLEGADA[ficha.llegada](ficha.sexo) }} en el año {{ Math.max(1, ficha.llegada_ano) }}</p>
        </div>
      </div>
      <button type="button" class="boton" :class="{ on: siguiendo }" :aria-pressed="siguiendo" @click="emit('seguir')">
        <Icono nombre="seguir" :tamano="18" />{{ siguiendo ? "Dejar de seguir en el mapa" : "Seguir en el mapa" }}
      </button>

      <Subpestanas :opciones="opciones" :activa="pestana" etiqueta="Partes de la ficha" @elegir="irPestana" />

      <template v-if="pestana === 'ahora'">
        <div class="tarjeta ahora">
          <p class="accion">{{ accionEnTexto(ficha) }}</p>
          <p v-if="ficha.motivo" class="motivo">«{{ ficha.motivo }}»</p>
          <p class="suave">{{ QUIEN_DECIDE[ficha.decidido_por] }}<template v-if="ficha.confianza != null">
            · confianza {{ Math.round(ficha.confianza * 100) }} %</template></p>
        </div>

        <div v-if="ficha.necesidades" class="bloque">
          <h3>Cómo está</h3>
          <div v-for="n in NECESIDADES" :key="n.clave" class="necesidad">
            <span>{{ n.texto }}</span>
            <div class="medidor" role="meter" :aria-label="n.texto" aria-valuemin="0" aria-valuemax="100"
                 :aria-valuenow="ficha.necesidades[n.clave]">
              <div :class="nivel(n.malo(ficha.necesidades[n.clave]))" :style="{ width: ficha.necesidades[n.clave] + '%' }"></div>
            </div>
            <span class="numero valor">{{ ficha.necesidades[n.clave] }}</span>
          </div>
          <p v-if="ficha.enfermo" class="suave">Está {{ ficha.sexo === "m" ? "enferma" : "enfermo" }}.</p>
        </div>
      </template>

      <VidaPersona v-else-if="pestana === 'vida'" :vida="ficha.vida" />

      <template v-else-if="pestana === 'familia'">
        <div class="bloque">
          <h3>Familia</h3>
          <dl class="familia">
            <template v-for="[titulo, personas] in [['Pareja', pareja], ['Padres', ficha.padres], ['Hijos', ficha.hijos]]" :key="titulo">
              <dt>{{ titulo }}</dt>
              <dd>
                <span v-if="!personas.length" class="suave">Nadie</span>
                <button v-for="p in personas" :key="p.id" type="button" class="persona" @click="abrir(p)">
                  <Cara :personaje="p.personaje" :nombre="p.nombre" :vivo="p.vivo" :tamano="24" />{{ p.nombre }}
                </button>
              </dd>
            </template>
          </dl>
        </div>
        <div class="bloque">
          <h3>Amistades y rivales</h3>
          <p v-if="!ficha.amigos.length && !ficha.rivales.length" class="suave">Todavía no tiene amigos ni rivales.</p>
          <dl v-else class="familia">
            <template v-for="[titulo, personas] in [['Amigos', ficha.amigos], ['Rivales', ficha.rivales]]" :key="titulo">
              <template v-if="personas.length">
                <dt>{{ titulo }}</dt>
                <dd><button v-for="p in personas" :key="p.id" type="button" class="persona" @click="abrir(p)">
                  <Cara :personaje="p.personaje" :nombre="p.nombre" :tamano="24" />{{ p.nombre }}</button></dd>
              </template>
            </template>
          </dl>
        </div>
        <button type="button" class="enlace" @click="ir('familias', id)">Ver su rama en el árbol de familias</button>
      </template>

      <template v-else>
        <p v-if="!ficha.historial.length" class="suave">Todavía no ha tenido que decidir nada.</p>
        <ol v-else class="decisiones">
          <li v-for="d in ficha.historial" :key="d.turno">
            <span class="marca" aria-hidden="true"></span>
            <div>
              <p class="que">{{ d.descripcion }}</p>
              <p class="motivo-d">«{{ d.motivo }}»</p>
              <p class="suave numero"><time>{{ cuando(d.turno) }}</time> · {{ d.decidido_por === "jev" ? "Jev" : "reglas" }}<template
                v-if="d.confianza != null">, {{ Math.round(d.confianza * 100) }} %</template></p>
            </div>
          </li>
        </ol>
      </template>
    </template>
  </section>
</template>

<style scoped>
.ficha { display: flex; flex-direction: column; gap: var(--space-4); }
.ficha > * { flex-shrink: 0; }   /* la ficha se desplaza; sus partes no se aplastan */
.enlace {
  align-self: flex-start; border: none; background: none; padding: var(--space-1) 0; color: var(--color-text);
  font: inherit; font-size: var(--text-sm); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer;
}
.enlace:hover { color: var(--color-accent); }
.cabecera { display: flex; gap: var(--space-4); align-items: center; }
.identidad { display: flex; flex-direction: column; gap: var(--space-2); min-width: 0; }
.chips { display: flex; flex-wrap: wrap; gap: var(--space-1); }
.chip {
  padding: 2px var(--space-2); border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 500;
  background: var(--color-surface); border: 1px solid var(--color-border);
}
.suave { color: var(--color-text-muted); font-size: var(--text-sm); margin: 0; }
.boton {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  height: var(--control-height); border-radius: var(--radius-md);
  border: 1px solid var(--color-border-strong); background: var(--color-surface); color: var(--color-text);
  font: inherit; font-size: var(--text-sm); font-weight: 500; cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.boton:hover { background: var(--color-surface-muted); }
.boton:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
.boton.on { border-color: var(--color-accent); background: color-mix(in srgb, var(--color-accent) 16%, transparent); }
.bloque { display: flex; flex-direction: column; gap: var(--space-2); }
h3 { font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-text-muted); }
.ahora { display: flex; flex-direction: column; gap: var(--space-1); }
.ahora p { margin: 0; }
.ahora .accion { font-size: var(--text-lg); font-weight: 600; }
.necesidad { display: grid; grid-template-columns: 64px 1fr 28px; align-items: center; gap: var(--space-2); font-size: var(--text-sm); }
.valor { text-align: right; color: var(--color-text-muted); }
.medidor { height: 8px; border-radius: 4px; background: var(--color-surface-muted); overflow: hidden; }
.medidor > div { height: 100%; border-radius: 4px; transition: width var(--duration) var(--ease); }
.bien { background: var(--success); }
.aviso { background: var(--warning); }
.peligro { background: var(--danger); }
.familia { display: grid; grid-template-columns: 64px 1fr; gap: var(--space-2); margin: 0; font-size: var(--text-sm); }
.familia dt { color: var(--color-text-muted); padding-top: 4px; }
.familia dd { margin: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
.persona {
  display: inline-flex; align-items: center; gap: var(--space-2); padding: 2px var(--space-2) 2px 2px;
  border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface);
  color: var(--color-text); font: inherit; font-size: var(--text-sm); cursor: pointer;
}
.persona:hover { background: var(--color-surface-muted); }
.decisiones { list-style: none; margin: 0; padding: 0; }
.decisiones li { position: relative; display: grid; grid-template-columns: 16px 1fr; gap: var(--space-3); padding-bottom: var(--space-4); font-size: var(--text-sm); }
.decisiones li:not(:last-child)::before { content: ""; position: absolute; left: 7px; top: 18px; bottom: 0; width: 2px; background: var(--color-border); }
.decisiones .marca { width: 16px; height: 16px; margin-top: 2px; border-radius: 50%; border: 2px solid var(--color-border-strong); background: var(--panel-bg); }
.decisiones p { margin: 0; }
.que { font-weight: 600; }
.decisiones .motivo-d { margin: 2px 0; }
.vacia { margin: 0; font-size: var(--text-sm); color: var(--color-text-muted); display: flex; flex-direction: column; gap: var(--space-2); align-items: flex-start; }
</style>
