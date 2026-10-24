from dataclasses import asdict

from jevmura.guardado import Guardado
from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea


def foto(aldea: Aldea) -> dict:
    return {
        "turno": aldea.turno,
        "habitantes": [asdict(h) for h in aldea.habitantes.values()],
        "recursos": (aldea.comida, aldea.madera, aldea.piedra, aldea.peces, aldea.muralla),
        "casas": [asdict(c) for c in aldea.casas],
        "relaciones": dict(aldea.relaciones),
        "cronica": [s.texto for s in aldea.cronica],
        "registro": {k: asdict(p) for k, p in aldea.registro.items()},
        "arboles": dict(aldea.mapa.arboles),
    }


def test_al_cargar_el_mundo_sigue_igual_que_si_no_se_hubiera_parado(tmp_path):
    original = Aldea(7)
    guardado = Guardado(str(tmp_path / "mundo.db"))
    for _ in range(5 * m.DIAS_POR_ANO):          # guardando cada 30 turnos, como el servidor
        for _ in range(m.TURNOS_POR_DIA // m.TURNOS_ENTRE_DECISIONES):
            original.avanzar(m.TURNOS_ENTRE_DECISIONES)
            guardado.guardar(original)
    cargada = guardado.cargar()
    assert foto(cargada) == foto(original)
    assert cargada.resumenes == original.resumenes

    original.avanzar(3 * m.TURNOS_POR_DIA)
    cargada.avanzar(3 * m.TURNOS_POR_DIA)
    assert foto(cargada) == foto(original)


def test_la_base_de_datos_solo_guarda_un_año_de_cronica(tmp_path):
    aldea = Aldea(2)
    guardado = Guardado(str(tmp_path / "mundo.db"))
    for _ in range(3 * m.DIAS_POR_ANO):
        aldea.avanzar(m.TURNOS_POR_DIA)
        guardado.guardar(aldea)
    turnos = [t for (t,) in guardado.db.execute("SELECT turno FROM cronica")]
    assert turnos and min(turnos) > aldea.turno - m.TURNOS_POR_ANO
    assert [r["ano"] for r in guardado.resumenes()] == [1, 2, 3]
    assert {p.id for p in guardado.personas()} == set(aldea.registro)


def test_los_totales_de_jev_no_vuelven_a_cero_al_reiniciar(tmp_path):
    from jevmura.motor.decisores import DecisorReglas

    class ConContadores(DecisorReglas):
        def __init__(self):
            super().__init__()
            self.llamadas, self.errores, self.coste, self.segundos = 0, 0, 0.0, 0.0

    aldea = Aldea(4, ConContadores())
    aldea.decisor.llamadas, aldea.decisor.coste = 39, 0.0022
    guardado = Guardado(str(tmp_path / "mundo.db"))
    guardado.guardar(aldea)
    cargada = guardado.cargar(ConContadores())
    assert (cargada.decisor.llamadas, cargada.decisor.coste) == (39, 0.0022)
