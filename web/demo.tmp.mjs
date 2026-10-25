// Ventanas de demostración: La aldea (con su etapa) y el mapa del mundo, con el mundo a toda velocidad.
import { chromium } from "playwright-core";
const abrir = async (url, x) => {
  const nav = await chromium.launch({ channel: "chrome", headless: false, args: [`--window-position=${x},0`, "--window-size=960,1000"] });
  const p = await (await nav.newContext({ viewport: null })).newPage();
  await p.goto(url);
  return nav;
};
const a = await abrir("http://localhost:8030/?clima=ninguno#/historia?aldea=1", 0);
const b = await abrir("http://localhost:8030/?clima=ninguno#/mundo/historia", 960);
const salir = () => process.exit(0);
a.on("disconnected", salir);
b.on("disconnected", salir);
await new Promise(() => {});
