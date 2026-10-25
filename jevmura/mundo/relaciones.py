"""Relaciones entre pueblos, villas y ciudades vecinos (a 3 zonas o menos): alianzas, rivalidades
con escaramuzas pequeñas y tributos de los pueblos a una ciudad o villa mucho más fuerte.

Cada par de vecinos tiene una relación de -100 a 100. Sube con el comercio y con terrenos distintos
(se necesitan); baja cuando los dos están llenos y compiten por el sitio, y se acerca a 0 con el
tiempo. Con 60 o más se alían; con -40 o menos son rivales. Se calcula una vez por estación.
Todo son reglas: no hay llamadas a Jev.

`Relaciones` es una clase base de `Mundo`.
"""

from __future__ import annotations

import random

ALCANCE = 3
ALIANZA = 60
FIN_ALIANZA = 20
RIVALIDAD = -40


def clave(a: int, b: int) -> str:
    return f"{min(a, b)}-{max(a, b)}"


def par(k: str) -> tuple[int, int]:
    a, b = k.split("-")
    return int(a), int(b)


class Relaciones:
    def _iniciar_relaciones(self, datos: dict | None = None) -> None:
        datos = datos or {}
        self.relaciones: dict[str, float] = dict(datos.get("relaciones", {}))
        self.alianzas: set[str] = set(datos.get("alianzas", []))
        self.vasallos: dict[int, int] = {int(k): v for k, v in datos.get("vasallos", {}).items()}

    def datos_relaciones(self) -> dict:
        return {"relaciones": {k: round(v, 1) for k, v in self.relaciones.items()},
                "alianzas": sorted(self.alianzas), "vasallos": {str(k): v for k, v in self.vasallos.items()}}

    def _vecinos_grandes(self) -> list[tuple[int, int]]:
        ids = sorted(self.grandes)
        return [(a, b) for n, a in enumerate(ids) for b in ids[n + 1:] if self.dist(a, b) <= ALCANCE]

    def sumar_relacion(self, a: int, b: int, puntos: float) -> None:
        if a in self.grandes and b in self.grandes:
            k = clave(a, b)
            self.relaciones[k] = max(-100.0, min(100.0, self.relaciones.get(k, 0.0) + puntos))

    def aliados(self, a: int, b: int) -> bool:
        return clave(a, b) in self.alianzas

    def _estacion_relaciones(self) -> None:
        """Una vez por estación: cambian las relaciones, se forman y rompen alianzas, hay
        escaramuzas entre rivales y se cobran y se rompen los tributos."""
        rng = random.Random(self.turno * 13 + 7)
        vecinos = self._vecinos_grandes()
        vivos = {clave(a, b) for a, b in vecinos}
        self.relaciones = {k: v for k, v in self.relaciones.items() if k in vivos}
        self.alianzas &= vivos
        for a, b in vecinos:
            ga, gb = self.grandes[a], self.grandes[b]
            k = clave(a, b)
            v = self.relaciones.get(k, 0.0) * 0.95
            if ga.bioma != gb.bioma:
                v += 2                                    # se necesitan: lo que a uno le sobra al otro le falta
            if ga.tipo == gb.tipo and ga.poblacion > 0.8 * ga.tope and gb.poblacion > 0.8 * gb.tope:
                # Los dos llenos compiten por el sitio de alrededor. Poco: con más, en un mundo lleno casi
                # todos los vecinos acababan siendo rivales (media de −30 frente al −40 de la rivalidad).
                v -= 1
            v += rng.uniform(-4, 4)
            self.relaciones[k] = max(-100.0, min(100.0, v))
            self._cambios_de_relacion(a, b, k)
        for a, b in vecinos:
            if self.relaciones.get(clave(a, b), 0) <= RIVALIDAD and rng.random() < 0.06:
                self._escaramuza(a, b, rng)
        self._tributos(vecinos, rng)
        self._proteccion()

    def _cambios_de_relacion(self, a: int, b: int, k: str) -> None:
        ga, gb = self.grandes[a], self.grandes[b]
        v = self.relaciones[k]
        if v >= ALIANZA and k not in self.alianzas:
            self.alianzas.add(k)
            for g, otro in ((ga, gb), (gb, ga)):
                g._cronica("hallazgo", f"{_Art(g.nombre)} se alía con {_art(otro.nombre)}: comercio y ayuda en los ataques.")
            if "ciudad" in (ga.tipo, gb.tipo):
                self.suceso(f"Alianza entre {_art(ga.nombre)} y {_art(gb.nombre)}.", a)
        elif v < FIN_ALIANZA and k in self.alianzas:
            self.alianzas.discard(k)
            for g, otro in ((ga, gb), (gb, ga)):
                g._cronica("discusion", f"Se rompe la alianza con {_art(otro.nombre)}.")

    def _escaramuza(self, a: int, b: int, rng) -> None:
        ga, gb = self.grandes[a], self.grandes[b]
        fa, fb = ga.defensa() * rng.uniform(0.6, 1.4), gb.defensa() * rng.uniform(0.6, 1.4)
        gana, pierde = (ga, gb) if fa >= fb else (gb, ga)
        bajas = max(1, round(pierde.poblacion * 0.004))
        pierde.sacar(bajas)
        botin = {}
        for r in ("comida", "madera", "piedra"):
            botin[r] = round(getattr(pierde, r) * 0.05)
            setattr(pierde, r, getattr(pierde, r) - botin[r])
            setattr(gana, r, getattr(gana, r) + botin[r])
        gana._cronica("ataque", f"Escaramuza con {_art(pierde.nombre)}: se gana y se traen {botin['comida']} de comida.")
        pierde._cronica("ataque", f"Escaramuza con {_art(gana.nombre)}: se pierde, con {bajas} muertos.")
        pierde.animo = max(0.0, pierde.animo - 0.05)
        if "ciudad" in (ga.tipo, gb.tipo):
            self.suceso(f"Escaramuza entre {_art(ga.nombre)} y {_art(gb.nombre)}. Gana {_art(gana.nombre)}.", gana.id)

    def _tributos(self, vecinos: list[tuple[int, int]], rng) -> None:
        # Los que ya pagan: tributo de la estación o independencia.
        for v, s in list(self.vasallos.items()):
            gv, gs = self.grandes.get(v), self.grandes.get(s)
            if not gv or not gs:
                self.vasallos.pop(v, None)
                continue
            oro = round(gv.oro * 0.15)
            comida = round(gv.comida * 0.05)
            gv.oro -= oro
            gv.comida -= comida
            gs.oro += oro
            gs.comida += comida
            gv.descontento = min(1.0, gv.descontento + 0.02)
            if (gv.descontento > 0.6 or gv.poblacion > gs.poblacion / 5) and rng.random() < 0.2:
                del self.vasallos[v]
                self.sumar_relacion(v, s, -30)
                gv._cronica("discusion", f"Se deja de pagar tributo {_al(gs.nombre)}: el {gv.nombre} vuelve a ser libre.")
                gs._cronica("discusion", f"El {gv.nombre} se niega a seguir pagando tributo.")
                self.suceso(f"El {gv.nombre} deja de pagar tributo {_al(gs.nombre)}.", v)
        # Nuevos: una ciudad o villa muy fuerte exige tributo a un pueblo vecino pequeño.
        for a, b in vecinos:
            for s, v in ((a, b), (b, a)):
                gs, gv = self.grandes[s], self.grandes[v]
                if (gs.tipo != "pueblo" and gv.tipo == "pueblo" and v not in self.vasallos and s not in self.vasallos
                        and gv.poblacion < gs.poblacion / 20 and gs.defensa() > 5 * gv.defensa()
                        and not self.aliados(s, v) and rng.random() < 0.05):
                    self.vasallos[v] = s
                    gv._cronica("discusion", f"{_Art(gs.nombre)} exige tributo al {gv.nombre}, que no puede negarse.")
                    gs._cronica("oficio", f"El {gv.nombre} empieza a pagar tributo {_al(gs.nombre)}.")
                    self.suceso(f"El {gv.nombre} empieza a pagar tributo {_al(gs.nombre)}.", s)

    def _proteccion(self) -> None:
        """Ayuda en los ataques: los aliados mandan algo de su defensa y el señor protege a quien le paga."""
        ayuda = {i: 0.0 for i in self.grandes}
        for k in self.alianzas:
            a, b = par(k)
            if a in self.grandes and b in self.grandes:
                ayuda[a] += 0.15 * self.grandes[b].defensa_propia()
                ayuda[b] += 0.15 * self.grandes[a].defensa_propia()
        for v, s in self.vasallos.items():
            if v in ayuda and s in self.grandes:
                ayuda[v] += 0.1 * self.grandes[s].defensa_propia()
        for i, g in self.grandes.items():
            g.proteccion = ayuda[i]

    def relaciones_de(self, id: int) -> dict:
        """Aliados, rivales, señor y vasallos de un asentamiento, con su nombre, para la web."""
        if id not in self.grandes:
            return {}
        aliados, rivales = [], []
        for k, v in self.relaciones.items():
            a, b = par(k)
            if id not in (a, b):
                continue
            otro = b if a == id else a
            if otro not in self.meta:
                continue
            nombre = self.meta[otro]["nombre"]
            if k in self.alianzas:
                aliados.append({"id": otro, "nombre": nombre})
            elif v <= RIVALIDAD:
                rivales.append({"id": otro, "nombre": nombre})
        senor = self.vasallos.get(id)
        return {"aliados": aliados, "rivales": rivales,
                "senor": {"id": senor, "nombre": self.meta[senor]["nombre"]} if senor in self.meta else None,
                "vasallos": [{"id": v, "nombre": self.meta[v]["nombre"]} for v, s in self.vasallos.items() if s == id and v in self.meta]}


def _art(nombre: str) -> str:
    return f"la {nombre}" if nombre.startswith(("Villa", "Ciudad")) else f"el {nombre}"


def _Art(nombre: str) -> str:
    t = _art(nombre)
    return t[0].upper() + t[1:]


def _al(nombre: str) -> str:
    return f"a la {nombre}" if nombre.startswith(("Villa", "Ciudad")) else f"al {nombre}"
