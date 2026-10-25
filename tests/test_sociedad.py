from jevmura.bucle import Mundo
from jevmura.motor import modelos as m
from jevmura.mundo.grande import Grande, nuevo
from jevmura.mundo.relaciones import ALIANZA, RIVALIDAD, clave


def ciudad(n=3000, tipo="villa", bioma="pradera") -> Grande:
    return nuevo(9, f"{tipo.capitalize()} de Prueba", tipo, bioma, 5, 0, [25] * n)


def test_los_impuestos_dan_oro_y_cambian_el_animo():
    g = ciudad()
    g.impuesto = "alto"
    antes = g.oro
    g.dia_sociedad()
    assert g.oro > antes
    assert g.animo_extra() < 0
    g.impuesto = "bajo"
    assert g.animo_extra() > 0


def test_un_avance_se_investiga_con_oro_y_se_queda_para_siempre():
    g = ciudad()
    g.edificios["granero"] = 1
    g.oro = 10_000
    assert "molinos" in g.avances_posibles()
    g.aplicar_sociedad("investigar:molinos")
    for _ in range(400):
        g._investigar()
    assert "molinos" in g.avances and g.investigando is None
    assert g.factor_comida() > 1


def test_un_monumento_tarda_y_sale_en_los_grandes_momentos():
    g = ciudad()
    g.madera, g.piedra, g.oro = 5000, 5000, 5000
    assert g.empezar_monumento("estatua")
    for _ in range(400):
        g._obra_monumento()
    assert "estatua" in g.monumentos and g.momentos


def test_el_descontento_trae_protestas_y_al_final_una_revuelta():
    g = ciudad()
    g.animo, g.impuesto = 0.2, "alto"
    for _ in range(400):
        g.animo = 0.2
        g._descontento()
    assert g.impuesto == "bajo" or g.protesta or g.descontento >= 0.5


def test_el_consejo_ve_las_opciones_nuevas():
    g = ciudad()
    g.edificios["granero"] = 1
    ops = g.opciones()
    assert any(o.startswith("investigar:") for o in ops)
    assert any(o.startswith("impuestos:") for o in ops)
    assert "construir:herreria" in ops


def test_la_vida_social_se_guarda():
    g = ciudad()
    g.oro, g.impuesto, g.avances, g.monumentos = 123.0, "bajo", ["molinos"], ["estatua"]
    h = Grande.de_datos(g.a_datos())
    assert (h.oro, h.impuesto, h.avances, h.monumentos) == (123.0, "bajo", ["molinos"], ["estatua"])


def test_alianzas_rivalidades_y_tributos(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=21, segundos_por_turno=0)
    centro = tuple(mundo.meta[1]["zona"])
    a = mundo.fundar_grande("villa", centro, [25] * 3000, [1])
    b = mundo.fundar_grande("villa", centro, [25] * 3000, [a])
    p = mundo.fundar_grande("pueblo", centro, [25] * 50, [a])
    mundo.relaciones[clave(a, b)] = ALIANZA + 30
    mundo._estacion_relaciones()
    assert clave(a, b) in mundo.alianzas
    assert mundo.grandes[a].proteccion > 0
    assert mundo.relaciones_de(a)["aliados"][0]["id"] == b
    mundo.relaciones[clave(a, b)] = RIVALIDAD - 50
    mundo._estacion_relaciones()
    assert clave(a, b) not in mundo.alianzas
    mundo.grandes[a].edificios["cuartel"] = 20
    for _ in range(200):
        mundo._tributos(mundo._vecinos_grandes(), mundo.grandes[a].rng)
        if p in mundo.vasallos:
            break
    assert mundo.vasallos.get(p) in (a, b)
    mundo.guardar()
    otro = Mundo(str(tmp_path / "mundo.db"), semilla=21, segundos_por_turno=0)
    assert otro.vasallos == mundo.vasallos


def test_un_dia_entero_de_un_mundo_con_todo_no_falla(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=22, segundos_por_turno=0)
    centro = tuple(mundo.meta[1]["zona"])
    for _ in range(3):
        mundo.fundar_grande("ciudad", centro, [25] * 4000, [1])
    for _ in range(m.TURNOS_POR_DIA * m.DIAS_POR_ESTACION + 2):
        mundo.paso()
    assert mundo.publico()["poblacion"] > 0
