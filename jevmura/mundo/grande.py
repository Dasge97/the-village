"""Pueblos, villas y ciudades: asentamientos que se simulan en grueso.

No se sigue a cada persona. Se lleva cuánta gente hay de cada edad (0 a 90 años), los recursos,
los edificios y una obra en marcha. Una vez al día del mundo nacen, mueren y trabajan según tasas
fijas; una vez al año todos cumplen años. Hay hasta 8 notables con nombre y cargo, con su vida y su
ficha, y un consejo que cada estación elige qué hacer (con Jev si hay presupuesto; si no, con
reglas). El mapa es el de una aldea con muchas más parcelas para casas y edificios.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import asdict, dataclass, field

from ..motor import modelos as m
from ..motor.mapa import generar_mapa
from ..motor.modelos import Persona, Suceso
from ..motor.nombres import elegir_aspecto, elegir_nombre

EDAD_MAX = 90
TIPOS = {
    "pueblo": {"tope": 400, "notables": 4, "por_casa": 6, "cargos": ["alcalde", "sacerdote", "capitán de la guardia", "maestro de obras"]},
    "villa": {"tope": 4000, "notables": 6, "por_casa": 8, "cargos": ["alcalde", "sacerdote", "capitán de la guardia", "maestro de obras", "mercader", "maestro"]},
    "ciudad": {"tope": 60000, "notables": 8, "por_casa": 10, "cargos": ["gobernador", "sumo sacerdote", "general", "arquitecto", "mercader", "maestro", "sabio", "juez"]},
}
# Edificios: coste (madera, piedra), días de obra y qué dan.
EDIFICIOS = {
    "casa": (25, 12, 2, "sitio para que viva más gente"),
    "granero": (40, 15, 3, "más comida guardada y menos pérdidas"),
    "taller": (30, 25, 3, "más madera y piedra"),
    "mercado": (60, 60, 5, "comercio y mejor ánimo"),
    "templo": (50, 90, 7, "menos enfermedades y mejor ánimo"),
    "dojo": (60, 60, 5, "defensa contra los ataques"),
    "muralla": (20, 60, 3, "un tramo de muralla: defensa"),
    "torre": (30, 80, 4, "defensa contra los ataques"),
    "posada": (50, 30, 4, "atrae a gente de fuera"),
}
PRODUCCION = {  # comida, madera, piedra por trabajador y terreno
    "pradera": (1.0, 1.0, 1.0), "bosque": (0.85, 1.5, 0.9), "desierto": (0.6, 0.6, 1.4),
    "nieve": (0.65, 1.1, 1.1), "pantano": (0.8, 1.0, 0.7),
}
COSECHA = {"primavera": 1.0, "verano": 1.15, "otoño": 1.25, "invierno": 0.45}
NACIMIENTOS = 1.3      # hijos al año por mujer de 18 a 40 años con comida y casa (ajustado: medio millón en ~90 años)
COMIDA_DIA = 1.75      # por persona y día del mundo, como en las aldeas


def mortalidad(edad: int) -> float:
    """Probabilidad de morir en un año del mundo, por edad."""
    if edad < 5:
        return 0.012
    if edad < 55:
        return 0.004
    if edad < 65:
        return 0.025
    if edad < 75:
        return 0.08
    if edad < 85:
        return 0.2
    return 0.45


@dataclass
class Notable:
    id: int
    nombre: str
    sexo: str
    nacimiento: int
    aspecto: str
    caracter: str
    cargo: str


@dataclass
class Grande:
    id: int
    nombre: str
    tipo: str
    bioma: str
    semilla: int
    turno: int = 0
    edades: list = field(default_factory=lambda: [0] * (EDAD_MAX + 1))
    comida: float = 300.0
    madera: float = 150.0
    piedra: float = 100.0
    edificios: dict = field(default_factory=dict)
    salud: float = 1.0
    animo: float = 0.7
    obra: dict | None = None
    notables: dict = field(default_factory=dict)       # id → Notable
    registro: dict = field(default_factory=dict)       # id → Persona: todos los notables que ha habido
    siguiente_id: int = 1
    cronica: list = field(default_factory=list)
    resumenes: list = field(default_factory=list)
    ano_en_curso: dict = field(default_factory=dict)
    consejo: dict = field(default_factory=dict)        # la última decisión del consejo
    epidemia: int = 0                                  # días que le quedan a una epidemia
    fiesta: int = 0
    ataque: dict | None = None
    salientes: int = 0                                 # gente que quiere irse (la recoge el mundo)

    def __post_init__(self):
        self.rng = random.Random(self.semilla * 31 + self.turno)
        self.mapa = generar_mapa(self.semilla, self.bioma)
        self.lotes = lotes(self.mapa)
        self.decisor = None
        if not self.ano_en_curso:
            self.ano_en_curso = self._resumen_vacio()

    # ---- fecha, como en las aldeas ----

    @property
    def dia(self) -> int:
        return self.turno // m.TURNOS_POR_DIA

    @property
    def hora(self) -> float:
        return (self.turno % m.TURNOS_POR_DIA) / m.TURNOS_POR_HORA

    @property
    def ano(self) -> int:
        return self.dia // m.DIAS_POR_ANO + 1

    @property
    def estacion(self) -> str:
        return m.ESTACIONES[(self.dia % m.DIAS_POR_ANO) // m.DIAS_POR_ESTACION]

    def de_noche(self) -> bool:
        return self.hora >= m.HORA_DORMIR or self.hora < m.HORA_DESPERTAR

    # ---- cifras ----

    @property
    def poblacion(self) -> int:
        return sum(self.edades)

    @property
    def tope(self) -> int:
        return TIPOS[self.tipo]["tope"]

    @property
    def capacidad(self) -> int:
        return self.edificios.get("casa", 0) * TIPOS[self.tipo]["por_casa"]

    def trabajadores(self) -> int:
        """Quien trabaja: desde los 14 años (ayudando) hasta los 65."""
        return sum(self.edades[14:66])

    def comida_diaria(self) -> float:
        """Lo que come el asentamiento en un día: los niños, algo más de la mitad que un adulto."""
        ninos = sum(self.edades[:16])
        return (self.poblacion - ninos) * COMIDA_DIA + ninos * COMIDA_DIA * 0.6

    def max_graneros(self) -> int:
        return 1 + self.poblacion // 80

    def defensa(self) -> float:
        e = self.edificios
        return e.get("dojo", 0) * 4 + e.get("torre", 0) * 3 + e.get("muralla", 0) * 0.6 + self.poblacion * 0.02

    # ---- gente que llega y que se va ----

    def sumar(self, edades: list[int]) -> None:
        for edad in edades:
            self.edades[max(0, min(EDAD_MAX, int(edad)))] += 1

    def sacar(self, n: int) -> list[int]:
        """Saca a n personas, sobre todo jóvenes adultos, y devuelve sus edades."""
        candidatos = [e for e in range(16, 41) for _ in range(self.edades[e])]
        self.rng.shuffle(candidatos)
        fuera = candidatos[:n]
        for e in fuera:
            self.edades[e] -= 1
        return fuera

    # ---- turno ----

    def paso(self) -> None:
        self.turno += 1
        if self.turno % m.TURNOS_POR_DIA == 0:
            self._dia()

    def avanzar(self, turnos: int) -> None:
        for _ in range(turnos):
            self.paso()

    def _dia(self) -> None:
        if self.dia % m.DIAS_POR_ANO == 0:
            self._cerrar_ano()
            self.edades = [0] + self.edades[:-1]                 # todos cumplen un año
        if self.dia % m.DIAS_POR_ESTACION == 0:
            self._cronica("estacion", f"Empieza {'la' if self.estacion == 'primavera' else 'el'} {self.estacion}.")
        self._trabajo()
        self._nacimientos_y_muertes()
        self._obras()
        self._sucesos()
        self._notables()
        if self.poblacion > 0.9 * self.tope:
            self.salientes += max(1, round(self.poblacion * 0.004))
        corte = self.turno - m.TURNOS_POR_ANO
        self.cronica = [s for s in self.cronica if s.turno > corte]

    def _trabajo(self) -> None:
        pob = self.poblacion
        w = self.trabajadores()
        fc, fm, fp = PRODUCCION[self.bioma]
        granero = 1 + 0.004 * min(self.edificios.get("granero", 0), self.max_graneros())
        por_campesino = 8.0 * fc * COSECHA[self.estacion] * granero
        necesaria = self.comida_diaria()
        # Se siembra pensando en todo el año (cosecha media 0,96), para guardar para el invierno.
        campesinos = min(w * 0.9, necesaria * 1.3 / max(8.0 * fc * 0.96 * granero, 0.1))
        resto = w - campesinos
        taller = 1 + 0.01 * self.edificios.get("taller", 0)
        self.comida += campesinos * por_campesino - necesaria
        self.madera += resto * 0.55 * 1.0 * fm * taller
        self.piedra += resto * 0.45 * 0.8 * fp * taller
        self.ano_en_curso["producido"]["comida"] += campesinos * por_campesino
        perdida = 0.006 / (1 + 0.05 * self.edificios.get("granero", 0))
        self.comida = max(0.0, self.comida * (1 - perdida))
        tope = pob * 30 + 500
        self.comida, self.madera, self.piedra = min(self.comida, tope), min(self.madera, tope), min(self.piedra, tope)
        mercado = 0.03 if self.edificios.get("mercado") else 0
        templo = 0.02 if self.edificios.get("templo") else 0
        objetivo = 0.55 + mercado + templo + (0.2 if self.fiesta else 0) - (0.25 if self.comida < necesaria else 0)
        self.animo += (objetivo - self.animo) * 0.1
        self.fiesta = max(0, self.fiesta - 1)

    def _nacimientos_y_muertes(self) -> None:
        pob = self.poblacion
        hambre = self.comida < self.comida_diaria()
        sitio = 1.0 if pob < self.capacidad else 0.15 if pob < self.tope else 0.03
        fertiles = sum(self.edades[18:41]) * 0.5
        tasa = NACIMIENTOS * sitio * (0.3 if hambre else 1.0) * (0.6 + 0.6 * self.animo) * self.salud
        nacen = self._redondear(fertiles * tasa / m.DIAS_POR_ANO)
        self.edades[0] += nacen
        self.ano_en_curso["nacimientos"] += nacen
        extra = (2.5 if hambre else 1.0) * (4.0 if self.epidemia else 1.0) / (1 + (0.5 if self.edificios.get("templo") else 0))
        muertes = 0
        for edad in range(EDAD_MAX + 1):
            n = self.edades[edad]
            if n:
                p = 1.0 if edad == EDAD_MAX else min(1.0, mortalidad(edad) * extra / m.DIAS_POR_ANO)
                mueren = min(n, self._redondear(n * p))
                self.edades[edad] -= mueren
                muertes += mueren
        self.ano_en_curso["muertes"]["varias"] += muertes
        self.epidemia = max(0, self.epidemia - 1)

    def _redondear(self, x: float) -> int:
        """Redondeo al azar: 2,3 da 2 el 70 % de las veces y 3 el 30 %."""
        base = math.floor(x)
        return base + (1 if self.rng.random() < x - base else 0)

    # ---- obras ----

    def puede_pagar(self, edificio: str) -> bool:
        madera, piedra, _, _ = EDIFICIOS[edificio]
        return self.madera >= madera and self.piedra >= piedra

    def empezar(self, edificio: str) -> bool:
        if self.obra or not self.puede_pagar(edificio):
            return False
        madera, piedra, dias, _ = EDIFICIOS[edificio]
        self.madera -= madera
        self.piedra -= piedra
        # Las ciudades construyen más deprisa: tienen más manos.
        self.obra = {"edificio": edificio, "dias": max(1, round(dias / (1 + self.trabajadores() / 400))), "total": dias}
        return True

    def _casas(self) -> None:
        """Las casas se hacen a la vez, según las manos que haya: una al día por cada 80 trabajadores.
        (Una a una, una ciudad nunca tendría sitio para crecer.) La obra de `obra` es para el resto."""
        madera, piedra, _, _ = EDIFICIOS["casa"]
        for _ in range(max(1, self.trabajadores() // 80)):
            if not self.falta_casa() or self.madera < madera or self.piedra < piedra:
                break
            self.madera -= madera
            self.piedra -= piedra
            self.edificios["casa"] = self.edificios.get("casa", 0) + 1
            if self.edificios["casa"] % 50 == 0:
                self._cronica("casa", f"Ya hay {self.edificios['casa']} casas.")

    def _obras(self) -> None:
        self._casas()
        if not self.obra:
            return
        self.obra["dias"] -= 1
        if self.obra["dias"] <= 0:
            edificio = self.obra["edificio"]
            self.edificios[edificio] = self.edificios.get(edificio, 0) + 1
            self.obra = None
            if edificio != "casa" or self.edificios["casa"] % 10 == 0:
                n = self.edificios[edificio]
                texto = {"casa": f"Ya hay {n} casas.", "muralla": f"La muralla ya tiene {n} tramos."}
                self._cronica("casa" if edificio == "casa" else "muralla" if edificio == "muralla" else "obra",
                              texto.get(edificio, f"Se termina {_articulo(edificio)}."))

    # ---- sucesos ----

    def _sucesos(self) -> None:
        pob = self.poblacion
        r = self.rng.random
        if r() < 1 / 30:
            self._ataque()
        if not self.epidemia and r() < 1 / (220 * (2 if self.edificios.get("templo") else 1)):
            self.epidemia = self.rng.randint(3, 8)
            self._cronica("enfermedad", "Llega una epidemia. Mucha gente cae enferma.")
            self.salud = 0.8
        else:
            self.salud = min(1.0, self.salud + 0.01)
        if self.edificios.get("casa", 0) > 3 and r() < 1 / 150:
            self.edificios["casa"] -= 1
            self.ano_en_curso["incendios"] += 1
            self._cronica("incendio", "Un incendio destruye una casa.")
        if r() < 1 / 60:
            self.comida += pob * 2
            self._cronica("pesca", "Este año la cosecha viene muy buena.")
        if self.edificios.get("posada") and r() < 0.15:
            llegan = self.rng.randint(1, 3)
            self.sumar(self.rng.randint(18, 35) for _ in range(llegan))
            self.ano_en_curso["llegadas"] += llegan

    def _ataque(self) -> None:
        monstruos, femenino, dibujo = random.Random(self.turno).choice(
            [("slimes", False, "Slime"), ("serpientes", True, "Snake"), ("murciélagos", False, "BlueBat"),
             ("arañas", True, "SpiderRed"), ("lagartos", False, "Lizard"), ("topos gigantes", False, "Mole")])
        fuerza = self.rng.uniform(0.5, 1.5) * (2 + self.poblacion ** 0.5 / 2)
        frenado = fuerza <= self.defensa()
        self.ano_en_curso["ataques"] += 1
        self.ataque = {"turno": self.turno - m.TURNOS_POR_DIA + int(m.HORA_ATAQUE * m.TURNOS_POR_HORA),
                       "monstruo": dibujo, "cuantos": min(8, 2 + int(fuerza // 4)),
                       "entrada": self.mapa.salidas[self.dia % len(self.mapa.salidas)], "frenado": frenado, "guardias": []}
        if frenado:
            self._cronica("ataque", f"Una noche llegan {monstruos}. La guardia {'las' if femenino else 'los'} echa.")
            return
        muertos = min(self.poblacion, self.rng.randint(1, 3) + int(fuerza // 6))
        for _ in range(muertos):
            vivos = [e for e in range(EDAD_MAX + 1) if self.edades[e]]
            self.edades[self.rng.choice(vivos)] -= 1
        robado = min(self.comida, fuerza * 15)
        self.comida -= robado
        self._cronica("ataque", f"Una noche llegan {monstruos} y entran. Mueren {muertos} personas y se llevan {int(robado)} de comida.")

    # ---- notables ----

    def _notables(self) -> None:
        for n in list(self.notables.values()):
            edad = (self.turno - n.nacimiento) / m.TURNOS_POR_ANO
            if self.rng.random() < mortalidad(int(edad)) / m.DIAS_POR_ANO:
                self._quitar_notable(n, "vejez" if edad >= 60 else "enfermedad")
        ocupados = {n.cargo for n in self.notables.values()}
        for cargo in TIPOS[self.tipo]["cargos"][:TIPOS[self.tipo]["notables"]]:
            if cargo not in ocupados and self.poblacion >= 10:
                self._nuevo_notable(cargo)

    def _nuevo_notable(self, cargo: str) -> Notable:
        sexo = self.rng.choice("hm")
        usados = {n.nombre for n in self.notables.values()}
        edad = self.rng.randint(28, 55)
        n = Notable(self.siguiente_id, elegir_nombre(self.rng, sexo, usados), sexo, self.turno - edad * m.TURNOS_POR_ANO,
                    elegir_aspecto(self.rng, sexo), self.rng.choice(m.CARACTERES), cargo)
        self.siguiente_id += 1
        self.notables[n.id] = n
        p = Persona(n.id, n.nombre, sexo, n.nacimiento, n.aspecto, "cargo")
        p.oficio = cargo
        self.registro[n.id] = p
        titulo = _femenino(cargo) if sexo == "m" else cargo
        texto = f"{n.nombre} pasa a ser {'la' if sexo == 'm' else 'el'} {titulo}."
        self._cronica("oficio", texto)
        p.hitos.append([self.turno, "oficio", texto])
        return n

    def _quitar_notable(self, n: Notable, causa: str) -> None:
        p = self.registro[n.id]
        p.salida, p.causa = self.turno, causa
        del self.notables[n.id]
        self._cronica("muerte", f"Muere {n.nombre}, {_femenino(n.cargo) if n.sexo == 'm' else n.cargo}.")

    # ---- consejo ----

    def toca_consejo(self) -> bool:
        return self.turno % (m.TURNOS_POR_DIA * m.DIAS_POR_ESTACION) == m.TURNOS_POR_DIA // 2

    def opciones(self) -> dict[str, str]:
        """Lo que puede decidir el consejo esta estación, cada cosa con lo que consigue."""
        ops = {}
        for edificio, (madera, piedra, _, da) in EDIFICIOS.items():
            if edificio == "muralla" and self.edificios.get("muralla", 0) >= 20:
                continue
            if edificio == "torre" and self.tipo == "pueblo":
                continue
            if edificio == "granero" and self.edificios.get("granero", 0) >= self.max_graneros():
                continue
            if edificio == "taller" and self.edificios.get("taller", 0) >= 1 + self.poblacion // 100:
                continue
            if edificio == "casa" and self.capacidad >= self.tope * 1.05:
                continue
            if edificio in ("mercado", "templo", "dojo", "posada") and self.edificios.get(edificio, 0) >= 1 + self.poblacion // 1500:
                continue
            if not self.obra and self.puede_pagar(edificio):
                ops[f"construir:{edificio}"] = f"Construir {_articulo(edificio)}: {da} (cuesta {madera} de madera y {piedra} de piedra)"
        if self.comida > self.comida_diaria() * 10:
            ops["fiesta"] = "Celebrar una fiesta: sube el ánimo de todos, gasta comida"
        if self.poblacion > 60:
            ops["fundar"] = "Mandar a unos cuantos a fundar una aldea nueva cerca: alivia el sitio y extiende el mundo"
        ops["ahorrar"] = "No hacer nada nuevo esta estación y guardar recursos"
        return ops

    def situacion(self) -> dict:
        """Lo que sabe el consejo al decidir, como datos para Jev."""
        return {
            "asentamiento": f"{self.tipo} de {self.poblacion} habitantes (tope {self.tope}, sitio en casas para {self.capacidad})",
            "terreno": self.bioma, "estacion": self.estacion, "ano": self.ano,
            "recursos": {"comida": int(self.comida), "madera": int(self.madera), "piedra": int(self.piedra)},
            "dias_de_comida": round(self.comida / max(1, self.comida_diaria()), 1),
            "edificios": dict(self.edificios), "obra_en_marcha": self.obra["edificio"] if self.obra else None,
            "defensa": round(self.defensa(), 1), "animo": round(self.animo, 2), "salud": round(self.salud, 2),
            "sucesos": [s.texto for s in self.cronica[-5:]] or ["nada destacable"],
        }

    def falta_casa(self) -> bool:
        return self.poblacion > 0.75 * self.capacidad and self.capacidad < self.tope * 1.05

    def eleccion_reglas(self) -> str:
        ops = self.opciones()
        if self.falta_casa():
            # Si hace falta sitio y no llega para una casa, se ahorra en vez de gastar en otra cosa.
            return "construir:casa" if "construir:casa" in ops else "ahorrar"
        orden = ["construir:granero", "construir:dojo", "construir:templo", "construir:mercado", "construir:muralla",
                 "construir:taller", "construir:torre", "construir:posada", "construir:casa"]
        if self.comida < self.comida_diaria() * 4:
            orden.insert(0, "construir:granero")
        for o in orden:
            if o in ops and (o != "construir:casa" or (self.poblacion > 0.5 * self.capacidad and self.capacidad < self.tope)):
                return o
        return "ahorrar"

    def aplicar(self, eleccion: str, quien: str, confianza: float | None = None) -> None:
        ops = self.opciones()
        if eleccion not in ops:
            eleccion = "ahorrar"
        texto = ops[eleccion]
        if eleccion.startswith("construir:"):
            self.empezar(eleccion.split(":")[1])
        elif eleccion == "fiesta":
            self.comida -= self.comida_diaria() * 2
            self.fiesta = 3
            self._cronica("hallazgo", "El consejo organiza una fiesta. Todo el mundo sale a la calle.")
        elif eleccion == "fundar":
            self.salientes += 10
        self.consejo = {"turno": self.turno, "eleccion": eleccion, "texto": texto.split(":")[0], "quien": quien,
                        "confianza": confianza}

    # ---- crónica y resúmenes ----

    def _cronica(self, tipo: str, texto: str) -> None:
        self.cronica.append(Suceso(self.turno, tipo, texto))

    def _resumen_vacio(self) -> dict:
        return {"nacimientos": 0, "muertes": Counter(), "parejas": 0, "llegadas": 0, "marchas": 0,
                "ataques": 0, "incendios": 0, "producido": Counter()}

    def _cerrar_ano(self) -> None:
        if self.turno == 0:
            return
        r = self.ano_en_curso
        self.resumenes.append({
            "ano": self.ano - 1, "poblacion": self.poblacion, "nacimientos": r["nacimientos"],
            "muertes": dict(r["muertes"]), "parejas": 0, "llegadas": r["llegadas"], "marchas": r["marchas"],
            "ataques": r["ataques"], "incendios": r["incendios"],
            "producido": {k: round(v) for k, v in r["producido"].items()},
            "casas": self.edificios.get("casa", 0), "muralla": self.edificios.get("muralla", 0),
            "comida": round(self.comida), "madera": round(self.madera), "piedra": round(self.piedra),
        })
        self.ano_en_curso = self._resumen_vacio()

    # ---- guardar ----

    def a_datos(self) -> dict:
        d = {k: getattr(self, k) for k in ("id", "nombre", "tipo", "bioma", "semilla", "turno", "edades", "comida",
                                            "madera", "piedra", "edificios", "salud", "animo", "obra", "siguiente_id",
                                            "consejo", "epidemia", "fiesta", "salientes")}
        d["notables"] = [asdict(n) for n in self.notables.values()]
        d["registro"] = [asdict(p) for p in self.registro.values()]
        d["cronica"] = [[s.turno, s.tipo, s.texto] for s in self.cronica]
        d["resumenes"] = self.resumenes
        d["ano_en_curso"] = {**self.ano_en_curso, "muertes": dict(self.ano_en_curso["muertes"]),
                             "producido": dict(self.ano_en_curso["producido"])}
        d["rng"] = self.rng.getstate()
        return d

    @classmethod
    def de_datos(cls, d: dict) -> "Grande":
        datos = {k: d[k] for k in ("id", "nombre", "tipo", "bioma", "semilla", "turno", "edades", "comida", "madera",
                                   "piedra", "edificios", "salud", "animo", "obra", "siguiente_id", "consejo",
                                   "epidemia", "fiesta", "salientes")}
        g = cls(**datos)
        g.notables = {n["id"]: Notable(**n) for n in d["notables"]}
        g.registro = {p["id"]: Persona(**{**p, "padres": tuple(p["padres"]) if p["padres"] else None}) for p in d["registro"]}
        g.cronica = [Suceso(*s) for s in d["cronica"]]
        g.resumenes = d["resumenes"]
        a = d["ano_en_curso"]
        g.ano_en_curso = {**a, "muertes": Counter(a["muertes"]), "producido": Counter(a["producido"])}
        estado = d["rng"]
        g.rng.setstate((estado[0], tuple(estado[1]), estado[2]))
        return g


def nuevo(id: int, nombre: str, tipo: str, bioma: str, semilla: int, turno: int, edades: list[int]) -> Grande:
    """Un pueblo, villa o ciudad recién fundado, con la gente que llega y casas para ella."""
    g = Grande(id, nombre, tipo, bioma, semilla, turno)
    g.sumar(edades)
    g.edificios = {"casa": math.ceil(len(edades) / TIPOS[tipo]["por_casa"]) + 2}
    g.comida = len(edades) * COMIDA_DIA * 20
    g._cronica("estacion", f"Se funda {_articulo_nombre(nombre)} con {len(edades)} personas.")
    for cargo in TIPOS[tipo]["cargos"][:TIPOS[tipo]["notables"]]:
        g._nuevo_notable(cargo)
    return g


def lotes(mapa) -> list[tuple[int, int]]:
    """Parcelas para casas y edificios: las de la aldea y, alrededor, muchas más en la hierba y el
    bosque (se talan los árboles que haya), de la plaza hacia fuera."""
    alto, ancho = len(mapa.casillas), len(mapa.casillas[0])
    muro = {p for t in mapa.tramos for p in t}
    libres = {"hierba", "bosque"}
    elegidos = list(mapa.solares)
    usadas = set()
    for x, y in elegidos:
        usadas.update((xx, yy) for xx in range(x - 2, x + 3) for yy in range(y - 2, y + 2))
    cx, cy = mapa.almacen
    candidatos = sorted(((x, y) for x in range(3, ancho - 3) for y in range(4, alto - 2)),
                        key=lambda p: (math.dist(p, (cx, cy)), p))
    for x, y in candidatos:
        sitio = [(xx, yy) for xx in range(x - 2, x + 3) for yy in range(y - 2, y + 2)]
        if any(p in usadas or p in muro for p in sitio):
            continue
        if all(0 <= yy < alto and 0 <= xx < ancho and mapa.casillas[yy][xx] in libres for xx, yy in sitio):
            elegidos.append((x, y))
            usadas.update(sitio)
            for p in sitio:
                mapa.arboles.pop(p, None)
                mapa.casillas[p[1]][p[0]] = "hierba"
        if len(elegidos) >= 90:
            break
    return elegidos


def _articulo(edificio: str) -> str:
    return {"casa": "una casa", "granero": "un granero", "taller": "un taller", "mercado": "un mercado",
            "templo": "un templo", "dojo": "un dojo", "muralla": "un tramo de muralla", "torre": "una torre",
            "posada": "una posada"}[edificio]


def _articulo_nombre(nombre: str) -> str:
    return f"la {nombre}" if nombre.startswith(("Villa", "Ciudad")) else f"el {nombre}"


def _femenino(cargo: str) -> str:
    return {"alcalde": "alcaldesa", "sacerdote": "sacerdotisa", "capitán de la guardia": "capitana de la guardia",
            "maestro de obras": "maestra de obras", "gobernador": "gobernadora", "sumo sacerdote": "suma sacerdotisa",
            "arquitecto": "arquitecta", "maestro": "maestra", "sabio": "sabia", "juez": "jueza",
            "mercader": "mercader", "general": "generala"}.get(cargo, cargo)
