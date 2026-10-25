"""El mundo grande: todos los asentamientos, que avanzan a la vez, en un mapa de zonas.

Cada aldea es un `Aldea` del motor y se guarda en su propia base de datos: `mundo.db` La aldea,
`mundo-2.db` la Aldea del río y `aldea-<id>.db` las siguientes. Lo que es del mundo (qué hay en
cada zona, de dónde salió cada asentamiento, la crónica del mundo) va en `mundo-global.db`.

Los que se marchan de una aldea llena van a la última aldea que fundó esa aldea; si está llena,
a un pueblo cercano con sitio; si no hay, fundan una aldea nueva en una zona libre de al lado.

Los pueblos, villas y ciudades (`grande.py`) se fundan solos cada día del mundo si se cumple su
condición (por ejemplo, 4 aldeas cerca sin pueblo) y se guardan, en JSON, en `mundo-global.db`.
"""

from __future__ import annotations

import json
import math
import os
import random
import sqlite3
import threading
import time
from collections.abc import Callable

from ..guardado import Guardado
from ..motor import modelos as m
from ..motor.aldea import Aldea, con_articulo
from ..motor.decisores import Decisor
from ..motor.evolucion import INSTRUCCIONES_CONSEJO_ALDEA
from ..motor.nombres import ASPECTOS as _ASPECTOS
from . import zonas
from .grande import Grande
from .grande import nuevo as nuevo_grande
from .presupuesto import DecisorConPresupuesto, Presupuesto
from .relaciones import RIVALIDAD, Relaciones, par

SEGUNDA = "Aldea del río"
SEMILLA_POR_ID = 7777          # la aldea n usa la semilla del mundo + 7777 × (n − 1)
MAX_ALDEAS = 40                 # aldeas detalladas como mucho; después la gente va a las que tengan sitio
CRONICA_MUNDO = 500             # sucesos del mundo que se guardan
VELOCIDADES = [1, 2, 5, 10, 30, 60, 300, 1000]     # las que se pueden elegir en el panel de administración
COSTE_LLAMADA = 0.000056                 # USD por llamada a Jev, para pasar el gasto máximo a llamadas
AJUSTES = {"velocidad": 1, "pausado": False, "usd_dia": 0.30, "jev": True}
DIAS_DE_GASTO = 60                       # días reales de gasto que se guardan
SEGUNDOS_ENTRE_GUARDADOS = 60            # con el mundo acelerado no se guarda más de una vez por minuto
HITOS_POBLACION = [100, 1000, 10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
GRUPO_MINIMO = 25               # gente que se junta en un asentamiento grande antes de irse a otro sitio
# Cuándo se funda cada tipo grande: cuántos del tipo de abajo hacen falta, a qué distancia (en zonas)
# y qué parte de su gente se va al nuevo.
FUNDACION = {
    "pueblo": {"de": "aldea", "cuantos": 4, "radio": 3, "parte": None},
    "villa": {"de": "pueblo", "cuantos": 3, "radio": 4, "parte": 0.15},
    "ciudad": {"de": "villa", "cuantos": 3, "radio": 7, "parte": 0.10},
}
TEXTO_TIPO = {"aldea": "Aldea", "pueblo": "Pueblo", "villa": "Villa", "ciudad": "Ciudad"}
ORDEN_TIPOS = ["aldea", "pueblo", "villa", "ciudad"]
INSTRUCCIONES_CONSEJO = (
    "Eres el consejo de este asentamiento de estilo Japón feudal. Elige qué hacer durante esta estación "
    "para que la gente viva bien y el asentamiento crezca y dure: que no falte comida ni sitio, que haya "
    "defensa contra los monstruos y buen ánimo. Cada opción explica lo que consigue.")


def distancia(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class GuardadoMundo:
    """Lo que es del mundo entero, en JSON, en `mundo-global.db`."""

    def __init__(self, ruta: str):
        self.db = sqlite3.connect(ruta, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS mundo (clave TEXT PRIMARY KEY, valor TEXT)")

    def cargar(self) -> dict | None:
        fila = self.db.execute("SELECT valor FROM mundo WHERE clave = 'mundo'").fetchone()
        return json.loads(fila[0]) if fila else None

    def guardar(self, datos: dict) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO mundo VALUES ('mundo', ?)", (json.dumps(datos),))


def _ruta_segunda(ruta_db: str) -> str:
    base, punto, extension = ruta_db.rpartition(".")
    return f"{base}-2.{extension}" if punto else f"{ruta_db}-2"


class Mundo(Relaciones):
    def __init__(self, ruta_db: str, semilla: int = 0, decisor: Decisor | None = None,
                 segundos_por_turno: float = m.TURNO_SEGUNDOS, hora_inicial: float = 0,
                 presupuesto: Presupuesto | None = None):
        self.ruta_db = ruta_db
        self.carpeta = os.path.dirname(ruta_db) or "."
        self.jev = decisor
        self.presupuesto = presupuesto or Presupuesto()
        self.vigiladas: set[int] = set()        # asentamientos que alguien está mirando en la web
        self.aldeas: dict[int, Aldea] = {}
        self.grandes: dict[int, Grande] = {}    # pueblos, villas y ciudades
        self.guardados: dict[int, Guardado] = {}
        self.meta: dict[int, dict] = {}         # nombre, zona, terreno, fichero y origen de cada uno
        self.hija: dict[int, int] = {}          # a qué aldea va la gente que se marcha de cada una
        self.cronica: list[list] = []           # [turno, texto, id, grande] de los sucesos del mundo
        self.anual: list[dict] = []             # una foto del mundo por año (la del año en curso, al día)
        self.ajustes = dict(AJUSTES)            # los del panel de administración
        self.gasto: dict[str, dict] = {}        # por día real: llamadas a Jev y coste
        self._visto_jev: tuple[int, float] | None = None   # totales de Jev la última vez que se contó el gasto
        self.arrancado = time.time()
        self.guardado_en: float | None = None   # hora real del último guardado
        self.ms_por_turno = 0.0                 # lo que tarda en calcularse un turno (media)
        self._turnos_reales: list[float] = []   # cuándo acabaron los últimos turnos, para medir la velocidad real
        self.global_ = GuardadoMundo(ruta_db.rpartition(".")[0] + "-global.db")   # mundo.db → mundo-global.db
        datos = self.global_.cargar()
        self._iniciar_relaciones(datos)
        if datos:
            self._cargar(datos)
        else:
            self._empezar(semilla, hora_inicial)
        self.segundos_por_turno = segundos_por_turno
        self.cerrojo = threading.Lock()          # la web lee las aldeas mientras el bucle las cambia
        # Se llama tras cada turno con cada aldea y su número.
        self.al_avanzar: list[Callable[[Aldea, int], None]] = []
        self._parar = threading.Event()

    # ---- cargar y empezar ----

    def _ruta(self, fichero: str) -> str:
        return os.path.join(self.carpeta, fichero)

    def _empezar(self, semilla: int, hora_inicial: float) -> None:
        """Primera vez con el mundo grande: La aldea (y la Aldea del río, si ya existía) son las
        primeras. Si no hay nada guardado, empieza un mundo nuevo."""
        principal = Guardado(self.ruta_db)
        aldea = principal.cargar(self.jev) if principal.existe() else Aldea(semilla, self.jev, hora_inicial=hora_inicial)
        self._poner(1, aldea, principal, {"nombre": aldea.nombre, "zona": list(zonas.CENTRO),
                                          "bioma": "pradera", "fichero": os.path.basename(self.ruta_db),
                                          "madre": None, "fundada": 0})
        segunda = Guardado(_ruta_segunda(self.ruta_db))
        if segunda.existe():
            otra = segunda.cargar(self.jev)
            otra.nombre = SEGUNDA
            self._poner(2, otra, segunda, {"nombre": SEGUNDA, "zona": [zonas.CENTRO[0] + 1, zonas.CENTRO[1]],
                                           "bioma": "pradera", "fichero": os.path.basename(_ruta_segunda(self.ruta_db)),
                                           "madre": 1, "fundada": otra.turno})
            self.hija[1] = 2
        else:
            segunda.cerrar()                     # abrirla creó un fichero vacío: se quita
            os.remove(_ruta_segunda(self.ruta_db))

    def _cargar(self, datos: dict) -> None:
        self.hija = {int(k): v for k, v in datos["hija"].items()}
        self.cronica = datos["cronica"]
        self.anual = datos.get("anual", [])
        self.ajustes = {**AJUSTES, **datos.get("ajustes", {})}
        self.gasto = datos.get("gasto", {})
        for clave, d in datos.get("grandes", {}).items():
            self._poner_grande(int(clave), Grande.de_datos(d), datos["asentamientos"][clave])
        for clave, meta in datos["asentamientos"].items():
            if meta.get("tipo", "aldea") != "aldea":
                continue
            guardado = Guardado(self._ruta(meta["fichero"]))
            aldea = guardado.cargar(self.jev)
            aldea.nombre = meta["nombre"]
            self._poner(int(clave), aldea, guardado, meta)

    def _poner(self, id: int, aldea: Aldea, guardado: Guardado, meta: dict) -> None:
        if self.jev is not None:
            aldea.decisor = DecisorConPresupuesto(self.jev, aldea.respaldo, self.presupuesto,
                                                  importante=lambda id=id: id == 1 or id in self.vigiladas)
        self.aldeas[id] = aldea
        self.guardados[id] = guardado
        self.meta[id] = meta

    def _poner_grande(self, id: int, g: Grande, meta: dict) -> None:
        self.grandes[id] = g
        self.meta[id] = meta

    # ---- consultas ----

    def asentamiento(self, id: int):
        """Aldea o Grande con ese número, o None."""
        return self.aldeas.get(id) or self.grandes.get(id)

    @property
    def aldea(self) -> Aldea:
        """La aldea principal, la primera."""
        return self.aldeas[1]

    @property
    def guardado(self) -> Guardado:
        return self.guardados[1]

    @property
    def turno(self) -> int:
        return self.aldeas[1].turno

    def poblacion(self, id: int) -> int:
        return len(self.aldeas[id].habitantes) if id in self.aldeas else self.grandes[id].poblacion

    def tipo(self, id: int) -> str:
        return self.meta[id].get("tipo", "aldea")

    def resumen(self) -> dict:
        """Cuánta gente hay en todo el mundo y en cuántos asentamientos, para el contador de la web."""
        return {"poblacion": sum(self.poblacion(id) for id in self.meta), "asentamientos": len(self.meta)}

    def publico(self) -> dict:
        """El mapa del mundo para la web: zonas descubiertas (con asentamiento o al lado de uno),
        asentamientos y caminos (cada uno con el que lo fundó)."""
        ocupadas = self.zonas_ocupadas()
        semilla = self.aldeas[1].semilla
        vistas = set(ocupadas)
        for z in ocupadas:
            vistas.update(zonas.vecinas(*z))
        return {
            "lado": zonas.LADO,
            "zonas": [{"x": x, "y": y, "bioma": zonas.bioma(semilla, x, y)} for x, y in sorted(vistas)],
            "asentamientos": [{"id": id, "nombre": meta["nombre"], "tipo": self.tipo(id), "zona": meta["zona"],
                               "bioma": meta["bioma"], "poblacion": self.poblacion(id)} for id, meta in self.meta.items()],
            "caminos": [list(c) for c in self._caminos()],
            "alianzas": [list(par(k)) for k in sorted(self.alianzas)],
            "vasallos": [[v, s] for v, s in self.vasallos.items()],
            "rivalidades": [list(par(k)) for k, v in self.relaciones.items() if v <= RIVALIDAD],
            "poblacion": sum(self.poblacion(id) for id in self.meta),
            "sucesos": [self._suceso_publico(s) for s in self.cronica[-60:]],
            "momentos": [self._suceso_publico(s) for s in self.cronica if len(s) > 3 and s[3]],
            "anual": self.anual,
        }

    @staticmethod
    def _suceso_publico(s: list) -> dict:
        return {"turno": s[0], "ano": s[0] // m.TURNOS_POR_ANO + 1, "texto": s[1], "id": s[2]}

    def zonas_ocupadas(self) -> dict[tuple[int, int], int]:
        return {tuple(meta["zona"]): id for id, meta in self.meta.items()}

    # ---- fundar y mudarse ----

    def _zona_libre(self, cerca_de: tuple[int, int]) -> tuple[int, int] | None:
        """La zona libre más cercana, empezando por las de al lado; entre las que están a la misma
        distancia, una al azar (fija para cada turno, para que todo se pueda repetir)."""
        ocupadas = self.zonas_ocupadas()
        rng = random.Random(self.turno * 31 + len(self.aldeas))
        for radio in range(1, zonas.LADO):
            anillo = [(cerca_de[0] + dx, cerca_de[1] + dy) for dx in range(-radio, radio + 1) for dy in range(-radio, radio + 1)
                      if max(abs(dx), abs(dy)) == radio]
            libres = [z for z in anillo if 0 <= z[0] < zonas.LADO and 0 <= z[1] < zonas.LADO and z not in ocupadas]
            if libres:
                return rng.choice(libres)
        return None

    def _nombre_nuevo(self, tipo: str = "aldea") -> str:
        """«Aldea de Mizuno», «Pueblo de Takada»…: el sitio no se repite entre asentamientos. Cuando se
        acaban los nombres, se les añade dónde quedan: «Villa de Mizuno del Norte»."""
        usados = {meta["nombre"].split(" de ", 1)[-1] for meta in self.meta.values()}
        for coletilla in ("", *zonas.COLETILLAS):
            for n in zonas.NOMBRES:
                if f"{n}{coletilla}" not in usados:
                    return f"{TEXTO_TIPO[tipo]} de {n}{coletilla}"
        return f"{TEXTO_TIPO[tipo]} número {len(self.meta) + 1}"

    def fundar(self, madre: int) -> int | None:
        """Una aldea nueva, vacía, en una zona libre junto a `madre`. Devuelve su número."""
        zona = self._zona_libre(tuple(self.meta[madre]["zona"]))
        if zona is None:
            return None
        id = max(self.meta) + 1
        principal = self.aldeas[1]
        terreno = zonas.bioma(principal.semilla, *zona)
        aldea = Aldea(principal.semilla + SEMILLA_POR_ID * (id - 1), None, habitantes=0, bioma=terreno)
        aldea.nombre = SEGUNDA if id == 2 else self._nombre_nuevo()
        aldea.turno = principal.turno
        fichero = os.path.basename(_ruta_segunda(self.ruta_db)) if id == 2 else f"aldea-{id}.db"
        self._poner(id, aldea, Guardado(self._ruta(fichero)), {
            "nombre": aldea.nombre, "zona": list(zona), "bioma": terreno, "fichero": fichero,
            "madre": madre, "fundada": aldea.turno})
        self.hija[madre] = id
        return id

    def fundar_grande(self, tipo: str, cerca_de: tuple[int, int], edades: list[int], fuentes: list[int]) -> int | None:
        """Un pueblo, villa o ciudad nuevo en la zona libre más cercana a `cerca_de`."""
        zona = self._zona_libre(cerca_de)
        if zona is None or not edades:
            return None
        id = max(self.meta) + 1
        semilla = self.aldeas[1].semilla
        terreno = zonas.bioma(semilla, *zona)
        nombre = self._nombre_nuevo(tipo)
        g = nuevo_grande(id, nombre, tipo, terreno, semilla + SEMILLA_POR_ID * (id - 1), self.turno, edades)
        self._poner_grande(id, g, {"nombre": nombre, "tipo": tipo, "zona": list(zona), "bioma": terreno,
                                   "madre": fuentes[0] if fuentes else None, "fuentes": fuentes, "fundada": self.turno})
        return id

    def _grande_con_sitio(self, tipo: str | None, zona, radio: int, menos_de: float = 0.9) -> int | None:
        cerca = [i for i, g in self.grandes.items() if (tipo is None or g.tipo == tipo)
                 and distancia(self.meta[i]["zona"], zona) <= radio and g.poblacion < menos_de * g.tope]
        return min(cerca, key=lambda i: distancia(self.meta[i]["zona"], zona)) if cerca else None

    def _destino(self, origen: int) -> tuple[int | None, bool]:
        """Adónde va quien se marcha de `origen` y si funda una aldea nueva."""
        hija = self.hija.get(origen)
        if hija in self.aldeas and len(self.aldeas[hija].habitantes) < m.POBLACION_MAXIMA:
            return hija, False
        pueblo = self._grande_con_sitio("pueblo", self.meta[origen]["zona"], FUNDACION["pueblo"]["radio"])
        if pueblo is not None:
            return pueblo, False
        if len(self.aldeas) < MAX_ALDEAS:
            nueva = self.fundar(origen)
            if nueva is not None:
                return nueva, True
        zona = self.meta[origen]["zona"]
        con_sitio = [i for i, a in self.aldeas.items() if i != origen and len(a.habitantes) < m.POBLACION_MAXIMA - 2]
        if not con_sitio:
            return None, False
        return min(con_sitio, key=lambda i: math.dist(self.meta[i]["zona"], zona)), False

    def _mudanzas(self) -> None:
        for origen, aldea in list(self.aldeas.items()):
            while aldea.emigrantes:
                e = aldea.emigrantes.pop(0)
                destino, funda = self._destino(origen)
                if destino is None:
                    aldea._hito(e["id"], "marcha", "Se marcha lejos, a un sitio que nadie conoce.")
                    continue
                if destino in self.grandes:
                    g = self.grandes[destino]
                    g.sumar([e["edad"]])
                    g.ano_en_curso["llegadas"] += 1
                    aldea._hito(e["id"], "marcha", f"Se va a vivir al {g.nombre}.")
                    continue
                nueva = self.aldeas[destino]
                nueva.recibir(e, aldea.nombre, funda=funda)
                nombre = con_articulo(nueva.nombre)
                aldea._hito(e["id"], "marcha", f"Se marcha a fundar {nombre}." if funda else f"Se va a vivir a {nombre}.")
                if funda:
                    aldea._cronica("marcha", f"{e['nombre']} funda una aldea nueva: {nombre}.")
                    self.suceso(f"{e['nombre']} sale de {con_articulo(aldea.nombre)} y funda {nombre}.", destino,
                                grande=len(self.aldeas) == 2)

    # ---- crecer: pueblos, villas y ciudades ----

    def _crecer(self) -> None:
        """Una vez al día del mundo: se fundan los pueblos, villas y ciudades que tocan y se reparte la
        gente que sobra en los asentamientos grandes."""
        for tipo, regla in FUNDACION.items():
            self._fundar_tipo(tipo, regla)
        for id, g in list(self.grandes.items()):
            if g.salientes:
                self._repartir(id, g)
        if (self.turno // m.TURNOS_POR_DIA) % m.DIAS_POR_ESTACION == 0:
            self._comercio()
            self._comercio_aldeas()
            self._estacion_relaciones()
        for id, g in self.grandes.items():          # monumentos, revueltas, terremotos…
            for texto in g.momentos:
                self.suceso(texto, id, grande=True)
            g.momentos.clear()
        self._contagios()
        self._anotar_ano()

    def _anotar_ano(self) -> None:
        """Pone al día la foto del año en curso: cuánta gente hay y en qué tipo de asentamiento. Cuando
        el mundo pasa de 100, 1.000, 10.000… personas, es un gran momento."""
        foto = {"ano": self.aldeas[1].ano, "poblacion": 0,
                "asentamientos": {t: 0 for t in ORDEN_TIPOS}, "gente": {t: 0 for t in ORDEN_TIPOS}}
        for id in self.meta:
            n = self.poblacion(id)
            foto["poblacion"] += n
            foto["asentamientos"][self.tipo(id)] += 1
            foto["gente"][self.tipo(id)] += n
        antes = self.anual[-1]["poblacion"] if self.anual else foto["poblacion"]   # sin fotos, no hay hito
        if self.anual and self.anual[-1]["ano"] == foto["ano"]:
            self.anual[-1] = foto
        else:
            self.anual.append(foto)
        for hito in HITOS_POBLACION:
            if antes < hito <= foto["poblacion"]:
                self.suceso(f"El mundo llega a {hito:,d} personas.".replace(",", "."), grande=True)

    def _caminos(self) -> list[tuple[int, int]]:
        return [(otro, id) for id, meta in self.meta.items()
                for otro in {meta.get("madre"), *meta.get("fuentes", [])} if otro in self.meta]

    def _comercio(self) -> None:
        """Cada estación, los pueblos, villas y ciudades unidos por un camino y con mercado se mandan
        caravanas: el que tiene de sobra un recurso manda una parte al que le falta."""
        for a, b in self._caminos():
            ga, gb = self.grandes.get(a), self.grandes.get(b)
            if not ga or not gb or not (ga.edificios.get("mercado") and gb.edificios.get("mercado")):
                continue
            for recurso in ("comida", "madera", "piedra"):
                rico, pobre = (ga, gb) if getattr(ga, recurso) / max(1, ga.poblacion) > getattr(gb, recurso) / max(1, gb.poblacion) else (gb, ga)
                por_rico = getattr(rico, recurso) / max(1, rico.poblacion)
                por_pobre = getattr(pobre, recurso) / max(1, pobre.poblacion)
                if por_rico > 3 * por_pobre + 5:
                    # Aliados, terrenos distintos, la rueda, el puerto y el faro hacen que la caravana valga más.
                    valor = (1.5 if self.aliados(a, b) else 1.0) * (1.3 if ga.bioma != gb.bioma else 1.0)
                    cantidad = round(getattr(rico, recurso) * 0.1 * min(2.0, valor * rico.factor_comercio()))
                    cantidad = min(cantidad, round(getattr(rico, recurso) * 0.3))
                    self.sumar_relacion(a, b, 6)
                    rico.oro += cantidad * 0.02 * (1.3 if ga.bioma != gb.bioma else 1.0)
                    setattr(rico, recurso, getattr(rico, recurso) - cantidad)
                    setattr(pobre, recurso, getattr(pobre, recurso) + cantidad)
                    pobre._cronica("hallazgo", f"Llega una caravana del {rico.nombre} con {cantidad} de {recurso}.")
                    rico._cronica("obra", f"Sale una caravana con {cantidad} de {recurso} hacia el {pobre.nombre}.")

    def _comercio_aldeas(self) -> None:
        """Cada estación, una aldea con mercado manda en caravana lo que tiene casi lleno en el almacén
        a la aldea o pueblo cercano (a 2 zonas o menos) que menos tiene de eso, y vuelve con algo de
        lo que a ella le falta."""
        for id, a in self.aldeas.items():
            if not a.efecto("mercado") or not a.habitantes:
                continue
            zona = self.meta[id]["zona"]
            vecinos = [j for j in self.meta if j != id and distancia(self.meta[j]["zona"], zona) <= 2
                       and self.poblacion(j) > 0]
            if not vecinos:
                continue
            for recurso in ("comida", "madera", "piedra"):
                if getattr(a, recurso) < 0.9 * a.tope(recurso):
                    continue
                destino = min(vecinos, key=lambda j: getattr(self.asentamiento(j), recurso) / max(1, self.poblacion(j)))
                otro = self.asentamiento(destino)
                cantidad = round(getattr(a, recurso) * 0.3)
                setattr(a, recurso, getattr(a, recurso) - cantidad)
                if destino in self.aldeas:
                    otro._guardar(recurso, cantidad)
                else:
                    setattr(otro, recurso, getattr(otro, recurso) + cantidad)
                # A la vuelta trae la mitad en lo que más le falta a la aldea, si el otro tiene de sobra.
                falta = min(("comida", "madera", "piedra"), key=lambda r: getattr(a, r) / a.tope(r))
                traido = 0
                if falta != recurso and getattr(otro, falta) > 2 * cantidad:
                    traido = cantidad // 2
                    setattr(otro, falta, getattr(otro, falta) - traido)
                    a._guardar(falta, traido)
                vuelta = f" y vuelve con {traido} de {falta}" if traido else ""
                a._cronica("caravana", f"Sale una caravana del mercado con {cantidad} de {recurso} hacia {con_articulo(otro.nombre)}{vuelta}.")
                if destino in self.aldeas:
                    otro._cronica("caravana", f"Llega una caravana de {con_articulo(a.nombre)} con {cantidad} de {recurso}.")
                else:
                    otro._cronica("hallazgo", f"Llega una caravana de {con_articulo(a.nombre)} con {cantidad} de {recurso}.")
                break                                 # una caravana por estación

    def _contagios(self) -> None:
        """Una epidemia puede pasar a los pueblos, villas y ciudades de alrededor (a 2 zonas o menos)."""
        enfermos = [i for i, g in self.grandes.items() if g.epidemia]
        for i in enfermos:
            for j, g in self.grandes.items():
                if j != i and not g.epidemia and distancia(self.meta[i]["zona"], self.meta[j]["zona"]) <= 2:
                    if random.Random(self.turno * 7 + i * 31 + j).random() < 0.04:
                        g.epidemia = random.Random(self.turno + j).randint(3, 6)
                        g._cronica("enfermedad", f"La epidemia del {self.grandes[i].nombre} llega hasta aquí.")

    def _fundar_tipo(self, tipo: str, regla: dict) -> None:
        de, radio = regla["de"], regla["radio"]
        abajo = [i for i in self.meta if self.tipo(i) == de]
        ya = [i for i in self.meta if self.tipo(i) == tipo]
        for i in abajo:
            zona = self.meta[i]["zona"]
            if any(distancia(self.meta[j]["zona"], zona) <= radio for j in ya):
                continue
            grupo = [j for j in abajo if distancia(self.meta[j]["zona"], zona) <= radio
                     and not any(distancia(self.meta[k]["zona"], self.meta[j]["zona"]) <= radio for k in ya)]
            if len(grupo) < regla["cuantos"]:
                continue
            centro = (round(sum(self.meta[j]["zona"][0] for j in grupo) / len(grupo)),
                      round(sum(self.meta[j]["zona"][1] for j in grupo) / len(grupo)))
            edades = []
            if tipo == "pueblo":
                for j in grupo:
                    edades += self._sacar_de_aldea(j, 3)
                rng = random.Random(self.turno)
                edades += [rng.randint(16, 40) for _ in range(30)]   # y gente de fuera
            else:
                for j in grupo:
                    g = self.grandes[j]
                    edades += g.sacar(round(g.poblacion * regla["parte"]))
            nuevo = self.fundar_grande(tipo, centro, edades, grupo)
            if nuevo is None:
                return
            ya.append(nuevo)
            articulo = "la" if tipo in ("villa", "ciudad") else "el"
            if sum(1 for i in self.meta if self.tipo(i) == tipo) == 1:
                primero = {"pueblo": "el primer pueblo", "villa": "la primera villa", "ciudad": "la primera ciudad"}[tipo]
                self.suceso(f"Nace {primero} del mundo: {articulo} {self.meta[nuevo]['nombre']}, con {len(edades)} personas.",
                            nuevo, grande=True)
            else:
                self.suceso(f"Nace {articulo} {self.meta[nuevo]['nombre']}, con {len(edades)} personas.", nuevo,
                            grande=tipo == "ciudad")

    def _sacar_de_aldea(self, id: int, n: int) -> list[int]:
        """Hasta n jóvenes solteros de una aldea se van al pueblo nuevo. Devuelve sus edades."""
        aldea = self.aldeas[id]
        jovenes = [h for h in aldea.habitantes.values() if h.oficio and h.pareja is None
                   and m.EDAD_ADULTA <= h.edad(aldea.turno) <= 35 and not h.fuera_hasta][:n]
        edades = []
        for h in jovenes:
            edades.append(int(h.edad(aldea.turno)))
            aldea._hito(h.id, "marcha", "Se va a vivir al pueblo nuevo que se funda cerca.")
            aldea._cronica("marcha", f"{h.nombre} se va a vivir al pueblo nuevo que se funda cerca.")
            aldea._quitar(h, "marcha")
        return edades

    def _repartir(self, id: int, g: Grande) -> None:
        """La gente que sobra en un pueblo, villa o ciudad: a otro del mismo tipo con sitio, a
        fundar uno nuevo si son bastantes o, si son pocos y es un pueblo, a fundar una aldea."""
        # La gente que quiere irse se junta hasta formar un grupo; uno pequeño, a veces, funda una aldea.
        zona = self.meta[id]["zona"]
        if g.salientes < GRUPO_MINIMO:
            if (g.tipo == "pueblo" and g.salientes >= 8 and len(self.aldeas) < MAX_ALDEAS
                    and random.Random(self.turno + id).random() < 0.1):
                self._aldea_desde(id, g, g.salientes)
                g.salientes = 0
            return
        n = min(g.salientes, 400)
        g.salientes = 0
        otro = self._grande_con_sitio(g.tipo, zona, 6, menos_de=0.7)
        edades = g.sacar(n)
        if otro is not None and otro != id:
            self.grandes[otro].sumar(edades)
            self.grandes[otro].ano_en_curso["llegadas"] += len(edades)
            g.ano_en_curso["marchas"] += len(edades)
            return
        # Sin sitio en otro del mismo tipo: fundar uno nuevo si hay una zona libre cerca; si no, a una
        # villa o ciudad cercana con sitio (tienen topes grandes).
        libre = self._zona_libre(tuple(zona))
        if len(edades) >= 20 and libre is not None and distancia(libre, zona) <= 3:
            nuevo = self.fundar_grande(g.tipo, tuple(zona), edades, [id])
            if nuevo is not None:
                g.ano_en_curso["marchas"] += len(edades)
                self.suceso(f"Gente del {g.nombre} funda el {self.meta[nuevo]['nombre']}.", nuevo)
                return
        mayores = [i for i, o in self.grandes.items() if ORDEN_TIPOS.index(o.tipo) > ORDEN_TIPOS.index(g.tipo)
                   and distancia(self.meta[i]["zona"], zona) <= 8 and o.poblacion < 0.9 * o.tope]
        if mayores:
            destino = min(mayores, key=lambda i: distancia(self.meta[i]["zona"], zona))
            self.grandes[destino].sumar(edades)
            self.grandes[destino].ano_en_curso["llegadas"] += len(edades)
            g.ano_en_curso["marchas"] += len(edades)
            return
        g.sumar(edades)                    # no hay adónde ir: se quedan

    def _aldea_desde(self, id: int, g: Grande, n: int) -> None:
        """Unos cuantos de un pueblo fundan una aldea nueva cerca."""
        nueva = self.fundar(id)
        if nueva is None:
            return
        aldea = self.aldeas[nueva]
        rng = random.Random(self.turno + id)
        for edad in g.sacar(min(max(n, 4), 8)):
            sexo = rng.choice("hm")
            aldea.recibir({"id": 0, "nombre": "", "sexo": sexo, "edad": edad, "oficio": None,
                           "caracter": rng.choice(m.CARACTERES), "aspecto": rng.choice(_ASPECTOS[sexo])},
                          g.nombre, funda=not aldea.habitantes)
        self.suceso(f"Gente del {g.nombre} funda {con_articulo(aldea.nombre)}.", nueva)

    def _consejos(self) -> None:
        """Cada estación, el consejo de cada aldea, pueblo, villa o ciudad elige qué hacer: con Jev
        si queda presupuesto de consejos; si no, con las reglas."""
        for id, a in self.aldeas.items():
            if not a.toca_consejo():
                continue
            eleccion, quien, confianza = a.eleccion_consejo_reglas(), "reglas", None
            if self.jev is not None and hasattr(self.jev, "elegir"):
                if self.presupuesto.gastar("consejos", importante=id == 1 or id in self.vigiladas):
                    try:
                        eleccion, confianza = self.jev.elegir(a.situacion_consejo(), a.opciones_consejo(),
                                                              INSTRUCCIONES_CONSEJO_ALDEA)
                        quien = "jev"
                    except Exception:
                        quien = "respaldo"
                else:
                    quien = "presupuesto"
            a.aplicar_consejo(eleccion, quien, confianza)
        for id, g in self.grandes.items():
            if not g.toca_consejo():
                continue
            opciones = g.opciones()
            eleccion, quien, confianza = g.eleccion_reglas(), "reglas", None
            if self.jev is not None and hasattr(self.jev, "elegir"):
                if self.presupuesto.gastar("consejos", importante=id in self.vigiladas):
                    try:
                        eleccion, confianza = self.jev.elegir(g.situacion(), opciones, INSTRUCCIONES_CONSEJO)
                        quien = "jev"
                    except Exception:
                        quien = "respaldo"
                else:
                    quien = "presupuesto"
            g.aplicar(eleccion, quien, confianza)

    def suceso(self, texto: str, id: int | None = None, grande: bool = False) -> None:
        """Un suceso del mundo, para la historia del mundo. `grande`: de los que marcan una época (la
        primera villa, la primera ciudad, el mundo llega a 10.000 personas…)."""
        self.cronica.append([self.turno, texto, id, int(grande)])
        if len(self.cronica) > CRONICA_MUNDO:    # se olvida el suceso más viejo, pero nunca un gran momento
            viejo = next((i for i, c in enumerate(self.cronica) if len(c) < 4 or not c[3]), 0)
            del self.cronica[viejo]

    # ---- avanzar y guardar ----

    def paso(self) -> None:
        with self.cerrojo:
            for aldea in self.aldeas.values():
                aldea.paso()
            for g in self.grandes.values():
                g.paso()
            self._mudanzas()
            self._consejos()
            if self.turno % m.TURNOS_POR_DIA == 1:
                self._crecer()
            self._contar_gasto()
            if self.turno % m.TURNOS_ENTRE_DECISIONES == 0 and (
                    self.guardado_en is None or time.time() - self.guardado_en >= SEGUNDOS_ENTRE_GUARDADOS):
                self.guardar()
        for funcion in self.al_avanzar:
            for id, asentamiento in list(self.aldeas.items()) + list(self.grandes.items()):
                funcion(asentamiento, id)

    def guardar(self) -> None:
        for id, aldea in self.aldeas.items():
            self.guardados[id].guardar(aldea)
        self.global_.guardar({
            "asentamientos": {str(id): meta for id, meta in self.meta.items()},
            "grandes": {str(id): g.a_datos() for id, g in self.grandes.items()},
            "hija": {str(k): v for k, v in self.hija.items()},
            "cronica": self.cronica,
            "anual": self.anual,
            "ajustes": self.ajustes,
            "gasto": self.gasto,
            **self.datos_relaciones(),
        })
        self.guardado_en = time.time()

    def ejecutar(self) -> None:
        siguiente = time.monotonic()
        while not self._parar.is_set():
            if self.ajustes["pausado"]:
                self._parar.wait(0.5)
                siguiente = time.monotonic()
                continue
            inicio = time.monotonic()
            self.paso()
            fin = time.monotonic()
            self.ms_por_turno = self.ms_por_turno * 0.9 + (fin - inicio) * 1000 * 0.1
            self._turnos_reales = [t for t in self._turnos_reales[-299:] if fin - t <= 60] + [fin]
            siguiente = max(siguiente + self.segundos_por_turno, time.monotonic())
            self._parar.wait(max(0.0, siguiente - time.monotonic()))
        with self.cerrojo:
            self.guardar()

    # ---- administración ----

    def aplicar_ajustes(self) -> None:
        """Pasa los ajustes a la marcha del mundo: segundos por turno y llamadas a Jev al día.
        El gasto máximo se reparte como siempre: 60 % para los vecinos y 40 % para los consejos."""
        self.segundos_por_turno = m.TURNO_SEGUNDOS / self.ajustes["velocidad"]
        llamadas = self.ajustes["usd_dia"] / COSTE_LLAMADA
        self.presupuesto.cambiar({"vecinos": round(llamadas * 0.6), "consejos": round(llamadas * 0.4)})
        self.presupuesto.activo = self.ajustes["jev"]

    def turnos_por_segundo(self) -> float:
        """Turnos de verdad por segundo en el último minuto (con el mundo muy acelerado, el
        ordenador puede no llegar a la velocidad pedida)."""
        t = self._turnos_reales
        if len(t) < 2:
            return 0.0
        return (len(t) - 1) / max(0.001, t[-1] - t[0])

    def _contar_gasto(self) -> None:
        """Suma al día real de hoy las llamadas y el coste de Jev desde la última vez."""
        jev = self.jev
        if jev is None or not hasattr(jev, "llamadas"):
            return
        ahora = (jev.llamadas, jev.coste)
        if self._visto_jev is not None:
            hoy = time.strftime("%Y-%m-%d")
            dia = self.gasto.setdefault(hoy, {"llamadas": 0, "coste": 0.0})
            dia["llamadas"] += max(0, ahora[0] - self._visto_jev[0])
            dia["coste"] += max(0.0, ahora[1] - self._visto_jev[1])
            for viejo in sorted(self.gasto)[:-DIAS_DE_GASTO]:
                del self.gasto[viejo]
        self._visto_jev = ahora

    def parar(self) -> None:
        self._parar.set()
