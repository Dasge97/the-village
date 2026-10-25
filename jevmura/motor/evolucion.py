"""Evolución de una aldea: etapas de edificios, mejoras, desgaste, reparaciones, consejo de la
aldea y gastos que no se acaban (fiestas, bodas, inviernos duros).

Una aldea empieza en la etapa 1 (casas y muralla). Al completar la muralla por primera vez se abre
la etapa 2; con sus cinco edificios, la 3; con los cuatro de la 3, la 4 (mejoras tramo a tramo y
casa a casa). Cada edificio tiene un efecto que se aplica en el motor (ver `efecto`) y se estropea
con los años: por debajo de 50 de estado su efecto se queda en la mitad y a 0 se pierde.

Las obras nuevas son opciones «construir» dentro de las decisiones de siempre: Jev no hace más
llamadas. El orden lo deciden las reglas, salvo que el consejo de la aldea haya elegido una obra
(una vez por estación, con Jev si queda presupuesto de consejos; lo llama el mundo).

`Evolucion` es una clase base de `Aldea`: usa sus recursos, su crónica y su azar.
"""

from __future__ import annotations

from . import modelos as m
from .modelos import Obra

# Edificios de las etapas 2 y 3: coste, turnos de obra, sitio en el mapa (casilla de abajo en el
# centro, desde el centro de la aldea; todos caben dentro de la muralla salvo los huertos) y qué dan.
EDIFICIOS = {
    "pozo": {"etapa": 2, "madera": 50, "piedra": 150, "turnos": 900, "sitio": (-6, -1),
             "nombre": "el pozo", "efecto": "menos enfermedades y la salud se recupera antes"},
    "granero": {"etapa": 2, "madera": 200, "piedra": 100, "turnos": 1200, "sitio": (-9, -8),
                "nombre": "el granero", "efecto": "cabe más comida y se pierde menos cada día"},
    "taller": {"etapa": 2, "madera": 180, "piedra": 180, "turnos": 1200, "sitio": (9, -8),
               "nombre": "el taller", "efecto": "leñadores y canteros sacan más"},
    "vigia": {"etapa": 2, "madera": 150, "piedra": 240, "turnos": 1200, "sitio": (11, -11),
              "nombre": "la torre de vigía", "efecto": "más defensa de noche y los ataques rompen menos muralla"},
    "huertos": {"etapa": 2, "madera": 150, "piedra": 60, "turnos": 1000, "sitio": (17, 11),
                "nombre": "los huertos nuevos", "efecto": "más campo y más cosecha"},
    "almacen": {"etapa": 3, "madera": 160, "piedra": 220, "turnos": 1500, "sitio": (-8, 10),
                "nombre": "el almacén de piedra", "efecto": "cabe más madera y piedra"},
    "templo": {"etapa": 3, "madera": 300, "piedra": 480, "turnos": 2400, "sitio": (-3, 11),
               "nombre": "el templo", "efecto": "más ánimo; una muerte baja menos el ánimo de los demás"},
    "dojo": {"etapa": 3, "madera": 400, "piedra": 400, "turnos": 2100, "sitio": (9, 11),
             "nombre": "el dojo", "efecto": "cada guardia defiende más"},
    "mercado": {"etapa": 3, "madera": 350, "piedra": 300, "turnos": 1800, "sitio": (4, 11),
                "nombre": "el mercado", "efecto": "manda caravanas con lo que sobra a las aldeas y pueblos cercanos"},
}
ORDEN = list(EDIFICIOS)
# Huertos nuevos: rectángulo de campo junto a los de siempre, desde el centro de la aldea.
HUERTOS = ((13, 11), (20, 16))

# Mejoras de la etapa 4, una a una.
MEJORAS = {
    "casa_piedra": {"madera": 40, "piedra": 200, "turnos": 1000},
    "reforzar": {"madera": 15, "piedra": 120, "turnos": 700},
    "faroles": {"madera": 80, "piedra": 40, "turnos": 450},
}
FAROLES = [(-1, -11), (1, 10), (-10, -1), (11, -1)]     # junto a las cuatro puertas

ETAPAS = {1: "Asentamiento", 2: "Aldea", 3: "Aldea próspera", 4: "Mejoras"}
DESGASTE_EDIFICIO = 100 / (6 * m.DIAS_POR_ANO)     # de 100 a 0 en unos 6 años sin reparar
DESGASTE_CASA = 100 / (8 * m.DIAS_POR_ANO)
REPARAR_EDIFICIO = 50                              # por debajo, su efecto es la mitad y se puede reparar
REPARAR_CASA = 40
PARTE_REPARACION = 0.3                             # una reparación cuesta el 30 % de la obra nueva
PROBABILIDAD_INVIERNO_DURO = 0.2
INSTRUCCIONES_CONSEJO_ALDEA = (
    "Eres el consejo de una pequeña aldea de estilo Japón feudal. Elige qué hacer esta estación para "
    "que la aldea viva bien y dure: qué obra empezar la próxima vez que haya recursos, o hacer una "
    "fiesta. Cada opción explica lo que consigue.")


def coste_obra(o: Obra) -> dict:
    """Madera, piedra y turnos de una obra, sea del tipo que sea."""
    if o.tipo in m.OBRAS:
        return m.OBRAS[o.tipo]
    if o.tipo == "edificio":
        return EDIFICIOS[o.nombre]
    if o.tipo == "reparar":
        base = EDIFICIOS[o.nombre] if o.nombre else m.OBRAS["casa"]
        return {k: round(base[k] * PARTE_REPARACION) for k in ("madera", "piedra")} | {
            "turnos": round(base["turnos"] * 0.4)}
    return MEJORAS[o.tipo]


class Evolucion:
    """Lo que añade la evolución a una aldea. Se inicia con `_iniciar_evolucion`."""

    def _iniciar_evolucion(self) -> None:
        self.etapa = 1
        self.edificios: dict[str, float] = {}     # edificio → estado de 0 a 100
        self.reforzados = 0                        # tramos de muralla reforzados (los primeros)
        self.faroles = 0
        self.plan: str | None = None               # el edificio que eligió el consejo
        self.consejo: dict = {}                    # la última decisión del consejo
        self.invierno_duro = False
        self.arboles_quitados: list[tuple[int, int]] = []   # los árboles que quitaron los huertos nuevos
        self.efectos: dict[str, float] = {}

    # ---- efectos ----

    def efecto(self, nombre: str) -> float:
        """1 si el edificio está bien, 0,5 si está estropeado, 0 si no existe o está en ruinas."""
        return self.efectos.get(nombre, 0.0)

    def _recalcular_efectos(self) -> None:
        self.efectos = {n: 0.0 if e <= 0 else 0.5 if e < REPARAR_EDIFICIO else 1.0 for n, e in self.edificios.items()}

    def tope(self, recurso: str) -> float:
        base = self.ALMACEN_MAX[recurso]
        if recurso == "comida":
            return base + 300 * self.efecto("granero")
        return base + 250 * self.efecto("almacen")

    def campos_de_trabajo(self) -> list[tuple[int, int]]:
        if "huertos" not in self.edificios:
            return self.mapa.campos
        (x0, y0), (x1, y1) = self.rect_huertos()
        return self.mapa.campos + [(x, y) for y in range(y0 + 1, y1) for x in range(x0 + 1, x1)]

    def rect_huertos(self) -> tuple[tuple[int, int], tuple[int, int]]:
        cx, cy = self.mapa.almacen
        (dx0, dy0), (dx1, dy1) = HUERTOS
        return (cx + dx0, cy + dy0), (cx + dx1, cy + dy1)

    def sitio(self, nombre: str) -> tuple[int, int]:
        cx, cy = self.mapa.almacen
        dx, dy = EDIFICIOS[nombre]["sitio"]
        return cx + dx, cy + dy

    def sitio_farol(self, k: int) -> tuple[int, int]:
        cx, cy = self.mapa.almacen
        return cx + FAROLES[k][0], cy + FAROLES[k][1]

    # ---- qué se puede construir ----

    def disponibles(self) -> list[str]:
        """Edificios de las etapas abiertas que aún no existen."""
        return [n for n in ORDEN if n not in self.edificios and EDIFICIOS[n]["etapa"] <= self.etapa]

    def _candidatas(self) -> list[tuple[str, str | int | None]]:
        """Obras posibles de la evolución, de la más a la menos urgente: reparar, el edificio que
        eligió el consejo, el siguiente de su etapa y las mejoras de la etapa 4."""
        lista: list[tuple[str, str | int | None]] = []
        rotos = sorted((e, n) for n, e in self.edificios.items() if e < REPARAR_EDIFICIO)
        lista += [("reparar", n) for _, n in rotos[:1]]
        viejas = sorted((c.estado, c.id) for c in self.casas if not c.quemada and c.estado < REPARAR_CASA)
        lista += [("reparar_casa", i) for _, i in viejas[:1]]
        libres = self.disponibles()
        if self.plan in libres:
            lista.append(("edificio", self.plan))
        lista += [("edificio", n) for n in libres if n != self.plan]
        if self.etapa >= 4:
            if self.reforzados < min(self.muralla, m.TRAMOS_MURALLA):
                lista.append(("reforzar", None))
            sin_piedra = [c for c in self.casas if not c.quemada and not c.piedra]
            if sin_piedra:
                lista.append(("casa_piedra", sin_piedra[0].id))
            if self.faroles < len(FAROLES):
                lista.append(("faroles", None))
        return lista

    def _coste_candidata(self, tipo: str, cual) -> dict:
        if tipo == "edificio":
            return EDIFICIOS[cual]
        if tipo == "reparar":
            return coste_obra(Obra("reparar", 0, 0, nombre=cual))
        if tipo == "reparar_casa":
            return coste_obra(Obra("reparar", 0, 0))
        return MEJORAS[tipo]

    def _pagable(self, coste: dict) -> bool:
        # Se guarda leña para el invierno, pero nunca más de lo que deja sitio en el almacén.
        reserva = min(self._lena_necesaria(), max(0.0, self.tope("madera") - coste["madera"]))
        return self.madera >= coste["madera"] + reserva and self.piedra >= coste["piedra"]

    def obra_evolucion(self, pagar: bool = True) -> tuple[str, str | int | None] | None:
        """La primera obra de la evolución que se puede pagar (o, con `pagar=False`, la primera). Con
        comida para menos de 4 días no se empieza ninguna: antes hay que comer."""
        if pagar and self.comida < 4 * 1.75 * max(1, len(self.habitantes)):
            return None
        for tipo, cual in self._candidatas():
            if not pagar or self._pagable(self._coste_candidata(tipo, cual)):
                return tipo, cual
        return None

    def texto_obra(self, tipo: str, cual) -> str:
        """Descripción de la obra para la opción «construir» de un habitante."""
        if tipo == "edificio":
            e = EDIFICIOS[cual]
            return f"Empezar {e['nombre']}: {e['efecto']}"
        if tipo == "reparar":
            return f"Reparar {EDIFICIOS[cual]['nombre']}: está muy estropeado y ya solo hace la mitad de lo que hacía"
        if tipo == "reparar_casa":
            return "Reparar una casa vieja: tiene goteras y sus vecinos están peor"
        if tipo == "reforzar":
            return "Reforzar un tramo de muralla: así los ataques casi nunca lo rompen"
        if tipo == "casa_piedra":
            return "Rehacer una casa en piedra: no se quema tan fácil y se vive mejor en ella"
        return "Poner faroles junto a una puerta: de noche los ataques se frenan mejor"

    def nombre_obra(self, o: Obra) -> str:
        """La obra en curso en pocas palabras, para el estado de la aldea."""
        if o.tipo == "edificio":
            return EDIFICIOS[o.nombre]["nombre"]
        if o.tipo == "reparar":
            return f"reparar {EDIFICIOS[o.nombre]['nombre']}" if o.nombre else "reparar una casa"
        return {"casa_piedra": "una casa de piedra", "reforzar": "reforzar un tramo de muralla",
                "faroles": "unos faroles"}.get(o.tipo, o.tipo)

    def empezar_evolucion(self, tipo: str, cual) -> None:
        coste = self._coste_candidata(tipo, cual)
        self.madera -= coste["madera"]
        self.piedra -= coste["piedra"]
        if tipo == "edificio":
            x, y = self.sitio(cual)
            self.obra = Obra("edificio", x, y, nombre=cual)
            if self.plan == cual:
                self.plan = None
        elif tipo == "reparar":
            x, y = self.sitio(cual)
            self.obra = Obra("reparar", x, y, nombre=cual)
        elif tipo == "reparar_casa":
            c = self.casas[cual - 1]
            self.obra = Obra("reparar", c.x, c.y, casa=c.id)
        elif tipo == "casa_piedra":
            c = self.casas[cual - 1]
            self.obra = Obra("casa_piedra", c.x, c.y, casa=c.id)
        elif tipo == "reforzar":
            x, y = self.mapa.muralla[self.reforzados]
            self.obra = Obra("reforzar", x, y)
        else:
            x, y = self.sitio_farol(self.faroles)
            self.obra = Obra("faroles", x, y)

    def terminar_evolucion(self, o: Obra) -> None:
        if o.tipo == "edificio":
            self.edificios[o.nombre] = 100.0
            e = EDIFICIOS[o.nombre]
            self._cronica("obra", f"Los vecinos terminan {e['nombre']}: {e['efecto']}.")
            if o.nombre == "huertos":
                self._quitar_arboles_huertos()
        elif o.tipo == "reparar" and o.nombre:
            self.edificios[o.nombre] = 100.0
            self._cronica("obra", f"Los vecinos reparan {EDIFICIOS[o.nombre]['nombre']}.")
        elif o.tipo == "reparar":
            self.casas[o.casa - 1].estado = 100.0
            self._cronica("casa", "Los vecinos arreglan una casa vieja.")
        elif o.tipo == "casa_piedra":
            c = self.casas[o.casa - 1]
            c.piedra, c.estado = True, 100.0
            self._cronica("casa", "Una casa de madera pasa a ser de piedra.")
        elif o.tipo == "reforzar":
            self.reforzados += 1
            self._cronica("muralla", f"Ya hay {self.reforzados} tramos de muralla reforzados.")
        elif o.tipo == "faroles":
            self.faroles += 1
            self._cronica("obra", "Ponen faroles junto a una de las puertas de la aldea.")
        self._recalcular_efectos()
        self._comprobar_etapa()

    def _quitar_arboles_huertos(self) -> None:
        (x0, y0), (x1, y1) = self.rect_huertos()
        for p in list(self.mapa.arboles):
            if x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
                self.mapa.arboles[p] = 0.0
                self.arboles_quitados.append(p)

    def _comprobar_etapa(self) -> None:
        nueva = self.etapa
        if self.etapa == 1 and self.muralla >= m.TRAMOS_MURALLA:
            nueva = 2
        elif self.etapa in (2, 3) and all(n in self.edificios for n in ORDEN if EDIFICIOS[n]["etapa"] == self.etapa):
            nueva = self.etapa + 1
        if nueva != self.etapa:
            self.etapa = nueva
            texto = {2: "Con la muralla completa, la aldea puede empezar a construir pozo, granero, taller, torre de vigía y huertos.",
                     3: "La aldea prospera: ya puede pensar en un templo, un dojo, un mercado y un almacén de piedra.",
                     4: "La aldea tiene todos sus edificios. Ahora toca mejorarla: casas de piedra, muralla reforzada y faroles."}[nueva]
            self._cronica("etapa", f"Nueva etapa: {ETAPAS[nueva]}. {texto}")

    # ---- cada día ----

    def dia_evolucion(self) -> None:
        """Desgaste de edificios y casas, casas viejas que bajan el ánimo y nuevas etapas."""
        for n in self.edificios:
            self.edificios[n] = max(0.0, self.edificios[n] - DESGASTE_EDIFICIO)
        for c in self.casas:
            if not c.quemada:
                c.estado = max(0.0, c.estado - DESGASTE_CASA * (0.5 if c.piedra else 1.0))
        for h in self.habitantes.values():
            casa = self._casa(h.casa)
            if casa and casa.estado < 30:
                h.animo = max(0.0, h.animo - 1.0)
            elif casa and casa.piedra:
                h.animo = min(100.0, h.animo + 0.5)
        self._recalcular_efectos()
        self._comprobar_etapa()

    def danar_edificio(self, cuanto: float) -> str | None:
        """Un ataque que entra en la aldea estropea un edificio. Devuelve su nombre, si hay."""
        if not self.edificios:
            return None
        n = self.rng.choice(sorted(self.edificios))
        self.edificios[n] = max(0.0, self.edificios[n] - cuanto)
        self._recalcular_efectos()
        return EDIFICIOS[n]["nombre"]

    # ---- consejo de la aldea ----

    def toca_consejo(self) -> bool:
        """Una vez por estación, a las 9 de la mañana del primer día."""
        return (self.dia % m.DIAS_POR_ESTACION == 0 and self.turno % m.TURNOS_POR_DIA == 9 * m.TURNOS_POR_HORA
                and bool(self.habitantes))

    def opciones_consejo(self) -> dict[str, str]:
        ops = {f"obra:{n}": f"Que la próxima obra sea {EDIFICIOS[n]['nombre']}: {EDIFICIOS[n]['efecto']}"
               for n in self.disponibles()}
        poblacion = len(self.habitantes)
        if self.estacion == "otoño" and self.comida >= 12 * poblacion:
            ops["fiesta"] = (f"Celebrar la fiesta de la cosecha: gasta unas {3 * poblacion} de comida y "
                             f"sube mucho el ánimo de todos")
        ops["seguir"] = "Seguir como hasta ahora: las obras se eligen según lo que más falte"
        return ops

    def situacion_consejo(self) -> dict:
        e = self.estado()
        return {"aldea": self.nombre, "estacion": self.estacion, "ano": self.ano, "poblacion": e.poblacion,
                "comida": e.comida, "madera": e.madera, "piedra": e.piedra, "dias_comida": e.dias_comida,
                "etapa": ETAPAS[self.etapa], "edificios": {EDIFICIOS[n]["nombre"]: round(v) for n, v in self.edificios.items()},
                "muralla": self.muralla, "enfermos": sum(1 for h in self.habitantes.values() if h.enfermo_hasta > self.turno),
                "animo_medio": round(sum(h.animo for h in self.habitantes.values()) / max(1, e.poblacion)),
                "sucesos": [s.texto for s in self.cronica[-5:]]}

    def eleccion_consejo_reglas(self) -> str:
        ops = self.opciones_consejo()
        animo = sum(h.animo for h in self.habitantes.values()) / max(1, len(self.habitantes))
        if "fiesta" in ops and animo < 60:
            return "fiesta"
        enfermos = sum(1 for h in self.habitantes.values() if h.enfermo_hasta > self.turno)
        preferidos = (["pozo"] if enfermos >= 2 else []) + (["granero"] if self.estado().dias_comida < 6 else []) + ORDEN
        for n in preferidos:
            if f"obra:{n}" in ops:
                return f"obra:{n}"
        return "seguir"

    def aplicar_consejo(self, eleccion: str, quien: str, confianza: float | None = None) -> None:
        ops = self.opciones_consejo()
        if eleccion not in ops:
            eleccion = "seguir"
        texto = ops[eleccion].split(":")[0]
        if eleccion.startswith("obra:"):
            self.plan = eleccion.split(":")[1]
        elif eleccion == "fiesta":
            self.fiesta()
        self.consejo = {"turno": self.turno, "eleccion": eleccion, "texto": texto, "quien": quien, "confianza": confianza}
        if eleccion != "seguir":
            self._cronica("consejo", f"El consejo de la aldea decide: {texto[0].lower() + texto[1:]}.")

    # ---- gastos ----

    def fiesta(self) -> None:
        poblacion = len(self.habitantes)
        self.comida = max(0.0, self.comida - 3 * poblacion)
        for h in self.habitantes.values():
            h.animo = min(100.0, h.animo + 15)
        self._cronica("fiesta", "La aldea celebra la fiesta de la cosecha. Hay comida y música para todos.")

    def boda(self) -> None:
        gasto = min(10.0, self.comida * 0.1)
        self.comida -= gasto
        for h in self.habitantes.values():
            h.animo = min(100.0, h.animo + 3)

    def empieza_estacion(self) -> None:
        self.invierno_duro = self.estacion == "invierno" and self.rng.random() < PROBABILIDAD_INVIERNO_DURO
        if self.invierno_duro:
            self._cronica("frio", "Llega un invierno muy duro: harán falta el doble de leña.")
