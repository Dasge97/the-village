from jevmura.guardado import Guardado
from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea
from jevmura.motor.formatos import FORMATOS_ALDEA, TAMANOS, generar
from jevmura.mundo.grande import nuevo


def test_cada_formato_de_aldea_tiene_todo_lo_que_usa_el_motor():
    for formato in FORMATOS_ALDEA:
        for semilla in range(4):
            mp = generar(semilla, "pradera", formato)
            (a0, a1), (h0, h1) = TAMANOS["aldea"]
            assert a0 <= len(mp.casillas[0]) <= a1 and h0 <= len(mp.casillas) <= h1
            assert len(mp.solares) == 12 and len(mp.tramos) == m.TRAMOS_MURALLA
            assert len(mp.sitios) == 8 and mp.huertos and mp.campos and mp.cantera and mp.orillas and mp.salidas
            ocupado = [mp.casillas[y][x] for x, y in mp.solares]
            assert all(t in ("hierba", "bosque") for t in ocupado)


def test_los_formatos_salen_distintos_y_del_mismo_tamano_nunca_dos_veces_igual():
    mapas = {f: generar(1, "pradera", f) for f in FORMATOS_ALDEA}
    assert len({tuple(mp.casillas[len(mp.casillas) // 2]) for mp in mapas.values()}) == len(FORMATOS_ALDEA)
    assert mapas["rio"].puentes and len(mapas["rio"].puentes) >= 2
    assert not mapas["claro"].puentes


def test_una_aldea_de_cada_formato_vive_y_se_guarda(tmp_path):
    for formato in FORMATOS_ALDEA:
        a = Aldea(3, formato=formato)
        a.avanzar(m.TURNOS_POR_DIA * 2)
        g = Guardado(str(tmp_path / f"{formato}.db"))
        g.guardar(a)
        b = g.cargar()
        assert b.formato == formato and b.mapa.casillas == a.mapa.casillas
        assert sorted(b.mapa.arboles) == sorted(a.mapa.arboles)


def test_pueblos_villas_y_ciudades_crecen_de_tamano_y_tienen_su_forma():
    tamanos = []
    for tipo in ("pueblo", "villa", "ciudad"):
        g = nuevo(5, "X", tipo, "pradera", 7, 0, [25] * 100)
        assert g._mapa is None                      # no se genera hasta que hace falta
        tamanos.append(len(g.mapa.casillas[0]) * len(g.mapa.casillas))
        assert g.mapa.formato == tipo and len(g.lotes) > 100
    assert tamanos == sorted(tamanos)
    assert nuevo(5, "X", "ciudad", "pradera", 7, 0, [25]).mapa.muros_fijos
