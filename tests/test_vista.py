import json

from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea
from jevmura.vista import arbol_publico, estado_publico, ficha_habitante, mapa_publico, personaje


def test_mapa_y_estado_se_pueden_mandar_por_websocket():
    aldea = Aldea(1)
    aldea.avanzar(3 * m.TURNOS_POR_ANO)
    mapa = json.loads(json.dumps(mapa_publico(aldea)))
    estado = json.loads(json.dumps(estado_publico(aldea)))
    assert len(mapa["casillas"]) == mapa["alto"] and all(len(f) == mapa["ancho"] for f in mapa["casillas"])
    assert len(mapa["tramos"]) == m.TRAMOS_MURALLA
    assert estado["poblacion"] == len(estado["habitantes"]) == len(aldea.habitantes)
    assert all(int(i) < len(mapa["arboles"]) for i in estado["arboles_cortados"])


def test_ficha_y_arbol_se_pueden_mandar_y_enlazan_bien():
    aldea = Aldea(3)
    aldea.avanzar(20 * m.TURNOS_POR_ANO)
    arbol = json.loads(json.dumps(arbol_publico(aldea)))
    ids = {p["id"] for p in arbol["personas"]}
    assert ids == set(aldea.registro) and any(not p["vivo"] for p in arbol["personas"])
    for h in aldea.habitantes.values():
        ficha = json.loads(json.dumps(ficha_habitante(aldea, h.id)))
        assert ficha["nombre"] == h.nombre and len(ficha["historial"]) <= 5
        assert all(p["id"] in ids for p in ficha["padres"] + ficha["hijos"] + ficha["parejas"])
    assert ficha_habitante(aldea, 10**6) is None


def test_cada_habitante_se_dibuja_segun_su_edad_y_oficio():
    aldea = Aldea(0)
    h = next(iter(aldea.habitantes.values()))
    h.nacimiento = aldea.turno - 5 * m.TURNOS_POR_ANO
    assert personaje(h, aldea.turno) == "Child"
    h.nacimiento = aldea.turno - 70 * m.TURNOS_POR_ANO
    assert personaje(h, aldea.turno).startswith("Old")
    h.nacimiento = aldea.turno - 30 * m.TURNOS_POR_ANO
    h.oficio = "guardia"
    assert personaje(h, aldea.turno) in ("Samurai", "SamuraiBlue", "NinjaRed")


def test_los_ataques_se_pueden_dibujar_unos_minutos():
    from jevmura.motor.aldea import MONSTRUOS, TURNOS_ATAQUE_VISIBLE

    aldea = Aldea(5)
    while aldea.ataque is None:
        aldea.avanzar(m.TURNOS_POR_DIA // 4)
    a = estado_publico(aldea)["ataque"] or aldea.ataque
    assert a["monstruo"] in {d for _, _, d in MONSTRUOS} and 1 <= a["cuantos"] <= 8
    assert tuple(a["entrada"]) in {tuple(s) for s in aldea.mapa.salidas}
    aldea.avanzar(TURNOS_ATAQUE_VISIBLE + 1)
    assert estado_publico(aldea)["ataque"] is None or estado_publico(aldea)["ataque"]["turno"] != a["turno"]
