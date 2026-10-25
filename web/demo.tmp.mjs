// Ventanas de demostración: La aldea y el mapa del mundo con el mundo a toda velocidad.
import { chromium } from "playwright-core";
const navegador = await chromium.launch({ channel: "chrome", headless: false, args: ["--window-position=0,0", "--window-size=1280,900"] });
const aldea = await navegador.newContext({ viewport: null });
const p1 = await aldea.newPage();
await p1.goto("http://localhost:8030/?clima=ninguno#/historia/grande?aldea=1");
const mundo = await navegador.newContext({ viewport: null });
const p2 = await mundo.newPage();
await p2.goto("http://localhost:8030/?clima=ninguno#/mundo");
navegador.on("disconnected", () => process.exit(0));
await new Promise(() => {});
