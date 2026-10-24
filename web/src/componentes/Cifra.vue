<script setup>
// Tarjeta con una cifra: etiqueta arriba, valor grande y, si hace falta, algo más debajo (slot).
// `compacta`, para ponerlas en fila dentro de un panel estrecho.
defineProps({ etiqueta: String, valor: [String, Number], icono: String, compacta: Boolean });
</script>

<template>
  <div class="cifra" :class="{ compacta }">
    <span class="etiqueta"><img v-if="icono" class="icono-pixel" :src="icono" alt="" />{{ etiqueta }}</span>
    <strong class="valor numero">{{ valor }}</strong>
    <slot />
  </div>
</template>

<style scoped>
.cifra {
  display: flex; flex-direction: column; gap: var(--space-1); min-width: 0;
  padding: var(--space-3) var(--space-4); background: var(--color-surface);
  border: 1px solid var(--color-border); border-radius: var(--radius-lg);
}
.etiqueta { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted); }
.valor { font-size: var(--text-xl); font-weight: 600; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.compacta { padding: var(--space-2) var(--space-3); gap: 2px; border-radius: var(--radius-md); }
.compacta .etiqueta { font-size: var(--text-xs); gap: var(--space-1); }
.compacta .etiqueta .icono-pixel { width: 16px; height: 16px; }
.compacta .valor { font-size: var(--text-lg); }
</style>
