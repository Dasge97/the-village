<script setup>
// Iconos de la interfaz: una sola colección dibujada a mano, trazo de 2 px, 24 × 24.
defineProps({ nombre: String, tamano: { type: Number, default: 20 } });

const TRAZOS = {
  personas: "M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7M20 20v-1.5a3.5 3.5 0 0 0-2.5-3.35M15.5 4.15a3.5 3.5 0 0 1 0 6.7",
  libro: "M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5zM20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5zM7 8h1.5M7 11h1.5M15.5 8H17M15.5 11H17",
  familia: "M12 4v5M12 9H6v4M12 9h6v4M6 13a2 2 0 1 0 0 4 2 2 0 0 0 0-4M18 13a2 2 0 1 0 0 4 2 2 0 0 0 0-4M6 17v3M18 17v3",
  grafica: "M4 4v16h16M8 15l3-4 3 2 5-6",
  ajustes: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.5-2.4.9a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.5a7 7 0 0 0-2 1.2l-2.4-.9-2 3.5 2 1.5a7 7 0 0 0 0 2.4l-2 1.5 2 3.5 2.4-.9a7 7 0 0 0 2 1.2L10 21h4l.5-2.5a7 7 0 0 0 2-1.2l2.4.9 2-3.5-2-1.5c.07-.4.1-.8.1-1.2",
  cerrar: "M6 6l12 12M18 6L6 18",
  izquierda: "M15 6l-6 6 6 6",
  derecha: "M9 6l6 6-6 6",
  mas: "M12 5v14M5 12h14",
  menos: "M5 12h14",
  mapa: "M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14",
  menu: "M4 7h16M4 12h16M4 17h16",
  todo: "M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5",
  seguir: "M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5",
  corazon: "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10",
  casa: "M4 11l8-7 8 7M6 9.5V20h12V9.5M10 20v-5h4v5",
  alerta: "M12 4L3 20h18zM12 10v4M12 17h.01",
  brujula: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M15.5 8.5l-2 5-5 2 2-5z",
  sol: "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4",
  historial: "M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4M12 8v4l3 2",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M12 11v5M12 8h.01",
  reloj: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M12 7v5l3 2",
  regla: "M4 17L17 4l3 3L7 20zM8 13l2 2M11 10l2 2M14 7l2 2",
  ojo: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6",
  dado: "M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1M8.5 8.5h.01M15.5 15.5h.01M12 12h.01M15.5 8.5h.01M8.5 15.5h.01",
  candado: "M6 11h12v9H6zM8.5 11V8a3.5 3.5 0 0 1 7 0v3M12 15v2",
  chispa: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6",
  globo: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18M3 12h18M12 3c2.5 2.5 3.5 5.5 3.5 9s-1 6.5-3.5 9M12 3c-2.5 2.5-3.5 5.5-3.5 9s1 6.5 3.5 9",
  altavoz: "M4 9h4l5-4v14l-5-4H4zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11",
  silencio: "M4 9h4l5-4v14l-5-4H4zM16 9l5 6M21 9l-5 6",
  maximizar: "M14 4h6v6M20 4l-7 7M10 20H4v-6M4 20l7-7",
  minimizar: "M20 10h-6V4M14 10l7-7M4 14h6v6M10 14l-7 7",
};
</script>

<template>
  <svg :width="tamano" :height="tamano" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <path :d="TRAZOS[nombre]" />
  </svg>
</template>
