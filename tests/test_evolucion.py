from jevmura.guardado import Guardado
from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea
from jevmura.motor.evolucion import EDIFICIOS, ORDEN, REPARAR_EDIFICIO
from jevmura.vista import estado_publico


def con_recursos(a: Aldea) -> Aldea:
    a.comida, a.madera, a.piedra = 400.0, 250.0, 250.0
    return a


def test_la_muralla_completa_abre_la_etapa_2():
    a = Aldea(1)
    assert a.etapa == 1 and a.disponibles() == []
    a.muralla = m.TRAMOS_MURALLA
    a._comprobar_etapa()
    assert a.etapa == 2
    assert set(a.disponibles()) == {n for n in ORDEN if EDIFICIOS[n]["etapa"] == 2}
    assert any(s.tipo == "etapa" for s in a.cronica)


def test_un_edificio_se_construye_y_da_su_efecto():
    a = con_recursos(Aldea(2))
    a.muralla, a.etapa = m.TRAMOS_MURALLA, 2
    tope_antes = a.tope("comida")
    a.empezar_evolucion("edificio", "granero")
    assert a.obra.tipo == "edificio" and a.madera == 250 - EDIFICIOS["granero"]["madera"]
    for _ in range(EDIFICIOS["granero"]["turnos"]):
        a._construir()
    assert a.obra is None and a.edificios["granero"] == 100
    assert a.tope("comida") > tope_antes


def test_los_cinco_edificios_abren_la_etapa_3_y_luego_la_4():
    a = Aldea(3)
    a.muralla, a.etapa = m.TRAMOS_MURALLA, 2
    for n in ORDEN:
        if EDIFICIOS[n]["etapa"] == 2:
            a.edificios[n] = 100.0
    a._comprobar_etapa()
    assert a.etapa == 3
    for n in ORDEN:
        a.edificios[n] = 100.0
    a._comprobar_etapa()
    assert a.etapa == 4
    a.casas[0].piedra = False
    tipos = [t for t, _ in a._candidatas()]
    assert "reforzar" in tipos and "casa_piedra" in tipos and "faroles" in tipos


def test_un_edificio_estropeado_rinde_la_mitad_y_se_repara():
    a = con_recursos(Aldea(4))
    a.etapa = 2
    a.edificios["taller"] = REPARAR_EDIFICIO - 1
    a._recalcular_efectos()
    assert a.efecto("taller") == 0.5
    assert a._candidatas()[0] == ("reparar", "taller")
    a.empezar_evolucion("reparar", "taller")
    while a.obra:
        a._construir()
    assert a.edificios["taller"] == 100 and a.efecto("taller") == 1.0


def test_el_desgaste_baja_el_estado_con_los_dias():
    a = Aldea(5)
    a.edificios["pozo"] = 100.0
    estado_casa = a.casas[0].estado
    for _ in range(m.DIAS_POR_ANO):
        a.dia_evolucion()
    assert a.edificios["pozo"] < 90 and a.casas[0].estado < estado_casa


def test_el_consejo_elige_con_las_reglas_y_marca_el_plan():
    a = con_recursos(Aldea(6))
    a.muralla, a.etapa = m.TRAMOS_MURALLA, 2
    eleccion = a.eleccion_consejo_reglas()
    assert eleccion.startswith("obra:")
    a.aplicar_consejo(eleccion, "reglas")
    assert a.plan == eleccion.split(":")[1] and a.consejo["quien"] == "reglas"
    assert a._candidatas()[0] == ("edificio", a.plan)


def test_la_evolucion_se_guarda_y_se_carga(tmp_path):
    a = Aldea(7)
    a.etapa, a.edificios, a.reforzados, a.faroles, a.plan = 3, {"pozo": 70.0}, 2, 1, "templo"
    a.casas[0].piedra = True
    g = Guardado(str(tmp_path / "a.db"))
    g.guardar(a)
    b = g.cargar()
    assert (b.etapa, b.edificios, b.reforzados, b.faroles, b.plan) == (3, {"pozo": 70.0}, 2, 1, "templo")
    assert b.casas[0].piedra and b.efecto("pozo") == 1.0


def test_la_web_recibe_los_edificios_y_la_etapa():
    a = Aldea(8)
    a.etapa = 2
    a.edificios["granero"] = 40.0
    e = estado_publico(a)
    assert e["evolucion"]["etapa"] == 2
    granero = next(c for c in e["casas"] if c.get("modelo") == "granero")
    assert granero["estado"] == 40
