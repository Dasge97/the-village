// Coloca a todas las personas que han vivido en la aldea en un árbol genealógico.
// Cada generación es una fila: los fundadores y forasteros en la 0 y cada hijo una fila por debajo
// de su padre o madre más joven. Quien llega de fuera y forma pareja se pone en la fila de su pareja.
// Dentro de cada fila, las parejas van juntas y los hijos se ordenan bajo sus padres.

export const NODO = { ancho: 136, alto: 56, hueco: 16, fila: 104 };

export function calcularArbol(personas) {
  const porId = new Map(personas.map((p) => [p.id, p]));
  const padresDe = (p) => p.padres.map((i) => porId.get(i)).filter(Boolean);

  const gen = new Map();
  const generacion = (p) => {
    if (gen.has(p.id)) return gen.get(p.id);
    gen.set(p.id, 0);
    const padres = padresDe(p);
    const g = padres.length ? Math.max(...padres.map(generacion)) + 1 : 0;
    gen.set(p.id, g);
    return g;
  };
  personas.forEach(generacion);
  for (let vuelta = 0; vuelta < 3; vuelta++) {
    for (const p of personas) {
      if (padresDe(p).length) continue;
      for (const q of p.parejas.map((i) => porId.get(i)).filter(Boolean)) gen.set(p.id, Math.max(gen.get(p.id), gen.get(q.id)));
    }
  }

  const filas = [];
  for (const p of personas) (filas[gen.get(p.id)] ||= []).push(p);

  const x = new Map();
  const paso = NODO.ancho + NODO.hueco;
  filas.forEach((fila, g) => {
    if (!fila) return;
    // Clave de orden: la posición media de los padres (o la de los padres de la pareja).
    const clave = (p) => {
      let padres = padresDe(p);
      if (!padres.length) {
        const pareja = p.parejas.map((i) => porId.get(i)).find((q) => q && gen.get(q.id) === g && padresDe(q).length);
        if (pareja) padres = padresDe(pareja);
      }
      const xs = padres.map((q) => x.get(q.id)).filter((v) => v !== undefined);
      return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : -1e6 + p.nacimiento / 1e3;
    };
    const ordenados = [...fila].sort((a, b) => clave(a) - clave(b) || a.nacimiento - b.nacimiento);
    const colocados = [];
    const hecho = new Set();
    for (const p of ordenados) {
      if (hecho.has(p.id)) continue;
      colocados.push(p);
      hecho.add(p.id);
      // Sus parejas de la misma fila, justo al lado.
      for (const q of p.parejas.map((i) => porId.get(i))) {
        if (q && !hecho.has(q.id) && gen.get(q.id) === g) { colocados.push(q); hecho.add(q.id); }
      }
    }
    colocados.forEach((p, i) => x.set(p.id, i * paso));
  });

  const nodos = personas.map((p) => ({ ...p, x: x.get(p.id), y: gen.get(p.id) * NODO.fila, generacion: gen.get(p.id) }));
  const nodoDe = new Map(nodos.map((n) => [n.id, n]));

  // Líneas de pareja (entre los dos, a media altura) y de hijos (del centro de los padres al hijo).
  const parejas = [];
  const vistas = new Set();
  for (const n of nodos) {
    for (const i of n.parejas) {
      const q = nodoDe.get(i);
      const clave = [n.id, i].sort().join("-");
      if (!q || vistas.has(clave) || q.y !== n.y) continue;
      vistas.add(clave);
      parejas.push({ desde: n, hasta: q });
    }
  }
  const hijos = [];
  for (const n of nodos) {
    const padres = n.padres.map((i) => nodoDe.get(i)).filter(Boolean);
    if (!padres.length) continue;
    const xPadres = padres.reduce((s, q) => s + q.x, 0) / padres.length + NODO.ancho / 2;
    const yPadres = Math.max(...padres.map((q) => q.y)) + NODO.alto;
    hijos.push({ hijo: n, x1: xPadres, y1: yPadres, x2: n.x + NODO.ancho / 2, y2: n.y });
  }

  const ancho = Math.max(0, ...nodos.map((n) => n.x)) + NODO.ancho;
  const alto = Math.max(0, ...nodos.map((n) => n.y)) + NODO.alto;
  return { nodos, nodoDe, parejas, hijos, ancho, alto, generaciones: filas.length };
}

// Antepasados y descendientes de una persona, para resaltarlos en el árbol.
export function familiaDe(id, porId) {
  const sangre = new Set([id]);
  const subir = (i) => { for (const p of porId.get(i)?.padres || []) if (!sangre.has(p)) { sangre.add(p); subir(p); } };
  const bajar = (i) => { for (const h of porId.get(i)?.hijos || []) if (!sangre.has(h)) { sangre.add(h); bajar(h); } };
  subir(id);
  bajar(id);
  for (const p of porId.get(id)?.parejas || []) sangre.add(p);
  return sangre;
}

// Descendientes vivos de cada persona.
export function descendientesVivos(id, porId, vistos = new Set()) {
  let n = 0;
  for (const h of porId.get(id)?.hijos || []) {
    if (vistos.has(h)) continue;
    vistos.add(h);
    if (porId.get(h)?.vivo) n += 1;
    n += descendientesVivos(h, porId, vistos);
  }
  return n;
}
