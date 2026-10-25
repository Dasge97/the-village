"""Vida de los pueblos, villas y ciudades más allá de crecer: oro e impuestos, edificios nuevos,
avances, especialidad del terreno, sociedad (descontento, protestas, revueltas y elecciones),
sucesos grandes y monumentos.

Todo son reglas y números: no hay llamadas nuevas a Jev. El consejo de cada estación tiene más
opciones en la misma llamada (investigar, monumento, impuestos). `Sociedad` es una clase base de
`Grande` y usa sus recursos, su crónica y su azar.
"""

from __future__ import annotations

from ..motor import modelos as m

# Edificios nuevos: madera, piedra, días de obra y qué dan; desde qué tipo de asentamiento.
EDIFICIOS_NUEVOS = {
    "herreria": (60, 80, 5, "herramientas: más madera y piedra"),
    "escuela": (70, 60, 6, "gente mejor preparada: más producción y avances más rápidos"),
    "hospital": (60, 90, 6, "epidemias más cortas y menos muertes"),
    "mina": (80, 40, 5, "más piedra y algo de oro"),
    "acueducto": (40, 200, 10, "agua limpia: más salud"),
    "puerto": (150, 60, 7, "comercio por el río: las caravanas valen más"),
    "teatro": (100, 100, 7, "más ánimo"),
    "cuartel": (90, 140, 7, "más defensa contra los ataques"),
    "biblioteca": (90, 120, 8, "avances mucho más rápidos"),
}
DESDE = {"herreria": "pueblo", "escuela": "pueblo", "hospital": "pueblo", "mina": "pueblo",
         "acueducto": "villa", "puerto": "villa", "teatro": "villa", "cuartel": "villa", "biblioteca": "ciudad"}
NIVEL = {"pueblo": 0, "villa": 1, "ciudad": 2}

# Avances: qué hace falta para investigarlos, días de investigación y qué dan.
AVANCES = {
    "herramientas de hierro": {"pide": ["herreria"], "dias": 80, "da": "más madera y piedra"},
    "molinos": {"pide": ["granero"], "dias": 80, "da": "más comida"},
    "rueda": {"pide": ["mercado"], "dias": 100, "da": "más comercio y más oro"},
    "escritura": {"pide": ["escuela"], "dias": 120, "da": "se investiga más deprisa"},
    "medicina": {"pide": ["hospital"], "dias": 120, "da": "menos muertes de niños y epidemias más suaves"},
    "ingeniería": {"pide": ["escritura", "taller"], "dias": 140, "da": "las obras se terminan antes"},
    "astronomía": {"pide": ["biblioteca"], "dias": 160, "da": "mejores cosechas y más ánimo"},
    "acero": {"pide": ["herramientas de hierro", "mina"], "dias": 160, "da": "más defensa"},
}
ORO_INVESTIGAR = 0.5           # oro al día mientras se investiga (más un poco por habitante)

# Monumentos: desde qué tipo, coste (madera, piedra, oro), días de obra y qué dan.
MONUMENTOS = {
    "estatua": {"desde": "villa", "coste": (100, 300, 150), "dias": 120, "da": "orgullo: más ánimo"},
    "gran templo": {"desde": "villa", "coste": (300, 600, 300), "dias": 200, "da": "más ánimo y menos epidemias"},
    "castillo": {"desde": "ciudad", "coste": (400, 1200, 600), "dias": 280, "da": "mucha más defensa"},
    "faro": {"desde": "ciudad", "coste": (200, 500, 400), "dias": 180, "da": "atrae a gente y comercio de lejos"},
}

# Lo que da cada terreno de más y lo que vale en el comercio con otros terrenos.
ESPECIALIDAD = {"pradera": "trigo", "bosque": "madera noble", "desierto": "especias y vidrio",
                "nieve": "pieles", "pantano": "hierbas medicinales"}
IMPUESTOS = {"bajo": (0.0005, 0.03), "normal": (0.001, 0.0), "alto": (0.002, -0.07)}   # oro por persona y día, ánimo

# Sucesos grandes: probabilidad al día y desde qué tipo.
SUCESOS = {"inundacion": (1 / 900, "pueblo"), "terremoto": (1 / 2400, "pueblo"), "gran_incendio": (1 / 1200, "villa"),
           "hambruna": (1 / 1500, "pueblo"), "peste": (1 / 3000, "villa"), "cometa": (1 / 4000, "pueblo"),
           "mercader": (1 / 400, "pueblo"), "veta": (1 / 1500, "pueblo")}


class Sociedad:
    """Lo que añade la vida social a un `Grande`. Sus campos (oro, impuesto, avances…) están en `Grande`."""

    # ---- efectos que usa el resto del motor ----

    def tiene(self, cosa: str) -> bool:
        """Un edificio construido o un avance ya investigado."""
        return bool(self.edificios.get(cosa)) or cosa in self.avances

    def factor_produccion(self) -> float:
        f = 1.0 + 0.1 * self.tiene("herreria") + 0.05 * self.tiene("escuela") + 0.15 * self.tiene("herramientas de hierro")
        return f * (0.8 if self.protesta else 1.0)

    def factor_comida(self) -> float:
        f = 1.0 + 0.1 * self.tiene("molinos") + 0.05 * self.tiene("astronomía")
        return f * (0.5 if self.hambruna else 1.0)

    def defensa_extra(self) -> float:
        d = 6 * self.edificios.get("cuartel", 0) + (0.3 * self.poblacion ** 0.5 if self.tiene("acero") else 0)
        return d + (40 if "castillo" in self.monumentos else 0)

    def animo_extra(self) -> float:
        a = 0.04 * self.tiene("teatro") + IMPUESTOS[self.impuesto][1]
        a += 0.03 * ("estatua" in self.monumentos) + 0.04 * ("gran templo" in self.monumentos) + 0.02 * self.tiene("astronomía")
        return a - (0.1 if self.protesta else 0)

    def factor_mortalidad(self) -> float:
        return (1 - 0.25 * self.tiene("hospital")) * (1 - 0.2 * self.tiene("medicina")) * (1 - 0.1 * self.tiene("acueducto"))

    def factor_epidemia(self) -> float:
        """Cuánto más rara es una epidemia (más alto, más rara)."""
        return 1 + self.tiene("acueducto") + 0.5 * ("gran templo" in self.monumentos) + 0.5 * self.tiene("medicina")

    def factor_obras(self) -> float:
        return 0.7 if self.tiene("ingeniería") else 1.0

    def factor_comercio(self) -> float:
        return 1 + 0.5 * self.tiene("rueda") + 0.5 * self.tiene("puerto") + 0.5 * ("faro" in self.monumentos)

    def especialidad(self) -> str:
        return ESPECIALIDAD[self.bioma]

    # ---- cada día ----

    def dia_sociedad(self) -> None:
        pob = self.poblacion
        self.oro += pob * IMPUESTOS[self.impuesto][0] * (1 + 0.5 * self.tiene("rueda")) + 1.5 * self.edificios.get("mina", 0)
        self.piedra += 3 * self.edificios.get("mina", 0)
        self.hambruna = max(0, self.hambruna - 1)
        self._investigar()
        self._obra_monumento()
        self._descontento()
        self._sucesos_grandes()
        # En una hambruna, si hay oro, se compra comida fuera.
        if self.comida < self.comida_diaria() * 2 and self.oro > 20:
            gasto = min(self.oro, self.comida_diaria() * 3 / 5)
            self.oro -= gasto
            self.comida += gasto * 5
            if self.rng.random() < 0.1:
                self._cronica("hallazgo", "Falta comida: el consejo la compra fuera con el oro guardado.")
        if self.dia % m.DIAS_POR_ANO == 0:
            self._elecciones()

    def _investigar(self) -> None:
        inv = self.investigando
        if not inv:
            return
        coste = ORO_INVESTIGAR + 0.0005 * self.poblacion     # cuanto más grande, más sabios a sueldo
        if self.oro < coste:
            return
        self.oro -= coste
        rapidez = 1 + 0.5 * self.tiene("escuela") + 0.5 * self.tiene("escritura") + 1.0 * self.tiene("biblioteca")
        inv["dias"] -= rapidez
        if inv["dias"] <= 0:
            self.avances.append(inv["avance"])
            self.investigando = None
            self._cronica("obra", f"Los sabios terminan de estudiar {inv['avance']}: {AVANCES[inv['avance']]['da']}.")

    def avances_posibles(self) -> list[str]:
        return [a for a, d in AVANCES.items() if a not in self.avances and all(self.tiene(p) for p in d["pide"])]

    def _obra_monumento(self) -> None:
        mon = self.monumento
        if not mon:
            return
        mon["dias"] -= 1 / self.factor_obras()
        if mon["dias"] <= 0:
            self.monumentos.append(mon["nombre"])
            self.monumento = None
            texto = f"Se termina {_con_articulo_mon(mon['nombre'])} {_del(self.nombre)}: {MONUMENTOS[mon['nombre']]['da']}."
            self._cronica("obra", texto)
            self.momentos.append(texto)

    def monumentos_posibles(self) -> list[str]:
        return [n for n, d in MONUMENTOS.items() if n not in self.monumentos and NIVEL[self.tipo] >= NIVEL[d["desde"]]
                and (n != "faro" or self.tiene("puerto"))]

    def empezar_monumento(self, nombre: str) -> bool:
        madera, piedra, oro = MONUMENTOS[nombre]["coste"]
        if self.monumento or self.madera < madera or self.piedra < piedra or self.oro < oro:
            return False
        self.madera -= madera
        self.piedra -= piedra
        self.oro -= oro
        self.monumento = {"nombre": nombre, "dias": MONUMENTOS[nombre]["dias"], "total": MONUMENTOS[nombre]["dias"]}
        self._cronica("obra", f"Empieza la obra de {_con_articulo_mon(nombre)}. Durará años.")
        return True

    def _descontento(self) -> None:
        if self.animo < 0.45:
            self.descontento = min(1.0, self.descontento + 0.02)
        else:
            self.descontento = max(0.0, self.descontento - 0.01)
        if self.protesta:
            self.protesta -= 1
        elif self.descontento >= 0.5 and self.rng.random() < 0.1:
            self.protesta = self.rng.randint(3, 8)
            self._cronica("discusion", "La gente sale a la calle a protestar contra el consejo. Se trabaja menos.")
        if self.descontento >= 0.9 and self.rng.random() < 0.05:
            self._revuelta()

    def _revuelta(self) -> None:
        jefe = TIPO_JEFE.get(self.tipo, "alcalde")
        for n in list(self.notables.values()):
            if n.cargo == jefe:
                self._quitar_notable(n, "revuelta")
        self.impuesto = "bajo"
        self.descontento = 0.3
        self.protesta = 0
        texto = f"Revuelta en {_el(self.nombre)}: la gente echa al consejo y baja los impuestos."
        self._cronica("discusion", texto)
        self.momentos.append(texto)

    def _elecciones(self) -> None:
        if self.ano < self.proxima_eleccion:
            return
        self.proxima_eleccion = self.ano + 4
        jefe = TIPO_JEFE.get(self.tipo, "alcalde")
        actual = next((n for n in self.notables.values() if n.cargo == jefe), None)
        if actual and self.animo >= 0.55 and self.rng.random() < 0.6:
            self._cronica("oficio", f"Elecciones: {actual.nombre} sigue de {_jefe(jefe, actual.sexo)} cuatro años más.")
            return
        if actual:
            self._quitar_notable(actual, "elecciones")
        nuevo = self._nuevo_notable(jefe)
        self._cronica("oficio", f"Elecciones: gana {nuevo.nombre}, {'nueva' if nuevo.sexo == 'm' else 'nuevo'} {_jefe(jefe, nuevo.sexo)}.")

    def _sucesos_grandes(self) -> None:
        for suceso, (p, desde) in SUCESOS.items():
            if NIVEL[self.tipo] >= NIVEL[desde] and self.rng.random() < p:
                getattr(self, f"_suceso_{suceso}")()

    def _suceso_inundacion(self) -> None:
        self.comida *= 0.7
        self.edificios["casa"] = max(1, round(self.edificios.get("casa", 0) * 0.97))
        self._cronica("incendio", "El río se desborda e inunda los campos y algunas casas.")

    def _suceso_terremoto(self) -> None:
        especiales = [e for e in self.edificios if e not in ("casa", "muralla") and self.edificios[e]]
        if especiales:
            e = self.rng.choice(especiales)
            self.edificios[e] -= 1
        self.edificios["casa"] = max(1, round(self.edificios.get("casa", 0) * 0.95))
        texto = f"Un terremoto sacude {_el(self.nombre)}. Se hunden casas y edificios."
        self._cronica("incendio", texto)
        self.momentos.append(texto)

    def _suceso_gran_incendio(self) -> None:
        self.edificios["casa"] = max(1, round(self.edificios.get("casa", 0) * 0.97))
        self._cronica("incendio", "Un gran incendio arrasa un barrio entero.")

    def _suceso_hambruna(self) -> None:
        self.hambruna = 2 * m.DIAS_POR_ESTACION
        self._cronica("sequia", "Llega una sequía larga: las cosechas darán la mitad durante dos estaciones.")

    def _suceso_peste(self) -> None:
        self.epidemia = max(self.epidemia, 15)
        self.salud = 0.6
        texto = f"La peste llega {_al(self.nombre)}."
        self._cronica("enfermedad", texto)
        self.momentos.append(texto)

    def _suceso_cometa(self) -> None:
        self.animo = max(0.0, self.animo - 0.15)
        texto = f"Un cometa cruza el cielo sobre {_el(self.nombre)}. Muchos lo toman por un mal presagio."
        self._cronica("hallazgo", texto)
        self.momentos.append(texto)

    def _suceso_mercader(self) -> None:
        oro = round(5 + self.poblacion ** 0.5 * self.factor_comercio())
        self.oro += oro
        self._cronica("hallazgo", f"Llega un mercader de muy lejos y compra {self.especialidad()}: deja {oro} de oro.")

    def _suceso_veta(self) -> None:
        self.edificios["mina"] = self.edificios.get("mina", 0) + 1
        self._cronica("hallazgo", "Unos canteros encuentran una veta: se abre una mina nueva.")

    # ---- consejo: opciones nuevas ----

    def opciones_sociedad(self) -> dict[str, str]:
        ops = {}
        if not self.investigando:
            for a in self.avances_posibles()[:3]:
                ops[f"investigar:{a}"] = f"Investigar {a}: {AVANCES[a]['da']} (cuesta oro mientras se estudia)"
        if not self.monumento:
            for n in self.monumentos_posibles():
                madera, piedra, oro = MONUMENTOS[n]["coste"]
                if self.madera >= madera and self.piedra >= piedra and self.oro >= oro:
                    ops[f"monumento:{n}"] = f"Empezar {_con_articulo_mon(n)}: {MONUMENTOS[n]['da']} (años de obra)"
        for nivel in IMPUESTOS:
            if nivel != self.impuesto:
                efecto = {"bajo": "la gente está más contenta, pero entra menos oro",
                          "normal": "ni mucho oro ni mucho descontento",
                          "alto": "entra mucho más oro, pero la gente se enfada"}[nivel]
                ops[f"impuestos:{nivel}"] = f"Poner los impuestos en {nivel}: {efecto}"
        return ops

    def aplicar_sociedad(self, eleccion: str) -> bool:
        tipo, _, cual = eleccion.partition(":")
        if tipo == "investigar":
            self.investigando = {"avance": cual, "dias": AVANCES[cual]["dias"]}
            self._cronica("obra", f"El consejo pone a los sabios a estudiar {cual}.")
        elif tipo == "monumento":
            self.empezar_monumento(cual)
        elif tipo == "impuestos":
            self.impuesto = cual
            self._cronica("oficio", f"El consejo pone los impuestos en {cual}.")
        else:
            return False
        return True

    def eleccion_sociedad_reglas(self) -> str | None:
        """Lo que harían las reglas con las opciones nuevas, o None para seguir con las de siempre."""
        ops = self.opciones_sociedad()
        if self.descontento > 0.4 and "impuestos:bajo" in ops:
            return "impuestos:bajo"
        if self.descontento < 0.1 and self.impuesto == "bajo" and "impuestos:normal" in ops:
            return "impuestos:normal"
        # Un monumento solo si sobra el doble de lo que cuesta: antes van las casas y la comida.
        for o in ops:
            if o.startswith("monumento:"):
                madera, piedra, oro = MONUMENTOS[o.split(":")[1]]["coste"]
                if self.madera >= 2 * madera and self.piedra >= 2 * piedra and self.rng.random() < 0.5:
                    return o
        return next((o for o in ops if o.startswith("investigar:")), None)

    # ---- edificios nuevos ----

    def edificios_nuevos_posibles(self) -> list[str]:
        return [e for e in EDIFICIOS_NUEVOS if NIVEL[self.tipo] >= NIVEL[DESDE[e]]
                and self.edificios.get(e, 0) < 1 + self.poblacion // 3000]

    def datos_sociedad(self) -> dict:
        return {"oro": round(self.oro), "impuesto": self.impuesto, "avances": list(self.avances),
                "investigando": self.investigando, "descontento": round(self.descontento, 2),
                "protesta": bool(self.protesta), "monumentos": list(self.monumentos), "monumento": self.monumento,
                "especialidad": self.especialidad(), "hambruna": bool(self.hambruna)}


TIPO_JEFE = {"pueblo": "alcalde", "villa": "alcalde", "ciudad": "gobernador"}


def _jefe(cargo: str, sexo: str) -> str:
    if sexo != "m":
        return cargo
    return {"alcalde": "alcaldesa", "gobernador": "gobernadora"}.get(cargo, cargo)


def _el(nombre: str) -> str:
    return f"la {nombre}" if nombre.startswith(("Villa", "Ciudad")) else f"el {nombre}"


def _del(nombre: str) -> str:
    t = _el(nombre)
    return "del" + t[2:] if t.startswith("el ") else "de " + t


def _al(nombre: str) -> str:
    t = _el(nombre)
    return "al" + t[2:] if t.startswith("el ") else "a " + t


def _con_articulo_mon(nombre: str) -> str:
    return {"estatua": "la estatua", "gran templo": "el gran templo", "castillo": "el castillo", "faro": "el faro"}[nombre]
