"""La aldea: estado del mundo y cálculo de cada turno.

En cada turno las reglas mueven a los habitantes, actualizan sus necesidades y aplican el efecto
de lo que están haciendo. El decisor (Jev o las reglas) solo interviene cuando a un habitante
adulto le toca decidir: cada 30 turnos mientras está despierto. Las decisiones de los adultos
se reparten al amanecer para que no coincidan en el mismo turno.

Lo urgente no pasa por el decisor: dormir de noche, comer con hambre y descansar sin energía.

Una vez al día se calculan los sucesos lentos: estaciones, nacimientos, muertes por vejez,
enfermedades, incendios, calefacción en invierno y llegada de forasteros. Los monstruos atacan
algunas noches a las 2:00.
"""

from __future__ import annotations

import math
import random
from collections import Counter

from . import modelos as m
from .decisores import Decision, Decisor, DecisorReglas, EstadoAldea, Opcion, Situacion
from .caminos import Caminos
from .evolucion import EDIFICIOS, ETAPAS, Evolucion, coste_obra
from .mapa import generar_mapa
from .modelos import Casa, Habitante, Obra, Persona, Suceso
from .nombres import elegir_aspecto, elegir_nombre

VELOCIDAD = 3.0                  # casillas por turno
PECES_MAX = 150.0
REGENERACION_PECES = 0.03        # por turno
CRECIMIENTO_ARBOL = 1 / (3 * m.DIAS_POR_ANO)   # por día: un árbol tarda 3 años en volver a crecer
TURNOS_POR_ARBOL = 60            # cortar un árbol lleva 4 horas
MADERA_POR_ARBOL = 6
LENA_INVIERNO = 1.5              # madera por casa ocupada y día de invierno
COMIDA_POR_RACION = 1.0
HAMBRE_POR_RACION = 35.0
HAMBRE_URGENTE = 55.0
ESPERA_CAMBIO_OFICIO = 3 * m.TURNOS_POR_DIA    # tras cambiar de oficio, 3 días sin poder volver a cambiar
DIFERENCIA_EDAD_PAREJA = 12
OLVIDO_DIARIO = 0.97             # cada día las relaciones se acercan un 3 % a 0
HISTORIAL = 5                    # decisiones que recuerda cada habitante, para su ficha
CANSANCIO_TRABAJO = 0.04        # ánimo que baja cada turno de trabajo
ALMACEN_MAX ={"comida": 400.0, "madera": 250.0, "piedra": 250.0}

# Comida que da cada turno de trabajo en el campo, según la estación.
COSECHA = {"primavera": 0.03, "verano": 0.05, "otoño": 0.07, "invierno": 0.0}
PESCA = 0.045
PIEDRA = 0.05

# Energía que gasta (positivo) o recupera (negativo) cada acción por turno.
GASTO_ENERGIA = {"dormir": -0.7, "descansar": -0.5, "trabajar": 0.3, "construir": 0.4,
                 "ayudar": 0.3, "jugar": 0.1}
ACCIONES_LARGAS = {"trabajar", "construir", "ayudar", "descansar", "jugar"}

# Monstruos del paquete de gráficos: nombre, si es femenino y carpeta de su dibujo en el paquete.
MONSTRUOS = [("slimes", False, "Slime"), ("serpientes", True, "Snake"), ("murciélagos", False, "BlueBat"),
             ("arañas", True, "SpiderRed"), ("lagartos", False, "Lizard"), ("topos gigantes", False, "Mole")]
TURNOS_ATAQUE_VISIBLE = 20      # cuánto se ve un ataque en el mapa: 20 turnos, algo más de 3 minutos reales


def con_articulo(nombre: str) -> str:
    """«la Aldea del río», pero «La aldea» tal cual: para usar el nombre en mitad de una frase."""
    return nombre if nombre.lower().startswith("la ") else f"la {nombre}"


def clave(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def limitar(v: float) -> float:
    return 0.0 if v < 0 else 100.0 if v > 100 else v


class Aldea(Evolucion):
    ALMACEN_MAX = ALMACEN_MAX

    def __init__(self, semilla: int = 0, decisor: Decisor | None = None, habitantes: int = 8,
                 hora_inicial: float = 0, bioma: str = "pradera"):
        self.semilla = semilla
        self.bioma = bioma
        self.rng = random.Random(semilla)
        self.mapa = generar_mapa(semilla, bioma)
        self.caminos = Caminos(self.mapa)
        self.respaldo = DecisorReglas(random.Random(semilla + 1))
        self.decisor = decisor or self.respaldo
        self.turno = 0
        self.habitantes: dict[int, Habitante] = {}
        self.siguiente_id = 1
        self.casas: list[Casa] = []
        self.comida = 60.0
        self.madera = 30.0
        self.piedra = 10.0
        self.peces = PECES_MAX
        self.muralla = 0
        self.obra: Obra | None = None
        self._iniciar_evolucion()
        self.relaciones: dict[tuple[int, int], float] = {}
        self.cronica: list[Suceso] = []
        self.resumenes: list[dict] = []
        self.registro: dict[int, Persona] = {}     # todos los que han vivido aquí, para el árbol genealógico
        self.sequia = False
        self.buena_pesca = False
        self.decisiones: Counter = Counter()     # decisiones tomadas por "jev", "reglas" o "respaldo"
        self.fallos_seguidos = 0
        self.ano_en_curso = self._resumen_vacio()
        self.ataque: dict | None = None          # el último ataque, para dibujarlo; no se guarda
        self.nombre = "La aldea"
        # Los que se acaban de marchar. El mundo los recoge en cada paso y los lleva a otra aldea.
        self.emigrantes: list[dict] = []
        for _ in range(3):
            self._nueva_casa()
        # El primer día puede empezar a otra hora que medianoche, por ejemplo por la mañana para
        # que quien entre a mirar un mundo recién creado vea a los habitantes despiertos.
        self.turno = int(hora_inicial * m.TURNOS_POR_HORA)
        self._poblar(habitantes)
        if not self.de_noche():
            self._repartir_decisiones()

    # ---- tiempo ----

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

    # ---- turno ----

    def paso(self) -> None:
        self.turno += 1
        t = self.turno % m.TURNOS_POR_DIA
        if t == 0:
            self._nuevo_dia()
        if t == m.HORA_ATAQUE * m.TURNOS_POR_HORA:
            self._ataque()
        if t == m.HORA_DESPERTAR * m.TURNOS_POR_HORA:
            self._repartir_decisiones()
        self.peces = min(PECES_MAX, self.peces + REGENERACION_PECES)
        for h in list(self.habitantes.values()):
            if h.id in self.habitantes:
                self._turno_habitante(h)

    def avanzar(self, turnos: int) -> None:
        for _ in range(turnos):
            self.paso()

    def _turno_habitante(self, h: Habitante) -> None:
        if h.fuera_hasta:
            if self.turno < h.fuera_hasta:
                return
            self._vuelve_de_explorar(h)
        self._necesidades(h)
        if h.salud <= 0:
            causa = "hambre" if h.hambre >= 90 else "enfermedad" if h.enfermo_hasta > self.turno else "agotamiento"
            self._morir(h, causa)
            return

        adulto = h.adulto(self.turno)
        if self.de_noche():
            if h.accion not in ("dormir", "explorar", "marcharse"):
                self._poner(h, "dormir", "reglas", "Es de noche", duracion=10**9)
        else:
            if h.accion == "dormir":
                self._por_defecto(h)
            if not self._urgencia(h):
                if adulto and self.turno >= h.proxima_decision:
                    self._decidir(h)
                elif self.turno >= h.fin_accion:
                    self._por_defecto(h)
        self._mover_y_actuar(h)

    def _necesidades(self, h: Habitante) -> None:
        h.hambre = min(100.0, h.hambre + (0.1 if h.accion == "dormir" else 0.17))
        gasto = GASTO_ENERGIA.get(h.accion, 0.1)
        if h.accion == "trabajar" and h.oficio == "cantero":
            gasto = 0.5
        h.energia = limitar(h.energia - gasto)
        salud = 0.0
        if h.hambre >= 90:
            salud -= 0.08
        if h.energia <= 0:
            salud -= 0.05
        if h.enfermo_hasta > self.turno:
            salud -= 0.04
        if salud == 0.0 and h.hambre < 60:
            salud = (0.06 if h.accion in ("dormir", "descansar") else 0.03) * (1 + 0.5 * self.efecto("pozo"))
        h.salud = limitar(h.salud + salud)
        h.animo += ((50 + 10 * self.efecto("templo") - h.animo) * 0.002 - (0.05 if h.hambre > 70 else 0.0)
                    - (CANSANCIO_TRABAJO if h.accion in ("trabajar", "construir") else 0.0))
        h.animo = limitar(h.animo)

    def _urgencia(self, h: Habitante) -> bool:
        if h.decidido_por == "urgencia" and self.turno < h.fin_accion:
            if h.accion == "descansar" and h.energia >= 60 and h.salud > 40:
                h.fin_accion = self.turno
                return False
            return True
        if h.hambre >= HAMBRE_URGENTE and self.comida >= COMIDA_POR_RACION:
            self._poner(h, "comer", "urgencia", "Tiene hambre", duracion=60)
            return True
        if h.energia <= 10 or h.salud <= 30:
            self._poner(h, "descansar", "urgencia", "No puede más", duracion=10**9)
            return True
        return False

    def _por_defecto(self, h: Habitante) -> None:
        if h.adulto(self.turno):
            self._poner(h, "trabajar", "reglas", "Toca trabajar")
        else:
            self._poner(h, "jugar", "reglas", "Es un niño")

    def _repartir_decisiones(self) -> None:
        adultos = [h for h in self.habitantes.values() if h.adulto(self.turno) and not h.fuera_hasta]
        for i, h in enumerate(sorted(adultos, key=lambda h: h.id)):
            h.proxima_decision = self.turno + i * m.TURNOS_ENTRE_DECISIONES // max(len(adultos), 1)

    # ---- decisiones ----

    def _decidir(self, h: Habitante) -> None:
        situacion = self.situacion(h)
        try:
            decision = self.decisor.decidir(situacion)
            if decision.opcion not in situacion.opciones:
                raise ValueError(f"opción fuera de la lista: {decision.opcion.id}")
            # Un decisor con presupuesto dice quién decidió de verdad: Jev o la regla («presupuesto»).
            quien = getattr(self.decisor, "quien", self.decisor.nombre)
            self.fallos_seguidos = 0
        except Exception:
            if self.decisor is self.respaldo:
                raise
            decision = self.respaldo.decidir(situacion)
            quien = "respaldo"
            self.fallos_seguidos += 1
        self.decisiones[quien] += 1
        h.proxima_decision = self.turno + m.TURNOS_ENTRE_DECISIONES
        self._aplicar(h, decision, quien)

    def situacion(self, h: Habitante) -> Situacion:
        """Lo que sabe un habitante al decidir, con sus opciones ya calculadas."""
        estado = self.estado()
        pareja = self.habitantes.get(h.pareja) if h.pareja else None
        relaciones = sorted(
            ((o.nombre, round(self.relacion(h.id, o.id))) for o in self.habitantes.values() if o.id != h.id),
            key=lambda r: -abs(r[1]))[:4]
        return Situacion(
            nombre=h.nombre, edad=int(h.edad(self.turno)), sexo=h.sexo, caracter=h.caracter,
            oficio=h.oficio or "", hambre=round(h.hambre), energia=round(h.energia),
            salud=round(h.salud), animo=round(h.animo), pareja=pareja.nombre if pareja else None,
            relaciones=tuple(relaciones), aldea=estado, ano=self.ano, estacion=self.estacion,
            hora=int(self.hora), sucesos=tuple(s.texto for s in self.cronica[-5:]),
            opciones=tuple(self._opciones(h, estado)),
        )

    def estado(self) -> EstadoAldea:
        adultos = [h for h in self.habitantes.values() if h.oficio]
        oficios = Counter(h.oficio for h in adultos)
        poblacion = len(self.habitantes)
        dias_comida = self.comida / max(poblacion * 1.75, 1)
        guardias = max(1, round(poblacion / 6))
        necesarios = []
        if dias_comida < 6:
            necesarios.append("pescador" if self.estacion in ("otoño", "invierno")
                              or oficios["campesino"] > 2 * oficios["pescador"] else "campesino")
        if oficios["guardia"] < guardias:
            necesarios.append("guardia")
        falta_casa = self._falta_casa()
        # Lo que cuesta la siguiente obra pendiente: una casa si hace falta, si no un tramo de muralla.
        # Si no llega para pagarla, falta quien saque madera o piedra (antes se pedía cantero solo
        # por debajo de 15 de piedra, y con 15-19 la muralla, que cuesta 20, no se empezaba nunca).
        pendiente = "casa" if falta_casa else "muralla" if self.muralla < m.TRAMOS_MURALLA else None
        siguiente = None if pendiente else self.obra_evolucion(pagar=False)
        coste = (m.OBRAS[pendiente] if pendiente else self._coste_candidata(*siguiente) if siguiente
                 else {"madera": 0, "piedra": 0})
        if self.madera < self._lena_necesaria() + coste["madera"]:
            necesarios.append("leñador")
        if self.piedra < coste["piedra"]:
            necesarios.append("cantero")
        obra = None
        if self.obra:
            obra = {"casa": "una casa nueva", "reconstruir": "reconstruir una casa quemada",
                    "muralla": "un tramo de muralla"}.get(self.obra.tipo) or self.nombre_obra(self.obra)
        return EstadoAldea(
            poblacion=poblacion, comida=int(self.comida), madera=int(self.madera),
            piedra=int(self.piedra), dias_comida=round(dias_comida, 1),
            plazas_libres=self._plazas_libres(), oficios=dict(oficios),
            oficios_necesarios=tuple(necesarios), guardias_necesarios=guardias,
            llenos=tuple(r for r in ALMACEN_MAX if self._lleno(r)),
            muralla=self.muralla, obra=obra, etapa=f"{self.etapa}: {ETAPAS[self.etapa]}",
            edificios=tuple(EDIFICIOS[n]["nombre"] for n in self.edificios),
        )

    def _opciones(self, h: Habitante, estado: EstadoAldea) -> list[Opcion]:
        # Cada descripción dice qué consigue la opción, para que Jev pueda comparar.
        recurso = m.RECURSO_OFICIO.get(h.oficio or "")
        if recurso is None:
            trabajo = "vigila la muralla; cuantos más guardias, mejor se frenan los ataques de noche"
        elif recurso in estado.llenos:
            trabajo = f"el almacén de {recurso} está lleno, así que no sirve de nada"
        else:
            trabajo = f"produce {recurso}; con el ánimo alto se produce más, y trabajar sin parar baja el ánimo"
        ops = [Opcion("trabajar", "trabajar", f"Trabajar de {h.de_oficio()}: {trabajo}")]
        if self.turno - h.cambio_oficio >= ESPERA_CAMBIO_OFICIO:
            for oficio in m.OFICIOS:
                if oficio != h.oficio:
                    falta = " (a la aldea le hace falta)" if oficio in estado.oficios_necesarios else ""
                    ops.append(Opcion(f"oficio:{oficio}", "oficio",
                                      f"Cambiar de oficio a {h.de_oficio(oficio)}{falta}; "
                                      f"después no podrá volver a cambiar en 3 días"))
        obra = self._obra_posible()
        if obra == "seguir":
            ops.append(Opcion("construir", "construir",
                              f"Seguir construyendo {estado.obra}: si nadie construye, la obra no se termina"))
        elif isinstance(obra, tuple):
            tipo, cual = obra
            ops.append(Opcion(f"construir:{tipo}:{cual}", "construir", self.texto_obra(tipo, cual)))
        elif obra:
            ops.append(Opcion(f"construir:{obra}", "construir", {
                "casa": "Empezar una casa nueva: hace falta para que las familias tengan hijos",
                "reconstruir": "Reconstruir la casa quemada: hay vecinos sin casa propia",
                "muralla": "Construir un tramo de muralla: ayuda a frenar los ataques de monstruos",
            }[obra]))
        ops.append(Opcion("descansar", "descansar", "Ir a casa a descansar: recupera energía y salud"))
        if self.comida >= COMIDA_POR_RACION:
            ops.append(Opcion("comer", "comer", "Comer del almacén: baja el hambre"))
            ops.append(Opcion("quitar", "quitar",
                              "Coger comida del almacén a escondidas: quita el hambre, pero si alguien "
                              "lo ve, la relación con esa persona empeora mucho"))

        otros = [o for o in self.habitantes.values() if o.id != h.id and not o.fuera_hasta]
        otros.sort(key=lambda o: -self.relacion(h.id, o.id))
        adultos = [o for o in otros if o.oficio and o.oficio != "guardia"]
        # Para hablar: la pareja, el mejor amigo y alguien al azar, para que se conozcan todos.
        charla = [self.habitantes[h.pareja]] if h.pareja and h.pareja in self.habitantes else []
        charla += [o for o in otros if o not in charla][:1]
        resto = [o for o in otros if o not in charla]
        if resto:
            charla.append(self.rng.choice(resto))
        for o in charla:
            if not o.fuera_hasta:
                quien = "su pareja" if o.id == h.pareja else f"relación {round(self.relacion(h.id, o.id))}"
                ops.append(self._social("hablar", f"Hablar con {o.nombre} ({quien}): sube el ánimo de "
                                                  f"los dos y mejora la relación", h, o))
        for o in adultos[:2]:
            ops.append(self._social("ayudar", f"Ayudar a {o.nombre} con su trabajo de {o.de_oficio()}: "
                                              f"produce algo menos que trabajando solo, pero mejora la relación", h, o))
        for o in [o for o in otros if self.relacion(h.id, o.id) < -20][-2:]:
            ops.append(self._social("discutir", f"Discutir con {o.nombre} (relación "
                                                f"{round(self.relacion(h.id, o.id))}): desahoga, pero la "
                                                f"relación empeora y uno de los dos acaba de peor humor", h, o))
        edad = h.edad(self.turno)
        if h.pareja is None and edad >= 18:
            for o in otros:
                otra = o.edad(self.turno)
                if (o.pareja is None and otra >= 18 and abs(otra - edad) <= DIFERENCIA_EDAD_PAREJA
                        and self.relacion(h.id, o.id) >= 50):
                    ops.append(self._social("proponer_pareja", f"Pedir a {o.nombre} que sea su pareja "
                                                               f"(relación {round(self.relacion(h.id, o.id))}): "
                                                               f"cuanto mejor la relación, más fácil que acepte; "
                                                               f"una pareja puede tener hijos", h, o))
        if self.hora < 16:
            ops.append(Opcion("explorar", "explorar",
                              "Salir a explorar más allá del bosque durante un día: puede volver con "
                              "recursos o una gema, pero también herido o con las manos vacías"))
        if len(self.habitantes) >= m.POBLACION_MAXIMA and h.pareja is None and h.edad(self.turno) <= 35:
            ops.append(Opcion("marcharse", "marcharse",
                              "Marcharse de la aldea para siempre: la aldea está llena y así deja sitio"))
        return ops

    def _social(self, tipo: str, descripcion: str, h: Habitante, o: Habitante) -> Opcion:
        return Opcion(f"{tipo}:{o.id}", tipo, descripcion, otro=o.id, nombre_otro=o.nombre,
                      relacion=round(self.relacion(h.id, o.id)))

    def _aplicar(self, h: Habitante, d: Decision, quien: str) -> None:
        o = d.opcion
        if o.tipo == "oficio":
            nuevo = o.id.split(":")[1]
            self._cronica("oficio", f"{h.nombre} deja de ser {h.de_oficio()} y pasa a ser {h.de_oficio(nuevo)}.", h.id)
            h.oficio = nuevo
            h.cambio_oficio = self.turno
            self._poner(h, "trabajar", quien, d.motivo)
        elif o.tipo == "construir":
            partes = o.id.split(":")
            if len(partes) == 2:
                self._empezar_obra(partes[1])
            elif len(partes) == 3:
                cual = int(partes[2]) if partes[2].isdigit() else None if partes[2] == "None" else partes[2]
                self.empezar_evolucion(partes[1], cual)
            self._poner(h, "construir", quien, d.motivo)
        elif o.tipo in ("hablar", "ayudar", "discutir", "proponer_pareja"):
            self._poner(h, o.tipo, quien, d.motivo, otro=o.otro)
        elif o.tipo == "explorar":
            self._poner(h, "explorar", quien, d.motivo, duracion=10**9)
        elif o.tipo == "marcharse":
            self._poner(h, "marcharse", quien, d.motivo, duracion=10**9)
        else:
            self._poner(h, o.tipo, quien, d.motivo)
        h.confianza = d.confianza
        h.historial = h.historial[-(HISTORIAL - 1):] + [[self.turno, o.id, o.descripcion.split(":")[0],
                                                         d.motivo, quien, d.confianza]]

    # ---- acciones ----

    def _poner(self, h: Habitante, accion: str, quien: str, motivo: str = "",
               otro: int | None = None, duracion: int | None = None) -> None:
        h.accion = accion
        h.decidido_por = quien
        h.motivo = motivo
        h.confianza = None
        h.otro = otro
        h.hecho = False
        h.fin_accion = self.turno + (duracion if duracion is not None else m.TURNOS_ENTRE_DECISIONES)
        h.objetivo = self._lugar(h, accion)

    def _lugar(self, h: Habitante, accion: str) -> tuple[float, float] | None:
        mapa = self.mapa
        if accion in ("dormir", "descansar"):
            casa = self._casa(h.casa)
            return (casa.x, casa.y + 1) if casa else mapa.almacen
        if accion in ("comer", "quitar"):
            return mapa.almacen
        if accion == "jugar":
            cx, cy = mapa.almacen
            return (cx + self.rng.uniform(-4, 4), cy + self.rng.uniform(-4, 4))
        if accion == "construir":
            return (self.obra.x, self.obra.y + 1) if self.obra else None
        if accion in ("explorar", "marcharse"):
            return min(mapa.salidas, key=lambda s: math.dist(s, (h.x, h.y)))
        if accion == "trabajar":
            if h.oficio == "campesino":
                return self.rng.choice(self.campos_de_trabajo())
            if h.oficio == "pescador":
                return self.rng.choice(mapa.orillas)
            if h.oficio == "cantero":
                return self.rng.choice(mapa.cantera)
            if h.oficio == "guardia":
                return self.rng.choice(mapa.muralla)
            if h.oficio == "leñador":
                if h.arbol is None or self.mapa.arboles.get(h.arbol, 0) < 1:
                    h.arbol = self._arbol_cercano(h)
                    h.progreso = 0
                return h.arbol
        return None                          # acciones con otro habitante: se sigue su posición

    def _mover_y_actuar(self, h: Habitante) -> None:
        if h.otro is not None:
            otro = self.habitantes.get(h.otro)
            if otro is None or otro.fuera_hasta:
                self._por_defecto(h)
            else:
                h.objetivo = (otro.x, otro.y)
        if h.objetivo is None:
            if h.accion == "construir":
                self._por_defecto(h)
            return
        if math.dist(h.objetivo, (h.x, h.y)) > 1.0 and not self._caminar(h):
            return
        self._actuar(h)

    def _caminar(self, h: Habitante) -> bool:
        """Avanza por la ruta hacia el objetivo, rodeando casas y muros y prefiriendo los caminos.
        Devuelve verdadero cuando ya está a menos de una casilla del objetivo."""
        destino = (round(h.objetivo[0]), round(h.objetivo[1]))
        if h.ruta_a != destino:
            self.caminos.preparar(self.casas, self.muralla)
            h.ruta = self.caminos.ruta((h.x, h.y), h.objetivo)
            h.ruta_a = destino
        restante = VELOCIDAD
        while restante > 0:
            # Las casillas de la ruta y, al final, el punto exacto del objetivo.
            px, py = h.ruta[0] if h.ruta else h.objetivo
            dx, dy = px - h.x, py - h.y
            d = math.hypot(dx, dy)
            if d <= restante:
                h.x, h.y = float(px), float(py)
                restante -= d
                if not h.ruta:
                    break
                h.ruta.pop(0)
            else:
                h.x += dx / d * restante
                h.y += dy / d * restante
                restante = 0
        return math.dist(h.objetivo, (h.x, h.y)) <= 1.0

    def _actuar(self, h: Habitante) -> None:
        a = h.accion
        if a == "trabajar":
            self._trabajar(h, h.oficio, 1.0)
        elif a == "construir":
            self._construir()
        elif a == "comer" and not h.hecho:
            if self.comida >= COMIDA_POR_RACION:
                self.comida -= COMIDA_POR_RACION
                h.hambre = max(0.0, h.hambre - HAMBRE_POR_RACION)
            h.hecho = True
            h.fin_accion = self.turno
        elif a == "quitar" and not h.hecho:
            tomado = min(3.0, self.comida)
            self.comida -= tomado
            h.hambre = max(0.0, h.hambre - HAMBRE_POR_RACION * tomado)
            h.hecho = True
            h.fin_accion = self.turno
            testigos = [o for o in self.habitantes.values() if o.id != h.id and o.oficio
                        and o.accion != "dormir" and not o.fuera_hasta]
            if testigos and self.rng.random() < 0.5:
                t = self.rng.choice(testigos)
                self._sumar_relacion(h.id, t.id, -15)
                self._cronica("robo", f"{t.nombre} ve a {h.nombre} cogiendo comida del almacén a escondidas.")
        elif a == "jugar":
            h.animo = limitar(h.animo + 0.05)
        elif a in ("explorar", "marcharse"):
            self._llega_al_borde(h)
        elif h.otro is not None:
            self._actuar_con_otro(h, self.habitantes[h.otro])

    def _actuar_con_otro(self, h: Habitante, o: Habitante) -> None:
        a = h.accion
        if a == "ayudar":
            if o.oficio and o.oficio != "guardia":
                self._trabajar(h, o.oficio, 0.6)
            self._sumar_relacion(h.id, o.id, 0.03)
            return
        if h.hecho:
            return
        h.hecho = True
        h.fin_accion = self.turno + 3
        if a == "hablar":
            solteros = (h.pareja is None and o.pareja is None and h.edad(self.turno) >= 18
                        and o.edad(self.turno) >= 18
                        and abs(h.edad(self.turno) - o.edad(self.turno)) <= DIFERENCIA_EDAD_PAREJA)
            self._sumar_relacion(h.id, o.id, 8 if solteros else 4)
            h.animo = limitar(h.animo + 8)
            o.animo = limitar(o.animo + 8)
        elif a == "discutir":
            self._sumar_relacion(h.id, o.id, -12)
            gana, pierde = (h, o) if self.rng.random() < 0.5 else (o, h)
            gana.animo = limitar(gana.animo + 3)
            pierde.animo = limitar(pierde.animo - 8)
            self._cronica("discusion", f"{h.nombre} y {o.nombre} discuten a gritos en la aldea.")
        elif a == "proponer_pareja":
            libre = o.pareja is None and h.pareja is None
            if libre and self.rng.random() < (self.relacion(h.id, o.id) - 30) / 70:
                self._formar_pareja(h, o)
            else:
                self._sumar_relacion(h.id, o.id, -5)
                h.animo = limitar(h.animo - 10)
                self._cronica("rechazo", f"{o.nombre} rechaza a {h.nombre}.", h.id, o.id)

    def _guardar(self, recurso: str, cantidad: float) -> float:
        """Mete un recurso en el almacén sin pasar del tope. Devuelve lo que ha cabido."""
        actual = getattr(self, recurso)
        cabe = max(0.0, min(cantidad, self.tope(recurso) - actual))
        setattr(self, recurso, actual + cabe)
        self.ano_en_curso["producido"][recurso] += cabe
        return cabe

    def _lleno(self, recurso: str) -> bool:
        return getattr(self, recurso) >= self.tope(recurso)

    def _trabajar(self, h: Habitante, oficio: str | None, factor: float) -> None:
        recurso = m.RECURSO_OFICIO.get(oficio or "")
        if recurso is None or self._lleno(recurso):
            return
        factor *= 0.6 + 0.8 * h.animo / 100        # con ánimo 50 se produce lo normal
        if oficio in ("cantero", "leñador"):
            factor *= 1 + 0.25 * self.efecto("taller")
        if oficio == "campesino":
            self._guardar("comida", COSECHA[self.estacion] * (0.5 if self.sequia else 1.0) * factor
                          * (1 + 0.3 * self.efecto("huertos")))
        elif oficio == "pescador":
            self.peces -= self._guardar("comida", min(PESCA * (2 if self.buena_pesca else 1) * factor, self.peces))
        elif oficio == "cantero":
            self._guardar("piedra", PIEDRA * factor)
        elif h.accion == "trabajar":
            if h.arbol is None or self.mapa.arboles.get(h.arbol, 0) < 1:
                h.objetivo = h.arbol = self._arbol_cercano(h)
                h.progreso = 0
                return
            h.progreso += 1
            if h.progreso >= TURNOS_POR_ARBOL:
                self.mapa.arboles[h.arbol] = 0.0
                self._guardar("madera", MADERA_POR_ARBOL)
                h.objetivo = h.arbol = self._arbol_cercano(h)
                h.progreso = 0
        else:
            self._guardar("madera", MADERA_POR_ARBOL / TURNOS_POR_ARBOL * factor)

    def _arbol_cercano(self, h: Habitante) -> tuple[int, int] | None:
        crecidos = [p for p, c in self.mapa.arboles.items() if c >= 1]
        if not crecidos:
            return None
        return min(crecidos, key=lambda p: (p[0] - h.x) ** 2 + (p[1] - h.y) ** 2)

    def _llega_al_borde(self, h: Habitante) -> None:
        if h.accion == "marcharse":
            self._cronica("marcha", f"{h.nombre} se marcha de la aldea en busca de un sitio nuevo.")
            self.ano_en_curso["marchas"] += 1
            self.emigrantes.append({"id": h.id, "nombre": h.nombre, "sexo": h.sexo, "edad": h.edad(self.turno),
                                    "oficio": h.oficio, "caracter": h.caracter, "aspecto": h.aspecto})
            self._quitar(h, "marcha")
        else:
            h.fuera_hasta = self.turno + m.TURNOS_POR_DIA
            self._cronica("explora", f"{h.nombre} sale a explorar más allá del bosque.", h.id)

    def _vuelve_de_explorar(self, h: Habitante) -> None:
        h.fuera_hasta = 0
        r = self.rng.random()
        if r < 0.5:
            recurso, cantidad = self.rng.choice([("comida", 20), ("madera", 12), ("piedra", 10)])
            self._guardar(recurso, cantidad)
            self._cronica("explora", f"{h.nombre} vuelve de explorar con {cantidad} de {recurso}.", h.id)
        elif r < 0.65:
            h.salud = limitar(h.salud - 30)
            self._cronica("explora", f"{h.nombre} vuelve herido de explorar." if h.sexo == "h"
                          else f"{h.nombre} vuelve herida de explorar.", h.id)
        elif r < 0.75:
            for o in self.habitantes.values():
                o.animo = limitar(o.animo + 10)
            self._cronica("hallazgo", f"{h.nombre} encuentra una gema al explorar. La aldea lo celebra.", h.id)
        else:
            self._cronica("explora", f"{h.nombre} vuelve de explorar sin nada.", h.id)
        self._por_defecto(h)

    # ---- obras ----

    def _obra_posible(self) -> str | None:
        if self.obra:
            return "seguir"
        quemada = any(c.quemada for c in self.casas)
        if quemada and self._puede_pagar("reconstruir"):
            return "reconstruir"
        if not quemada and self._falta_casa() and self._puede_pagar("casa"):
            return "casa"
        if self.muralla < m.TRAMOS_MURALLA:
            if self._puede_pagar("muralla") and self.madera > self._lena_necesaria():
                return "muralla"
            if self.etapa == 1:
                return None
        return self.obra_evolucion()

    def _puede_pagar(self, tipo: str) -> bool:
        coste = m.OBRAS[tipo]
        return self.madera >= coste["madera"] and self.piedra >= coste["piedra"]

    def _empezar_obra(self, tipo: str) -> None:
        coste = m.OBRAS[tipo]
        self.madera -= coste["madera"]
        self.piedra -= coste["piedra"]
        if tipo == "reconstruir":
            casa = next(c for c in self.casas if c.quemada)
            self.obra = Obra(tipo, casa.x, casa.y, casa=casa.id)
        elif tipo == "casa":
            x, y = self.mapa.solares[len(self.casas)]
            self.obra = Obra(tipo, x, y)
        else:
            x, y = self.mapa.muralla[self.muralla]
            self.obra = Obra(tipo, x, y)

    def _construir(self) -> None:
        obra = self.obra
        if obra is None:
            return
        obra.progreso += 1
        if obra.progreso < coste_obra(obra)["turnos"]:
            return
        self.obra = None
        if obra.tipo not in m.OBRAS:
            self.terminar_evolucion(obra)
        elif obra.tipo == "casa":
            self._nueva_casa()
            self._cronica("casa", "Los vecinos terminan una casa nueva.")
            self._reubicar()
        elif obra.tipo == "reconstruir":
            self.casas[obra.casa - 1].quemada = False
            self._cronica("casa", "La casa quemada vuelve a estar en pie.")
            self._reubicar()
        else:
            self.muralla += 1
            self._cronica("muralla", f"La muralla ya tiene {self.muralla} tramos de {m.TRAMOS_MURALLA}.")
            self._comprobar_etapa()
        for h in self.habitantes.values():
            if h.accion == "construir":
                h.fin_accion = self.turno

    # ---- casas ----

    def _nueva_casa(self) -> Casa:
        x, y = self.mapa.solares[len(self.casas)]
        casa = Casa(len(self.casas) + 1, x, y)
        self.casas.append(casa)
        return casa

    def _casa(self, id: int | None) -> Casa | None:
        if id is None:
            return None
        casa = self.casas[id - 1]
        return None if casa.quemada else casa

    def _ocupantes(self) -> Counter:
        return Counter(h.casa for h in self.habitantes.values() if h.casa is not None)

    def _plazas_libres(self) -> int:
        ocupadas = self._ocupantes()
        return sum(m.CAPACIDAD_CASA - ocupadas[c.id] for c in self.casas if not c.quemada)

    def _casa_con_sitio(self, plazas: int = 1) -> Casa | None:
        ocupadas = self._ocupantes()
        libres = [c for c in self.casas if not c.quemada and m.CAPACIDAD_CASA - ocupadas[c.id] >= plazas]
        return min(libres, key=lambda c: ocupadas[c.id]) if libres else None

    def _familias(self) -> list[list[Habitante]]:
        """Grupos que viven juntos: cada adulto con su pareja y sus hijos menores de edad.
        Un menor sin padres en la aldea forma su propio grupo."""
        vistos: set[int] = set()
        grupos = []
        menores = [h for h in self.habitantes.values() if not h.adulto(self.turno)]
        for h in sorted(self.habitantes.values(), key=lambda h: h.id):
            if h.id in vistos or not h.adulto(self.turno):
                continue
            grupo = [h]
            if h.pareja in self.habitantes:
                grupo.append(self.habitantes[h.pareja])
            ids = {g.id for g in grupo}
            grupo += [k for k in menores if k.id not in vistos and k.padres and ids & set(k.padres)]
            vistos |= {g.id for g in grupo}
            grupos.append(grupo)
        grupos += [[k] for k in menores if k.id not in vistos]
        return grupos

    def _familia_sin_casa_propia(self) -> bool:
        """Hay alguna pareja separada, sin casa o viviendo con gente que no es de su familia."""
        ocupadas = self._ocupantes()
        for grupo in self._familias():
            if len(grupo) < 2 or not any(g.pareja for g in grupo):
                continue
            casas = {g.casa for g in grupo}
            if len(casas) > 1 or None in casas or ocupadas[grupo[0].casa] > len(grupo):
                return True
        return False

    def _falta_casa(self) -> bool:
        if len(self.habitantes) >= m.POBLACION_MAXIMA or len(self.casas) >= len(self.mapa.solares):
            return False
        return self._plazas_libres() < 2 or self._familia_sin_casa_propia()

    def _reubicar(self) -> None:
        """Mantiene juntas a las familias, da casa a quien no tiene y lleva a cada pareja a una
        casa propia cuando hay una vacía. Los hijos solteros de 18 años o más se van de casa de sus
        padres si hay sitio en otra."""
        for grupo in self._familias():
            casas = {g.casa for g in grupo}
            if len(casas) == 1 and self._casa(grupo[0].casa):
                continue
            ocupadas = self._ocupantes()
            for g in grupo:
                if g.casa is not None:
                    ocupadas[g.casa] -= 1
            caben = [c for c in self.casas if not c.quemada and m.CAPACIDAD_CASA - ocupadas[c.id] >= len(grupo)]
            if caben:
                casa = max(caben, key=lambda c: (c.id in casas, -ocupadas[c.id]))
                for g in grupo:
                    g.casa = casa.id
                continue
            for g in grupo:
                if self._casa(g.casa) is None:
                    sitio = self._casa_con_sitio()
                    g.casa = sitio.id if sitio else None

        for grupo in self._familias():
            ocupadas = self._ocupantes()
            casa = grupo[0].casa
            if casa is None:
                continue
            en_pareja = any(g.pareja for g in grupo)
            hijo_mayor = len(grupo) == 1 and grupo[0].padres and grupo[0].edad(self.turno) >= 18 and any(
                p in self.habitantes and self.habitantes[p].casa == casa for p in grupo[0].padres)
            if en_pareja and ocupadas[casa] > len(grupo):
                vacia = next((c for c in self.casas if not c.quemada and ocupadas[c.id] == 0), None)
                if vacia:
                    for g in grupo:
                        g.casa = vacia.id
            elif hijo_mayor:
                otras = [c for c in self.casas if not c.quemada and c.id != casa and ocupadas[c.id] <= 2]
                if otras:
                    grupo[0].casa = min(otras, key=lambda c: ocupadas[c.id]).id

    # ---- personas ----

    def _poblar(self, n: int) -> None:
        # Dos familias, tres jóvenes solteros y un anciano. Si se piden más, se añaden solteros.
        plan = [("h", 30, "campesino", 1), ("m", 28, "pescador", 1), ("h", 6, None, 1),
                ("h", 26, "leñador", 2), ("m", 25, "campesino", 2),
                ("h", 20, "guardia", 3), ("m", 19, "cantero", 3), ("h", 58, "leñador", 3)]
        while len(plan) < n:
            plan.append((self.rng.choice("hm"), self.rng.randint(18, 30), self.rng.choice(m.OFICIOS), None))
        creados = [self._nuevo(sexo, edad, oficio, casa) for sexo, edad, oficio, casa in plan[:n]]
        if n >= 5:
            self._formar_pareja(creados[0], creados[1], cronica=False)
            self._formar_pareja(creados[3], creados[4], cronica=False)
            creados[2].padres = self.registro[creados[2].id].padres = (creados[0].id, creados[1].id)
            self.registro[creados[0].id].hijos.append(creados[2].id)
            self.registro[creados[1].id].hijos.append(creados[2].id)
            self._sumar_relacion(creados[2].id, creados[0].id, 70)
            self._sumar_relacion(creados[2].id, creados[1].id, 70)
        for i, a in enumerate(creados):
            for b in creados[i + 1:]:
                if clave(a.id, b.id) not in self.relaciones:
                    self._sumar_relacion(a.id, b.id, self.rng.uniform(-10, 30))
        self._reubicar()

    def _nuevo(self, sexo: str, edad: float, oficio: str | None, casa: int | None,
               padres: tuple[int, int] | None = None, llegada: str = "fundador") -> Habitante:
        usados = {h.nombre for h in self.habitantes.values()}
        cx, cy = self.mapa.almacen
        h = Habitante(
            id=self.siguiente_id, nombre=elegir_nombre(self.rng, sexo, usados), sexo=sexo,
            nacimiento=self.turno - round(edad * m.TURNOS_POR_ANO),
            caracter=self.rng.choice(m.CARACTERES), aspecto=elegir_aspecto(self.rng, sexo),
            oficio=oficio, x=cx + self.rng.uniform(-2, 2), y=cy + self.rng.uniform(-2, 2),
            casa=casa, padres=padres,
        )
        self.siguiente_id += 1
        self.habitantes[h.id] = h
        self.registro[h.id] = Persona(h.id, h.nombre, sexo, h.nacimiento, h.aspecto, llegada, padres)
        for p in padres or ():
            self.registro[p].hijos.append(h.id)
        self._por_defecto(h)
        if self.de_noche():
            self._poner(h, "dormir", "reglas", "Es de noche", duracion=10**9)
        return h

    def recibir(self, e: dict, origen: str, funda: bool = False) -> Habitante:
        """Alguien que llega desde otra aldea (ver `emigrantes`) y se queda a vivir aquí."""
        casa = self._casa_con_sitio()
        h = self._nuevo(e["sexo"], e["edad"], e["oficio"] or self.rng.choice(m.OFICIOS[:4]),
                        casa.id if casa else None, llegada="colono")
        # Conserva su nombre y su aspecto si los trae (gente de un pueblo llega sin ellos).
        if e["nombre"] and e["nombre"] not in {o.nombre for o in self.habitantes.values() if o.id != h.id}:
            h.nombre = self.registro[h.id].nombre = e["nombre"]
        h.caracter = e["caracter"]
        if e["aspecto"]:
            h.aspecto = self.registro[h.id].aspecto = e["aspecto"]
        texto = (f"{h.nombre} llega desde {con_articulo(origen)} y funda {con_articulo(self.nombre)}." if funda
                 else f"{h.nombre} llega desde {con_articulo(origen)} para vivir aquí.")
        self._cronica("colono", texto, h.id)
        self.ano_en_curso["llegadas"] += 1
        return h

    def _formar_pareja(self, a: Habitante, b: Habitante, cronica: bool = True) -> None:
        a.pareja, b.pareja = b.id, a.id
        self.registro[a.id].parejas.append(b.id)
        self.registro[b.id].parejas.append(a.id)
        self._sumar_relacion(a.id, b.id, 80 - self.relacion(a.id, b.id))
        a.animo = limitar(a.animo + 20)
        b.animo = limitar(b.animo + 20)
        if cronica:
            self._cronica("pareja", f"{a.nombre} y {b.nombre} forman pareja. La aldea lo celebra con una pequeña boda.", a.id, b.id)
            self.boda()
            self.ano_en_curso["parejas"] += 1
            self._reubicar()

    def _morir(self, h: Habitante, causa: str) -> None:
        texto = {
            "vejez": f"{h.nombre} muere de viejo a los {int(h.edad(self.turno))} años.",
            "hambre": f"{h.nombre} muere de hambre.",
            "enfermedad": f"{h.nombre} muere por una enfermedad.",
            "agotamiento": f"{h.nombre} muere de agotamiento.",
            "monstruos": f"{h.nombre} muere en el ataque de los monstruos.",
        }[causa]
        if causa == "vejez" and h.sexo == "m":
            texto = texto.replace("de viejo", "de vieja")
        self._cronica("muerte", texto)
        self.ano_en_curso["muertes"][causa] += 1
        for o in self.habitantes.values():
            consuelo = 1 - 0.5 * self.efecto("templo")
            if o.id == h.pareja:
                o.animo = limitar(o.animo - 30 * consuelo)
            elif o.id != h.id and self.relacion(h.id, o.id) > 40:
                o.animo = limitar(o.animo - 10 * consuelo)
        self._quitar(h, causa)

    def _quitar(self, h: Habitante, causa: str) -> None:
        persona = self.registro[h.id]
        persona.salida, persona.causa, persona.oficio = self.turno, causa, h.oficio
        if h.pareja and h.pareja in self.habitantes:
            self.habitantes[h.pareja].pareja = None
        del self.habitantes[h.id]
        self.relaciones = {k: v for k, v in self.relaciones.items() if h.id not in k}

    def relacion(self, a: int, b: int) -> float:
        return self.relaciones.get(clave(a, b), 0.0)

    def _sumar_relacion(self, a: int, b: int, puntos: float) -> None:
        k = clave(a, b)
        self.relaciones[k] = max(-100.0, min(100.0, self.relaciones.get(k, 0.0) + puntos))

    # ---- sucesos diarios ----

    def _nuevo_dia(self) -> None:
        dia_del_ano = self.dia % m.DIAS_POR_ANO
        if dia_del_ano == 0:
            self._cerrar_ano()
        if dia_del_ano % m.DIAS_POR_ESTACION == 0:
            self.sequia = self.estacion == "verano" and self.rng.random() < 0.15
            self._cronica("estacion", f"Empieza {'el' if self.estacion != 'primavera' else 'la'} {self.estacion}.")
            self.empieza_estacion()
            if self.sequia:
                self._cronica("sequia", "Este verano llega una sequía. Los campos darán la mitad.")
        self.comida *= 1 - 0.01 * (1 - 0.6 * self.efecto("granero"))
        self.relaciones = {k: v * OLVIDO_DIARIO for k, v in self.relaciones.items()}
        quitados = set(self.arboles_quitados)
        for p, c in self.mapa.arboles.items():
            if c < 1 and p not in quitados:
                self.mapa.arboles[p] = min(1.0, c + CRECIMIENTO_ARBOL)
        self.buena_pesca = self.rng.random() < 0.2
        if self.buena_pesca:
            self._cronica("pesca", "Hoy el río viene lleno de peces.")
        if self.estacion == "invierno":
            self._calefaccion()
        self._edades()
        self._nacimientos()
        self._enfermedades()
        if self.rng.random() < 1 / 72:
            self._incendio()
        if len(self.habitantes) < 4 and self.rng.random() < 0.3:
            self._forastero()
        self._emigracion()
        self.dia_evolucion()
        self._reubicar()
        corte = self.turno - m.TURNOS_POR_ANO
        self.cronica = [s for s in self.cronica if s.turno > corte]

    def _emigracion(self) -> None:
        """Con la aldea llena, cada día un joven soltero puede marcharse a buscar sitio, aunque
        Jev no lo haya decidido. Así las aldeas llenas siempre empujan gente hacia fuera."""
        if len(self.habitantes) < m.POBLACION_MAXIMA or self.rng.random() >= 0.5:
            return
        if any(h.accion == "marcharse" for h in self.habitantes.values()):
            return
        jovenes = [h for h in self.habitantes.values() if h.oficio and h.pareja is None
                   and m.EDAD_ADULTA <= h.edad(self.turno) <= 35 and not h.fuera_hasta]
        if jovenes:
            h = self.rng.choice(jovenes)
            self._poner(h, "marcharse", "reglas", "La aldea está llena: se va a buscar un sitio nuevo",
                        duracion=10**9)

    def _calefaccion(self) -> None:
        ocupadas = [c for c in self.casas if not c.quemada and self._ocupantes()[c.id]]
        necesaria = len(ocupadas) * LENA_INVIERNO * (2 if self.invierno_duro else 1)
        if self.madera >= necesaria:
            self.madera -= necesaria
            return
        self.madera = 0.0
        for h in self.habitantes.values():
            h.salud = limitar(h.salud - 5)
            h.animo = limitar(h.animo - 10)
        self._cronica("frio", "No queda leña. Los vecinos pasan la noche helados.")

    def _edades(self) -> None:
        for h in list(self.habitantes.values()):
            edad = h.edad(self.turno)
            riesgo = 0.01 * math.exp((edad - 50) / 4) / m.DIAS_POR_ANO
            if self.rng.random() < riesgo:
                self._morir(h, "vejez")
            elif h.oficio is None and edad >= m.EDAD_ADULTA:
                necesarios = self.estado().oficios_necesarios
                h.oficio = necesarios[0] if necesarios else self.rng.choice(m.OFICIOS[:4])
                self._cronica("oficio", f"{h.nombre} cumple {m.EDAD_ADULTA} años y empieza a trabajar de {h.de_oficio()}.", h.id)

    def _nacimientos(self) -> None:
        ocupadas = self._ocupantes()
        for h in list(self.habitantes.values()):
            if h.sexo != "m" or h.pareja is None:
                continue
            p = self.habitantes[h.pareja]
            if p.sexo != "h" or not 18 <= h.edad(self.turno) <= 42 or h.casa != p.casa or h.casa is None:
                continue
            if (len(self.habitantes) >= m.POBLACION_MAXIMA or ocupadas[h.casa] >= m.CAPACIDAD_CASA
                    or self.comida < 3 * len(self.habitantes)):
                continue
            if self.rng.random() < 0.05:
                hijo = self._nuevo(self.rng.choice("hm"), 0, None, h.casa, padres=(p.id, h.id),
                                   llegada="nacimiento")
                hijo.x, hijo.y = h.x, h.y
                ocupadas[h.casa] += 1
                for padre in (h, p):
                    self._sumar_relacion(hijo.id, padre.id, 70)
                    padre.animo = limitar(padre.animo + 20)
                hijo_de = "hijo" if hijo.sexo == "h" else "hija"
                self._cronica("nacimiento", f"Nace {hijo.nombre}, {hijo_de} de {h.nombre} y {p.nombre}.")
                self.ano_en_curso["nacimientos"] += 1

    def _enfermedades(self) -> None:
        for h in self.habitantes.values():
            edad = h.edad(self.turno)
            riesgo = 0.004 * (2 if edad >= 50 or edad < 5 else 1) * (1 - 0.4 * self.efecto("pozo"))
            if h.enfermo_hasta <= self.turno and self.rng.random() < riesgo:
                h.enfermo_hasta = self.turno + 3 * m.TURNOS_POR_DIA
                self._cronica("enfermedad", f"{h.nombre} cae enfermo." if h.sexo == "h"
                              else f"{h.nombre} cae enferma.")

    def _incendio(self) -> None:
        ocupadas = self._ocupantes()
        casas = [c for c in self.casas if not c.quemada and ocupadas[c.id]]
        if not casas:
            return
        casa = self.rng.choices(casas, weights=[0.2 if c.piedra else 1.0 for c in casas])[0]
        casa.quemada = True
        for h in self.habitantes.values():
            if h.casa == casa.id:
                h.casa = None
                h.animo = limitar(h.animo - 15)
        self._cronica("incendio", "Una casa se quema. Sus vecinos tendrán que dormir en otra.")
        self.ano_en_curso["incendios"] += 1

    def _forastero(self) -> None:
        casa = self._casa_con_sitio()
        h = self._nuevo(self.rng.choice("hm"), self.rng.randint(18, 30),
                        self.rng.choice(m.OFICIOS[:4]), casa.id if casa else None, llegada="forastero")
        self._cronica("forastero", f"Llega a la aldea {'un forastero' if h.sexo == 'h' else 'una forastera'}: "
                                   f"{h.nombre}, {h.de_oficio()}.", h.id)
        self.ano_en_curso["llegadas"] += 1

    def _ataque(self) -> None:
        if not self.habitantes or self.rng.random() >= 0.12:
            return
        monstruos, femenino, dibujo = self.rng.choice(MONSTRUOS)
        # Cuanto más grande es la aldea, más monstruos atrae.
        fuerza = self.rng.randint(1, 3 + len(self.habitantes) // 5) + (1 if self.rng.random() < 0.2 else 0)
        guardias = [h for h in self.habitantes.values()
                    if h.oficio == "guardia" and not h.fuera_hasta and h.salud > 30]
        defensa = ((1.5 + self.efecto("dojo")) * len(guardias) + 0.15 * self.muralla
                   + 2 * self.efecto("vigia") + 0.5 * self.faroles)
        self.ano_en_curso["ataques"] += 1
        rotura = 0.5 - 0.2 * self.efecto("vigia")
        if self.muralla <= self.reforzados:
            rotura *= 0.3                     # el último tramo está reforzado
        if self.muralla and self.rng.random() < rotura:
            self.muralla -= 1
            self.reforzados = min(self.reforzados, self.muralla)
            roto = " Rompen un tramo de muralla."
        else:
            roto = ""
        # Lo que hace falta para verlo en el mapa: qué entra, cuántos, por qué borde y si se les frena.
        self.ataque = {"turno": self.turno, "monstruo": dibujo, "cuantos": min(fuerza, 8),
                       "entrada": self.mapa.salidas[self.turno % len(self.mapa.salidas)],
                       "frenado": fuerza <= defensa, "guardias": [g.id for g in guardias]}
        if fuerza <= defensa:
            self._cronica("ataque", f"Una noche llegan {monstruos}. Los guardias {'las' if femenino else 'los'} echan.{roto}")
            if guardias and self.rng.random() < 0.25:
                g = self.rng.choice(guardias)
                g.salud = limitar(g.salud - 15)
            return
        exceso = fuerza - defensa
        robado = min(self.comida, 8 * exceso)
        self.comida -= robado
        danado = self.danar_edificio(20)
        if danado:
            roto += f" Estropean {danado}."
        self._cronica("ataque", f"Una noche llegan {monstruos} y entran en la aldea.{roto} "
                                f"Se llevan {int(robado)} de comida.")
        presentes = [h for h in self.habitantes.values() if not h.fuera_hasta]
        for h in self.rng.sample(presentes, min(len(presentes), math.ceil(exceso))):
            h.salud = limitar(h.salud - self.rng.uniform(25, 55))
            self._hito(h.id, "ataque", f"Resulta {'herida' if h.sexo == 'm' else 'herido'} en un ataque de {monstruos}.")
            if h.salud <= 0:
                self._morir(h, "monstruos")

    # ---- crónica y resúmenes ----

    def _cronica(self, tipo: str, texto: str, *quienes: int) -> None:
        """Apunta un suceso en la crónica y, si es de alguien en concreto, también en su vida."""
        self.cronica.append(Suceso(self.turno, tipo, texto))
        for q in quienes:
            self._hito(q, tipo, texto)

    def _hito(self, id: int, tipo: str, texto: str) -> None:
        """Un momento de la vida de alguien, para contarla en su ficha aunque ya no esté."""
        if id in self.registro:
            self.registro[id].hitos.append([self.turno, tipo, texto])

    def _resumen_vacio(self) -> dict:
        return {"nacimientos": 0, "muertes": Counter(), "parejas": 0, "llegadas": 0, "marchas": 0,
                "ataques": 0, "incendios": 0, "producido": Counter()}

    def _cerrar_ano(self) -> None:
        if self.turno == 0:
            return
        r = self.ano_en_curso
        self.resumenes.append({
            "ano": self.ano - 1,
            "poblacion": len(self.habitantes),
            "nacimientos": r["nacimientos"],
            "muertes": dict(r["muertes"]),
            "parejas": r["parejas"],
            "llegadas": r["llegadas"],
            "marchas": r["marchas"],
            "ataques": r["ataques"],
            "incendios": r["incendios"],
            "producido": {k: round(v) for k, v in r["producido"].items()},
            "casas": sum(1 for c in self.casas if not c.quemada),
            "muralla": self.muralla,
            "etapa": self.etapa,
            "edificios": len(self.edificios),
            "reforzados": self.reforzados,
            "casas_piedra": sum(1 for c in self.casas if c.piedra),
            "comida": round(self.comida),
            "madera": round(self.madera),
            "piedra": round(self.piedra),
        })
        self.ano_en_curso = self._resumen_vacio()

    def _lena_necesaria(self) -> float:
        """Madera para calentar las casas ocupadas durante un invierno entero."""
        ocupadas = sum(1 for n in self._ocupantes().values() if n)
        return ocupadas * LENA_INVIERNO * m.DIAS_POR_ESTACION
