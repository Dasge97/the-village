// Saca capturas de la web en varios anchos y modos, y enseña los mensajes de la consola.
// Uso: node capturas.mjs [url] [carpeta] [espera en ms] [rutas separadas por comas, p. ej. "#/familias,#/historia"]
import { chromium } from "playwright-core";

const url = process.argv[2] || "http://localhost:8000/";
const carpeta = process.argv[3] || ".";
const espera = Number(process.argv[4] || 4000);
const RUTAS = (process.argv[5] || "").split(",").filter(Boolean);
const ANCHOS = [[375, 812], [768, 1024], [1280, 800], [1440, 900]];

const navegador = await chromium.launch({ channel: "chrome", args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
for (const ruta of RUTAS.length ? RUTAS : [""]) {
for (const tema of ["light", "dark"]) {
  for (const [w, h] of ANCHOS) {
    const pagina = await navegador.newPage({ viewport: { width: w, height: h }, colorScheme: tema });
    pagina.on("console", (m) => console.log(`[${tema} ${w}] consola ${m.type()}: ${m.text()}`));
    pagina.on("pageerror", (e) => console.log(`[${tema} ${w}] error: ${e.message}`));
    await pagina.goto(url + ruta);
    await pagina.waitForTimeout(espera);
    const desborde = await pagina.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (desborde) console.log(`[${tema} ${w}] AVISO: hay desplazamiento horizontal`);
    await pagina.screenshot({ path: `${carpeta}/${ruta.replace(/[#/]+/g, "_") || "inicio"}-${tema}-${w}.png`, fullPage: true });
    await pagina.close();
  }
}
}
await navegador.close();
