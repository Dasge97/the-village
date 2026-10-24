import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// En desarrollo, la API y el websocket los sirve `python -m jevmura.servidor` en el puerto 8000.
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
