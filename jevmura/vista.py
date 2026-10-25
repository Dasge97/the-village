"""Lo que ve la web: el mapa fijo y el estado de la aldea en cada turno, en datos sencillos.

El mapa se manda una vez al conectar. El estado se manda después de cada turno por websocket.
Aquí también se decide con qué personaje del paquete se dibuja cada habitante según su edad y
su oficio.
"""

from __future__ import annotations

import re

from .motor import modelos as m
from .motor.aldea import TURNOS_ATAQUE_VISIBLE, Aldea
from .motor.evolucion import EDIFICIOS, ETAPAS, coste_obra
from .motor.modelos import Habitante

# Una letra por tipo de casilla para que el mapa ocupe poco.
LETRAS = {"hierba": "h", "agua": "a", "bosque": "b", "campo": "c", "cantera": "k", "camino": "m", "plaza": "p"}

EDAD_ANCIANO = 55


def personaje(h: Habitante, turno: int) -> str:
    """Carpeta del personaje en `Actor/Character` con la que se dibuja al habitante."""
    edad = h.edad(turno)
    if edad < m.EDAD_ADULTA:
        return "Child"
    if edad >= EDAD_ANCIANO:
        return "OldWoman" if h.sexo == "m" else ("OldMan", "OldMan2")[h.id % 2]
    if h.oficio == "guardia":
        return "NinjaRed" if h.sexo == "m" else ("Samurai", "SamuraiBlue")[h.id % 2]
    return h.aspecto


def mapa_publico(aldea: Aldea) -> dict:
    mp = aldea.mapa
    return {
        "ancho": len(mp.casillas[0]),
        "alto": len(mp.casillas),
        "casillas": ["".join(LETRAS[c] for c in fila) for fila in mp.casillas],
        "arboles": sorted(mp.arboles),
        "solares": mp.solares,
        "tramos": mp.tramos,
        "almacen": mp.almacen,
        "molino": mp.molino,
        "puente": mp.puente,
        "puentes": mp.puentes or ([mp.puente] if mp.puente else []),
        "muros_fijos": mp.muros_fijos,
        "formato": mp.formato,
        "bioma": mp.bioma,
        "campos": [min(mp.campos), max(mp.campos)],
        "cantera": mp.cantera,
    }


def estado_publico(aldea: Aldea) -> dict:
    t = aldea.turno
    arboles = sorted(aldea.mapa.arboles)
    obra = None
    if aldea.obra:
        o = aldea.obra
        obra = {"tipo": o.tipo, "x": o.x, "y": o.y, "progreso": o.progreso, "total": coste_obra(o)["turnos"],
                "tramo": aldea.muralla if o.tipo == "muralla" else aldea.reforzados if o.tipo == "reforzar" else None,
                "modelo": _modelo_obra(aldea, o)}
    return {
        "nombre": aldea.nombre,
        "bioma": aldea.bioma,
        "turno": t,
        "segundos_por_turno": m.TURNO_SEGUNDOS,
        "ano": aldea.ano,
        "estacion": aldea.estacion,
        "dia": aldea.dia % m.DIAS_POR_ANO + 1,
        "hora": aldea.hora,
        "de_noche": aldea.de_noche(),
        "poblacion": len(aldea.habitantes),
        "recursos": {"comida": round(aldea.comida), "madera": round(aldea.madera), "piedra": round(aldea.piedra)},
        "muralla": aldea.muralla,
        "casas": _casas(aldea),
        "evolucion": _evolucion(aldea),
        "obra": obra,
        "ataque": aldea.ataque if aldea.ataque and t - aldea.ataque["turno"] < TURNOS_ATAQUE_VISIBLE else None,
        "arboles_cortados": {i: round(aldea.mapa.arboles[p], 2) for i, p in enumerate(arboles) if aldea.mapa.arboles[p] < 1},
        "habitantes": [_habitante(aldea, h) for h in aldea.habitantes.values()],
        "sucesos": [{"turno": s.turno, "tipo": s.tipo, "texto": s.texto} for s in aldea.cronica[-30:]],
    }


# Edificios que se dibujan como tales (los huertos nuevos se dibujan como campo).
DIBUJADOS = [n for n in EDIFICIOS if n != "huertos"]


def _casas(aldea: Aldea) -> list[dict]:
    """Las casas y, detrás, los edificios de la evolución, con el modelo con el que se dibujan."""
    casas = [{"id": c.id, "x": c.x, "y": c.y, "quemada": c.quemada, "estado": round(c.estado),
              "modelo": "casa_piedra" if c.piedra else None} for c in aldea.casas]
    for i, n in enumerate(DIBUJADOS):
        if n in aldea.edificios:
            x, y = aldea.sitio(n)
            casas.append({"id": 1000 + i, "x": x, "y": y, "quemada": False, "estado": round(aldea.edificios[n]),
                          "modelo": n})
    return casas


def _modelo_obra(aldea: Aldea, o) -> str | None:
    if o.tipo in ("edificio", "reparar") and o.nombre:
        return o.nombre if o.nombre != "huertos" else None
    if o.tipo == "casa_piedra":
        return "casa_piedra"
    return None


def _evolucion(aldea: Aldea) -> dict:
    """Etapa, edificios con su estado, mejoras y la última decisión del consejo de la aldea."""
    return {
        "etapa": aldea.etapa, "nombre": ETAPAS[aldea.etapa], "etapas": len(ETAPAS),
        "edificios": [{"id": n, "nombre": EDIFICIOS[n]["nombre"], "estado": round(e), "efecto": EDIFICIOS[n]["efecto"]}
                      for n, e in aldea.edificios.items()],
        "pendientes": [{"id": n, "nombre": EDIFICIOS[n]["nombre"], "efecto": EDIFICIOS[n]["efecto"]} for n in aldea.disponibles()],
        "plan": EDIFICIOS[aldea.plan]["nombre"] if aldea.plan else None,
        "reforzados": aldea.reforzados,
        "casas_piedra": sum(1 for c in aldea.casas if c.piedra),
        "faroles": [aldea.sitio_farol(k) for k in range(aldea.faroles)],
        "huertos": aldea.rect_huertos() if "huertos" in aldea.edificios else None,
        "arboles_quitados": [i for i, p in enumerate(sorted(aldea.mapa.arboles)) if p in set(aldea.arboles_quitados)],
        "consejo": aldea.consejo or None,
        "invierno_duro": aldea.invierno_duro,
        "obra": aldea.estado().obra if aldea.obra else None,
    }


def _habitante(aldea: Aldea, h: Habitante) -> dict:
    t = aldea.turno
    pareja = aldea.habitantes.get(h.pareja) if h.pareja else None
    otro = aldea.habitantes.get(h.otro) if h.otro else None
    return {
        "id": h.id,
        "nombre": h.nombre,
        "sexo": h.sexo,
        "edad": int(h.edad(t)),
        "oficio": h.de_oficio() if h.oficio else None,
        "caracter": h.caracter,
        "personaje": personaje(h, t),
        "x": round(h.x, 2),
        "y": round(h.y, 2),
        "fuera": bool(h.fuera_hasta),
        "accion": h.accion,
        "con": otro.nombre if otro else None,
        "motivo": h.motivo,
        "decidido_por": h.decidido_por,
        "confianza": h.confianza,
        "necesidades": {"hambre": round(h.hambre), "energia": round(h.energia),
                        "salud": round(h.salud), "animo": round(h.animo)},
        "pareja": pareja.nombre if pareja else None,
        "enfermo": h.enfermo_hasta > t,
    }


def _persona(aldea: Aldea, id: int) -> dict | None:
    """Datos mínimos de alguien del registro, para enlazarlo desde una ficha o el árbol."""
    p = aldea.registro.get(id)
    if p is None:
        return None
    h = aldea.habitantes.get(id)
    return {"id": p.id, "nombre": p.nombre, "sexo": p.sexo, "vivo": h is not None,
            "personaje": personaje(h, aldea.turno) if h else p.aspecto}


def ficha_habitante(aldea: Aldea, id: int) -> dict | None:
    """Todo lo que enseña la ficha de un habitante vivo."""
    h = aldea.habitantes.get(id)
    if h is None:
        return None
    p = aldea.registro[id]
    relaciones = sorted(((round(aldea.relacion(id, o.id)), o) for o in aldea.habitantes.values() if o.id != id),
                        key=lambda r: -r[0])
    amigos = [{**_persona(aldea, o.id), "puntos": v} for v, o in relaciones if v >= 20 and o.id != h.pareja][:3]
    rivales = [{**_persona(aldea, o.id), "puntos": v} for v, o in reversed(relaciones) if v <= -20][:3]
    return {
        **_habitante(aldea, h),
        "llegada": p.llegada,
        "nacimiento_ano": p.nacimiento // m.TURNOS_POR_ANO + 1,
        "llegada_ano": _turno_de_llegada(p) // m.TURNOS_POR_ANO + 1,
        "padres": [_persona(aldea, i) for i in (p.padres or ())],
        "parejas": [_persona(aldea, i) for i in p.parejas],
        "hijos": [_persona(aldea, i) for i in p.hijos],
        "amigos": amigos,
        "rivales": rivales,
        "historial": [{"turno": t, "opcion": op, "descripcion": desc, "motivo": mot, "decidido_por": quien,
                       "confianza": conf} for t, op, desc, mot, quien, conf in reversed(h.historial)],
        "vida": vida(aldea, p),
    }


def _turno_de_llegada(p) -> int:
    """Cuándo empezó a vivir en esta aldea: al fundarla, al nacer o al llegar de fuera."""
    if p.llegada == "nacimiento":
        return p.nacimiento
    return next((t for t, tipo, _ in p.hitos if tipo in ("forastero", "colono")), 0)


SALIDA = {
    "vejez": "Muere de vejez", "hambre": "Muere de hambre", "enfermedad": "Muere por una enfermedad",
    "agotamiento": "Muere de agotamiento", "monstruos": "Muere en un ataque de monstruos",
    "marcha": "Se marcha a vivir a otra aldea",
}


def vida(aldea: Aldea, p) -> list[dict]:
    """La vida de una persona por orden: cómo llegó, sus momentos, sus hijos y cómo se fue."""
    a = "a" if p.sexo == "m" else "o"
    momentos = []
    if p.llegada == "fundador":
        momentos.append((0, "llegada", f"Es {'una' if p.sexo == 'm' else 'uno'} de los fundadores de la aldea."))
    elif p.llegada == "nacimiento":
        padres = [aldea.registro[i].nombre for i in (p.padres or ()) if i in aldea.registro]
        de = f", hij{a} de {' y '.join(padres)}" if padres else ""
        momentos.append((p.nacimiento, "nacimiento", f"Nace en la aldea{de}."))
    # Los cambios de oficio seguidos se cuentan en una sola línea, y de las exploraciones solo la vuelta.
    oficios = []
    for t, tipo, texto in p.hitos:
        cambio = re.search(r"deja de ser (.+) y pasa a ser (.+)\.$", texto) if tipo == "oficio" else None
        if cambio:
            if oficios and momentos and momentos[-1][1] == "oficio":
                momentos.pop()
            else:
                oficios = [cambio.group(1)]
            oficios.append(cambio.group(2))
            lista = ", ".join(oficios[:-1]) + " y " + oficios[-1]
            momentos.append((t, "oficio", f"Cambia de oficio: {lista}." if len(oficios) > 2 else
                             f"Deja de ser {oficios[0]} y pasa a ser {oficios[1]}."))
        elif tipo == "explora" and " sale a explorar" in texto:
            continue
        else:
            momentos.append((t, tipo, texto))
    for i in p.hijos:
        hijo = aldea.registro.get(i)
        if hijo:
            momentos.append((hijo.nacimiento, "hijo", f"Nace {'su hija' if hijo.sexo == 'm' else 'su hijo'} {hijo.nombre}."))
    if p.salida is not None:
        edad = (p.salida - p.nacimiento) // m.TURNOS_POR_ANO
        momentos.append((p.salida, "salida", f"{SALIDA.get(p.causa, 'Deja la aldea')} a los {edad} años."))
    # El fundador va siempre primero, aunque tuviera hijos antes de fundar la aldea.
    momentos.sort(key=lambda x: (x[1] != "llegada", x[0]))
    return [{"turno": t, "tipo": tipo, "texto": texto, "edad": max(0, (t - p.nacimiento) // m.TURNOS_POR_ANO)}
            for t, tipo, texto in momentos]


def arbol_publico(aldea: Aldea) -> dict:
    """Todas las personas que han vivido en la aldea, para dibujar el árbol genealógico."""
    personas = []
    for p in aldea.registro.values():
        h = aldea.habitantes.get(p.id)
        personas.append({
            "id": p.id, "nombre": p.nombre, "sexo": p.sexo, "llegada": p.llegada,
            "padres": list(p.padres) if p.padres else [], "parejas": p.parejas, "hijos": p.hijos,
            "nacimiento": p.nacimiento, "salida": p.salida, "causa": p.causa,
            "oficio": h.de_oficio() if h and h.oficio else (
                m.FEMENINO_OFICIO.get(p.oficio, p.oficio) if p.sexo == "m" else p.oficio),
            "vivo": h is not None, "edad": int(h.edad(aldea.turno)) if h else None,
            "personaje": personaje(h, aldea.turno) if h else p.aspecto,
            "vida": vida(aldea, p),
        })
    return {"turno": aldea.turno, "turnos_por_ano": m.TURNOS_POR_ANO, "personas": personas}
