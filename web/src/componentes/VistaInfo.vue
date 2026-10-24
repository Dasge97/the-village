<script setup>
// Sección "Qué es La aldea": explica el experimento. Arriba, una presentación con la situación
// de ahora mismo; debajo, tarjetas con cada parte: qué hay escrito, quién decide y cómo mirarlo.
import Cara from "./Cara.vue";
import Icono from "./Icono.vue";
import { ir } from "../ruta.js";
import { mayuscula } from "../textos.js";

defineProps({ aldea: Object });

const CARAS = ["Villager", "Woman", "Monk", "OldWoman", "Child", "Samurai", "Princess", "Hunter"];

const REGLAS = [
  "Cada habitante tiene hambre, energía, salud y ánimo, y envejece.",
  "Trabajar da comida, madera o piedra según el oficio. Los árboles vuelven a crecer y el río se repone.",
  "Hay estaciones: en invierno no hay cosecha y las casas gastan leña.",
  "De noche se duerme y a veces llegan monstruos del bosque.",
  "Pasan cosas al azar: sequías, incendios, enfermedades o un forastero que llega.",
  "Límites para que el mundo no se rompa: como mucho 20 habitantes, y solo nace alguien si hay casa y comida.",
];

const ACCIONES = ["Trabajar", "Cambiar de oficio", "Construir", "Descansar", "Comer", "Hablar", "Ayudar", "Discutir",
  "Coger comida a escondidas", "Proponer pareja", "Explorar", "Marcharse"];

const TIEMPO = [
  ["10 segundos", "1 turno del mundo (4 minutos)"],
  ["1 hora", "1 día con su noche"],
  ["6 horas", "1 estación"],
  ["1 día", "1 año entero"],
  ["16 días", "lo que tarda un niño en ser adulto"],
  ["unos 2 meses", "una vida completa"],
];
</script>

<template>
  <div class="info">
    <header class="portada">
      <div class="texto-portada">
        <p class="antetitulo">Un experimento que no se detiene</p>
        <h3 class="lema">Un mundo simulado en el que no hay nada escrito</h3>
        <p class="presentacion">
          La aldea es mi mundo simulado. Avanza día y noche, lo mire alguien o no. Solo hay unas reglas
          básicas; todo lo demás lo decide un modelo de inteligencia artificial según lo que va pasando.
          Nadie sabe qué ocurrirá mañana, ni siquiera yo.
        </p>
        <div class="caras" aria-hidden="true">
          <Cara v-for="c in CARAS" :key="c" :personaje="c" :nombre="c" :tamano="40" />
        </div>
      </div>
      <dl class="ahora">
        <div><dt>Ahora mismo</dt><dd>Año {{ aldea.ano }} · {{ mayuscula(aldea.estacion) }}</dd></div>
        <div><dt>Viven en la aldea</dt><dd class="numero">{{ aldea.poblacion }} habitantes</dd></div>
        <div><dt>Casas levantadas</dt><dd class="numero">{{ aldea.casas.length }}</dd></div>
        <div><dt>Muralla</dt><dd class="numero">{{ aldea.muralla }} de 20 tramos</dd></div>
      </dl>
    </header>

    <div class="tarjetas">
      <section class="tarjeta bloque destacado">
        <span class="icono" aria-hidden="true"><Icono nombre="chispa" /></span>
        <h3>Nada está escrito</h3>
        <p>
          No hay guion, ni misiones, ni finales preparados. Nadie ha decidido quién se enamora, quién
          tiene hijos, quién se marcha o si la aldea sobrevive al invierno. Cada historia de la
          crónica ha salido sola, de las decisiones de sus habitantes.
        </p>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="regla" /></span>
        <h3>Las reglas básicas</h3>
        <p>Las reglas solo dicen cómo funciona el mundo, no lo que tiene que pasar:</p>
        <ul class="lista">
          <li v-for="r in REGLAS" :key="r">{{ r }}</li>
        </ul>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="personas" /></span>
        <h3>Quién decide: Jev</h3>
        <p>
          Jev es el modelo que decide por cada adulto despierto, más o menos cada 5 minutos. Ve lo
          mismo que vería el habitante: cómo está, su oficio, su edad, con quién se lleva bien o mal,
          lo que queda en el almacén, la estación, la hora y lo último que ha pasado.
        </p>
        <p>Con eso elige una de estas acciones:</p>
        <ul class="chips">
          <li v-for="a in ACCIONES" :key="a">{{ a }}</li>
        </ul>
        <p class="suave">Cada decisión dura un rato y en la ficha de cada habitante verás qué eligió, por qué y con cuánta seguridad.</p>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="dado" /></span>
        <h3>Cuando algo es urgente</h3>
        <p>
          Si alguien está a punto de desfallecer de hambre o de cansancio, las reglas lo mandan a comer
          o a descansar sin esperar a Jev. Y si Jev no responde, decide un sistema de reglas sencillo
          por ese habitante. El mundo nunca se para.
        </p>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="casa" /></span>
        <h3>Una segunda aldea</h3>
        <p>
          Cuando la aldea llega a 20 habitantes ya no cabe nadie más. Entonces los jóvenes sin pareja
          pueden decidir marcharse. El primero que se va funda la Aldea del río, y los que se marchen
          después se van a vivir con él.
        </p>
        <p>
          Desde ese momento hay dos aldeas que viven a la vez, cada una con sus casas, sus familias y
          su historia. Para mirar la otra, pulsa el nombre de arriba a la izquierda.
        </p>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="reloj" /></span>
        <h3>El tiempo</h3>
        <table class="tiempo">
          <thead><tr><th scope="col">Tiempo real</th><th scope="col">En la aldea</th></tr></thead>
          <tbody>
            <tr v-for="[real, mundo] in TIEMPO" :key="real"><th scope="row">{{ real }}</th><td>{{ mundo }}</td></tr>
          </tbody>
        </table>
      </section>

      <section class="tarjeta bloque">
        <span class="icono" aria-hidden="true"><Icono nombre="ojo" /></span>
        <h3>Qué puedes hacer tú</h3>
        <p>Solo mirar. Nadie puede intervenir, tampoco yo. Pero hay mucho que ver:</p>
        <div class="accesos">
          <button type="button" class="acceso" @click="ir('habitantes')"><Icono nombre="personas" :tamano="18" />Conocer a sus habitantes</button>
          <button type="button" class="acceso" @click="ir('historia')"><Icono nombre="libro" :tamano="18" />Leer lo que ha pasado</button>
          <button type="button" class="acceso" @click="ir('familias')"><Icono nombre="familia" :tamano="18" />Ver el árbol de familias</button>
          <button type="button" class="acceso" @click="ir('historia', null, null, true)"><Icono nombre="historial" :tamano="18" />Ver la historia año a año</button>
        </div>
      </section>
    </div>

    <footer class="creditos">
      Gráficos: <strong>Ninja Adventure</strong>, de Pixel-boy y AAA (licencia CC0). Decisiones: Jev, a través de OpenRouter.
    </footer>
  </div>
</template>

<style scoped>
.info { display: flex; flex-direction: column; gap: var(--space-6); }

.portada {
  display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: var(--space-6); align-items: center;
  padding: var(--space-6); border-radius: var(--radius-lg);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 14%, var(--color-surface)), var(--color-surface));
  border: 1px solid var(--color-border);
}
.texto-portada { display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; }
.antetitulo { margin: 0; font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--color-accent); }
.lema { font-family: var(--font-pixel); font-size: var(--text-2xl); line-height: 1.2; }
.presentacion { margin: 0; font-size: var(--text-md); max-width: 680px; }
.caras { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-1); }
.ahora { display: grid; gap: var(--space-3); margin: 0; padding: var(--space-4); border-radius: var(--radius-md); background: var(--color-surface); border: 1px solid var(--color-border); }
.ahora dt { font-size: var(--text-xs); color: var(--color-text-muted); }
.ahora dd { margin: 0; font-weight: 600; }

.tarjetas { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-4); }
.bloque { display: flex; flex-direction: column; gap: var(--space-3); padding: var(--space-6); }
.bloque p { margin: 0; font-size: var(--text-sm); line-height: 1.6; }
.bloque h3 { font-size: var(--text-lg); }
.icono {
  display: grid; place-items: center; width: 40px; height: 40px; border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--color-accent) 16%, transparent); color: var(--color-accent);
}
.destacado { border-color: color-mix(in srgb, var(--color-accent) 50%, transparent); }
.lista { margin: 0; padding-left: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); font-size: var(--text-sm); line-height: 1.5; }
.chips { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-1); }
.chips li { padding: 2px var(--space-2); border-radius: var(--radius-sm); font-size: var(--text-xs); font-weight: 500; background: var(--color-surface-muted); }
.suave { color: var(--color-text-muted); }
.tiempo { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.tiempo th, .tiempo td { padding: var(--space-2) 0; text-align: left; border-bottom: 1px solid var(--color-border); }
.tiempo thead th { font-size: var(--text-xs); font-weight: 600; color: var(--color-text-muted); }
.tiempo tbody th { font-weight: 600; white-space: nowrap; padding-right: var(--space-4); }
.accesos { display: flex; flex-direction: column; gap: var(--space-2); }
.acceso {
  display: flex; align-items: center; gap: var(--space-2); height: var(--control-height); padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong); border-radius: var(--radius-md); background: var(--color-surface);
  color: var(--color-text); font: inherit; font-size: var(--text-sm); font-weight: 500; text-align: left; cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.acceso:hover { background: var(--color-surface-muted); }
.acceso:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
.creditos { font-size: var(--text-xs); color: var(--color-text-muted); padding-bottom: var(--space-2); }

@media (max-width: 960px) {
  .portada { grid-template-columns: 1fr; padding: var(--space-4); }
  .lema { font-size: var(--text-xl); }
  .bloque { padding: var(--space-4); }
  .tarjetas { grid-template-columns: 1fr; }
}
</style>
