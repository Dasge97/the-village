"""Lo que ve la web de un pueblo, villa o ciudad, con la misma forma que lo de una aldea (vista.py)
para que el mapa, las secciones y las fichas sirvan para los dos. Además lleva `grande` con lo que
solo tienen estos: población por edades, edificios, la última decisión del consejo y cuánta gente
anda por la calle (`multitud`, que la web dibuja como gente sin ficha)."""

from __future__ import annotations

from .motor import modelos as m
from .motor.aldea import TURNOS_ATAQUE_VISIBLE
from .mundo.grande import TIPOS, Grande, _femenino
from .vista import vida

# Edificios que se dibujan en las parcelas, de la plaza hacia fuera, antes que las casas.
ESPECIALES = ["mercado", "templo", "dojo", "posada", "torre", "taller", "herreria", "escuela", "hospital", "mina",
              "acueducto", "puerto", "teatro", "cuartel", "biblioteca", "granero"]
MONUMENTOS_DIBUJO = {"estatua": "estatua", "gran templo": "gran_templo", "castillo": "castillo", "faro": "faro"}
MAX_ESPECIALES = 3      # de cada tipo, como mucho, en el dibujo


def _casas(g: Grande) -> list[dict]:
    modelos = [MONUMENTOS_DIBUJO[n] for n in g.monumentos]
    for e in ESPECIALES:
        modelos += [e] * min(MAX_ESPECIALES, g.edificios.get(e, 0))
    modelos += ["casa"] * g.edificios.get("casa", 0)
    return [{"id": i + 1, "x": x, "y": y, "quemada": False, "modelo": modelo}
            for i, ((x, y), modelo) in enumerate(zip(g.lotes, modelos))]


def _cargo(n) -> str:
    return _femenino(n.cargo) if n.sexo == "m" else n.cargo


def _notable(g: Grande, n, i: int, casas: list[dict]) -> dict:
    # Cada notable está delante de un edificio: de día del suyo; de noche, en una casa.
    sitio = casas[i % len(casas)] if casas else {"x": g.mapa.almacen[0], "y": g.mapa.almacen[1]}
    noche = g.de_noche()
    return {
        "id": n.id, "nombre": n.nombre, "sexo": n.sexo, "edad": int((g.turno - n.nacimiento) / m.TURNOS_POR_ANO),
        "oficio": _cargo(n), "caracter": n.caracter, "personaje": n.aspecto,
        "x": sitio["x"] + (0.5 if noche else 1.5), "y": sitio["y"] + 1, "fuera": False,
        "accion": "dormir" if noche else "trabajar", "con": None,
        "motivo": "Es de noche" if noche else f"Hace su trabajo de {_cargo(n)}",
        "decidido_por": "reglas", "confianza": None,
        "necesidades": None,      # en los asentamientos grandes no se siguen las necesidades de cada uno
        "pareja": None, "enfermo": False,
    }


def estado_grande(g: Grande) -> dict:
    casas = _casas(g)
    obra = None
    if g.obra and len(casas) < len(g.lotes):
        x, y = g.lotes[len(casas)]
        obra = {"tipo": "casa", "x": x, "y": y, "progreso": g.obra["total"] - g.obra["dias"], "total": g.obra["total"]}
    pob = g.poblacion
    t = g.turno
    return {
        "nombre": g.nombre, "tipo": g.tipo, "bioma": g.bioma,
        "turno": t, "segundos_por_turno": m.TURNO_SEGUNDOS, "ano": g.ano, "estacion": g.estacion,
        "dia": g.dia % m.DIAS_POR_ANO + 1, "hora": g.hora, "de_noche": g.de_noche(),
        "poblacion": pob,
        "recursos": {"comida": round(g.comida), "madera": round(g.madera), "piedra": round(g.piedra)},
        "muralla": g.edificios.get("muralla", 0),
        "casas": casas, "obra": obra, "arboles_cortados": {},
        "ataque": g.ataque if g.ataque and t - g.ataque["turno"] < TURNOS_ATAQUE_VISIBLE else None,
        "habitantes": [_notable(g, n, i, casas) for i, n in enumerate(g.notables.values())],
        "sucesos": [{"turno": s.turno, "tipo": s.tipo, "texto": s.texto} for s in g.cronica[-30:]],
        "multitud": min(45, round(pob / 8)) if not g.de_noche() else min(8, round(pob / 60)),
        "grande": {
            "tipo": g.tipo, "tope": g.tope, "capacidad": g.capacidad,
            "edades": {"ninos": sum(g.edades[:16]), "adultos": sum(g.edades[16:60]), "mayores": sum(g.edades[60:])},
            "edificios": dict(g.edificios), "obra": g.obra["edificio"] if g.obra else None,
            "consejo": g.consejo, "animo": round(g.animo, 2), "salud": round(g.salud, 2),
            "notables": TIPOS[g.tipo]["notables"],
            "sociedad": g.datos_sociedad(),
        },
    }


def ficha_notable(g: Grande, id: int) -> dict | None:
    casas = _casas(g)
    lista = list(g.notables.values())
    n = g.notables.get(id)
    if n is None:
        return None
    p = g.registro[id]
    return {
        **_notable(g, n, lista.index(n), casas),
        "llegada": "cargo", "nacimiento_ano": p.nacimiento // m.TURNOS_POR_ANO + 1,
        "llegada_ano": next((t for t, _, _ in p.hitos), g.turno) // m.TURNOS_POR_ANO + 1,
        "padres": [], "parejas": [], "hijos": [], "amigos": [], "rivales": [],
        "historial": [], "vida": vida(g, p),
    }


def arbol_grande(g: Grande) -> dict:
    personas = []
    for p in g.registro.values():
        n = g.notables.get(p.id)
        personas.append({
            "id": p.id, "nombre": p.nombre, "sexo": p.sexo, "llegada": p.llegada, "padres": [], "parejas": [],
            "hijos": [], "nacimiento": p.nacimiento, "salida": p.salida, "causa": p.causa,
            "oficio": (_cargo(n) if n else _femenino(p.oficio) if p.sexo == "m" else p.oficio),
            "vivo": n is not None, "edad": int((g.turno - p.nacimiento) / m.TURNOS_POR_ANO) if n else None,
            "personaje": p.aspecto, "vida": vida(g, p),
        })
    return {"turno": g.turno, "turnos_por_ano": m.TURNOS_POR_ANO, "personas": personas}
