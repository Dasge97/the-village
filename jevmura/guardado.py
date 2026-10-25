"""Guarda el mundo en SQLite y lo recupera al arrancar.

Tablas:
- `mundo`: una fila por clave. `estado` es todo lo que cambia de la aldea, en JSON. El mapa no se
  guarda porque sale de la semilla; de él solo se guarda el crecimiento de cada árbol.
- `cronica`: los sucesos del último año del mundo. Los más antiguos se borran al guardar.
- `resumenes`: un resumen por año del mundo. No se borran nunca.
- `personas`: la ficha de cada habitante que ha vivido en la aldea, para el árbol genealógico.
  No se borran nunca.

Si el servidor estuvo apagado, el mundo sigue desde el último guardado sin calcular los turnos
que se perdieron.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import asdict, fields

from .motor import modelos as m
from .motor.aldea import Aldea
from .motor.decisores import Decisor
from .motor.modelos import Casa, Habitante, Obra, Persona, Suceso

ESQUEMA = """
CREATE TABLE IF NOT EXISTS mundo (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cronica (turno INTEGER NOT NULL, tipo TEXT NOT NULL, texto TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS cronica_turno ON cronica (turno);
CREATE TABLE IF NOT EXISTS resumenes (ano INTEGER PRIMARY KEY, datos TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS personas (id INTEGER PRIMARY KEY, datos TEXT NOT NULL);
"""

# Campos que son tuplas y JSON devuelve como listas.
TUPLAS = {"objetivo", "arbol", "padres", "ruta_a"}
CONTADORES_JEV = ("llamadas", "errores", "coste", "segundos")


def _tuplas(datos: dict) -> dict:
    return {k: tuple(v) if k in TUPLAS and v is not None else v for k, v in datos.items()}


def _rng(estado: list) -> tuple:
    version, interno, gauss = estado
    return version, tuple(interno), gauss


class Guardado:
    def __init__(self, ruta: str):
        self.db = sqlite3.connect(ruta, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(ESQUEMA)
        self.db.commit()

    def cerrar(self) -> None:
        self.db.close()

    def existe(self) -> bool:
        return self._valor("estado") is not None

    def _valor(self, clave: str) -> str | None:
        fila = self.db.execute("SELECT valor FROM mundo WHERE clave = ?", (clave,)).fetchone()
        return fila[0] if fila else None

    # ---- guardar ----

    def guardar(self, aldea: Aldea) -> None:
        anterior = int(self._valor("turno_guardado") or -1)
        arboles = sorted(aldea.mapa.arboles)
        estado = {
            "semilla": aldea.semilla,
            "bioma": aldea.bioma,
            "formato": aldea.formato,
            "nombre": aldea.nombre,
            "turno": aldea.turno,
            "rng": aldea.rng.getstate(),
            "rng_respaldo": aldea.respaldo.rng.getstate(),
            "habitantes": [asdict(h) for h in aldea.habitantes.values()],
            "siguiente_id": aldea.siguiente_id,
            "casas": [asdict(c) for c in aldea.casas],
            "comida": aldea.comida,
            "madera": aldea.madera,
            "piedra": aldea.piedra,
            "peces": aldea.peces,
            "muralla": aldea.muralla,
            "obra": asdict(aldea.obra) if aldea.obra else None,
            "relaciones": [[a, b, v] for (a, b), v in aldea.relaciones.items()],
            "arboles": [aldea.mapa.arboles[p] for p in arboles],
            "sequia": aldea.sequia,
            "buena_pesca": aldea.buena_pesca,
            "decisiones": dict(aldea.decisiones),
            "fallos_seguidos": aldea.fallos_seguidos,
            "ano_en_curso": aldea.ano_en_curso,
            # Evolución de la aldea (motor/evolucion.py).
            "etapa": aldea.etapa, "edificios": aldea.edificios, "reforzados": aldea.reforzados,
            "faroles": aldea.faroles, "plan": aldea.plan, "consejo": aldea.consejo,
            "invierno_duro": aldea.invierno_duro, "arboles_quitados": aldea.arboles_quitados,
            # Totales de Jev desde que existe el mundo, para que no vuelvan a cero en cada reinicio.
            "jev": {c: getattr(aldea.decisor, c) for c in CONTADORES_JEV} if hasattr(aldea.decisor, "llamadas") else None,
        }
        # Personas que han podido cambiar desde el último guardado: los vivos y los que acaban de irse.
        personas = [p for p in aldea.registro.values() if p.salida is None or p.salida > anterior]
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO mundo VALUES ('estado', ?)", (json.dumps(estado),))
            self.db.execute("INSERT OR REPLACE INTO mundo VALUES ('turno_guardado', ?)", (str(aldea.turno),))
            self.db.executemany("INSERT INTO cronica VALUES (?, ?, ?)",
                                [(s.turno, s.tipo, s.texto) for s in aldea.cronica if s.turno > anterior])
            self.db.execute("DELETE FROM cronica WHERE turno <= ?", (aldea.turno - m.TURNOS_POR_ANO,))
            self.db.executemany("INSERT OR REPLACE INTO resumenes VALUES (?, ?)",
                                [(r["ano"], json.dumps(r)) for r in aldea.resumenes[-2:]])
            self.db.executemany("INSERT OR REPLACE INTO personas VALUES (?, ?)",
                                [(p.id, json.dumps(asdict(p))) for p in personas])

    # ---- cargar ----

    def cargar(self, decisor: Decisor | None = None) -> Aldea:
        e = json.loads(self._valor("estado"))
        aldea = Aldea(e["semilla"], decisor, bioma=e.get("bioma", "pradera"), formato=e.get("formato", "clasica"))
        aldea.nombre = e.get("nombre", aldea.nombre)
        aldea.turno = e["turno"]
        aldea.rng.setstate(_rng(e["rng"]))
        aldea.respaldo.rng.setstate(_rng(e["rng_respaldo"]))
        campos = {f.name for f in fields(Habitante)}
        aldea.habitantes = {d["id"]: Habitante(**_tuplas({k: v for k, v in d.items() if k in campos}))
                            for d in e["habitantes"]}
        aldea.siguiente_id = e["siguiente_id"]
        aldea.casas = [Casa(**c) for c in e["casas"]]
        for clave in ("comida", "madera", "piedra", "peces", "muralla", "sequia", "buena_pesca", "fallos_seguidos"):
            setattr(aldea, clave, e[clave])
        aldea.obra = Obra(**e["obra"]) if e["obra"] else None
        aldea.relaciones = {(a, b): v for a, b, v in e["relaciones"]}
        for p, valor in zip(sorted(aldea.mapa.arboles), e["arboles"]):
            aldea.mapa.arboles[p] = valor
        aldea.decisiones = Counter(e["decisiones"])
        for clave in ("etapa", "edificios", "reforzados", "faroles", "plan", "consejo", "invierno_duro"):
            if clave in e:
                setattr(aldea, clave, e[clave])
        aldea.arboles_quitados = [tuple(p) for p in e.get("arboles_quitados", [])]
        aldea._recalcular_efectos()
        aldea._comprobar_etapa()
        if e.get("jev") and hasattr(aldea.decisor, "llamadas"):
            for c in CONTADORES_JEV:
                setattr(aldea.decisor, c, e["jev"].get(c, 0))
        a = e["ano_en_curso"]
        aldea.ano_en_curso = {**a, "muertes": Counter(a["muertes"]), "producido": Counter(a["producido"])}
        aldea.cronica = [Suceso(*fila) for fila in self.db.execute(
            "SELECT turno, tipo, texto FROM cronica ORDER BY rowid")]
        aldea.resumenes = self.resumenes()
        aldea.registro = {p.id: p for p in self.personas()}
        return aldea

    # ---- consultas para la web ----

    def resumenes(self) -> list[dict]:
        return [json.loads(d) for (d,) in self.db.execute("SELECT datos FROM resumenes ORDER BY ano")]

    def personas(self) -> list[Persona]:
        return [Persona(**_tuplas(json.loads(d))) for (d,) in self.db.execute("SELECT datos FROM personas ORDER BY id")]
