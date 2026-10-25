"""Datos fijos del mundo y estado de cada habitante.

Las necesidades van de 0 a 100. En energía, salud y ánimo, más es mejor. En hambre, más es peor.

Escala de tiempo: un turno son 10 segundos reales y 4 minutos del mundo. Un día del mundo dura
una hora real y un año, un día real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TURNO_SEGUNDOS = 10
TURNOS_POR_HORA = 15
TURNOS_POR_DIA = 360
DIAS_POR_ESTACION = 6
DIAS_POR_ANO = 24
TURNOS_POR_ANO = TURNOS_POR_DIA * DIAS_POR_ANO
ESTACIONES = ("primavera", "verano", "otoño", "invierno")

HORA_DESPERTAR = 6
HORA_DORMIR = 22
HORA_ATAQUE = 2                 # los monstruos atacan de madrugada

TURNOS_ENTRE_DECISIONES = 30    # 5 minutos reales
POBLACION_MAXIMA = 20
POBLACION_EMIGRAR = 14          # desde aquí, algún joven se marcha a fundar otra aldea
CAPACIDAD_CASA = 6              # con 4, una pareja con dos hijos ya no podía tener más
EDAD_ADULTA = 16
TRAMOS_MURALLA = 20

OFICIOS = ("campesino", "leñador", "pescador", "cantero", "guardia")
PLURAL_OFICIO = {"campesino": "campesinos", "leñador": "leñadores", "pescador": "pescadores",
                 "cantero": "canteros", "guardia": "guardias"}
FEMENINO_OFICIO = {"campesino": "campesina", "leñador": "leñadora", "pescador": "pescadora",
                   "cantero": "cantera", "guardia": "guardia"}
RECURSO_OFICIO ={"campesino": "comida", "pescador": "comida", "leñador": "madera",
                  "cantero": "piedra", "guardia": None}
CARACTERES = ("trabajador", "perezoso", "sociable", "solitario", "valiente", "prudente")

# Lo que cuesta cada obra y los turnos de trabajo que lleva.
OBRAS = {
    "casa": {"madera": 20, "piedra": 15, "turnos": 360},
    "reconstruir": {"madera": 10, "piedra": 8, "turnos": 180},
    "muralla": {"madera": 4, "piedra": 20, "turnos": 240},
}


@dataclass
class Habitante:
    id: int
    nombre: str
    sexo: str                    # "h" o "m"
    nacimiento: int              # turno en que nació; los primeros habitantes, en negativo
    caracter: str
    aspecto: str                 # carpeta del personaje en Actor/Character del paquete
    oficio: str | None           # None mientras es niño
    x: float
    y: float
    casa: int | None
    padres: tuple[int, int] | None = None
    pareja: int | None = None
    hambre: float = 20.0
    energia: float = 80.0
    salud: float = 100.0
    animo: float = 60.0
    # Lo que está haciendo ahora.
    accion: str = "dormir"
    decidido_por: str = "reglas"  # "jev", "reglas", "respaldo" o "urgencia"
    motivo: str = ""
    confianza: float | None = None   # confianza de Jev en la decisión actual
    objetivo: tuple[float, float] | None = None
    ruta: list = field(default_factory=list)   # casillas que le quedan por pisar hasta el objetivo
    ruta_a: tuple[int, int] | None = None      # casilla del objetivo para la que se calculó la ruta
    otro: int | None = None      # habitante con el que hace la acción
    fin_accion: int = 0
    hecho: bool = False          # para acciones de un solo efecto, como comer
    progreso: int = 0            # turnos que lleva cortando el árbol actual
    arbol: tuple[int, int] | None = None
    proxima_decision: int = 0
    cambio_oficio: int = -10**9  # turno del último cambio de oficio
    enfermo_hasta: int = 0
    fuera_hasta: int = 0         # explorando fuera del mapa hasta este turno
    # Últimas decisiones, la más reciente al final: [turno, opción, descripción, motivo, quién, confianza].
    historial: list = field(default_factory=list)

    def edad(self, turno: int) -> float:
        return (turno - self.nacimiento) / TURNOS_POR_ANO

    def adulto(self, turno: int) -> bool:
        return self.edad(turno) >= EDAD_ADULTA

    def de_oficio(self, oficio: str | None = None) -> str:
        """Nombre del oficio con el género del habitante: "campesina", "leñador"…"""
        oficio = oficio or self.oficio or ""
        return FEMENINO_OFICIO.get(oficio, oficio) if self.sexo == "m" else oficio


@dataclass
class Persona:
    """Ficha permanente de cada habitante que ha vivido en la aldea, para el árbol genealógico.
    No se borra nunca, ni cuando el habitante muere o se marcha."""
    id: int
    nombre: str
    sexo: str
    nacimiento: int
    aspecto: str
    llegada: str                 # "fundador", "nacimiento" o "forastero"
    padres: tuple[int, int] | None = None
    parejas: list[int] = field(default_factory=list)   # por orden, si enviuda y vuelve a emparejarse
    hijos: list[int] = field(default_factory=list)
    oficio: str | None = None    # último oficio que tuvo
    salida: int | None = None    # turno en que murió o se marchó
    causa: str | None = None     # "vejez", "hambre", "enfermedad", "agotamiento", "monstruos" o "marcha"
    hitos: list = field(default_factory=list)   # [turno, tipo, texto]: pareja, oficio, exploraciones, heridas


@dataclass
class Casa:
    id: int
    x: int
    y: int
    quemada: bool = False
    piedra: bool = False         # mejorada a casa de piedra (etapa 4)
    estado: float = 100.0        # de 0 a 100: baja con los años; por debajo de 40 hay que repararla


@dataclass
class Obra:
    tipo: str                    # "casa", "reconstruir", "muralla", "edificio", "reparar", "casa_piedra", "reforzar" o "faroles"
    x: int
    y: int
    progreso: int = 0
    casa: int | None = None      # casa que se reconstruye, se repara o se hace de piedra
    nombre: str | None = None    # edificio que se construye o se repara


@dataclass(frozen=True)
class Suceso:
    turno: int
    tipo: str
    texto: str
