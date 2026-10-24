from collections import Counter

import pytest

from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea
from jevmura.motor.decisores import Decision, DecisorReglas, Opcion
from jevmura.motor.mapa import ALTO, ANCHO, generar_mapa


def test_mapa_tiene_cada_zona_en_su_sitio():
    mapa = generar_mapa(3)
    assert len(mapa.casillas) == ALTO and all(len(fila) == ANCHO for fila in mapa.casillas)
    for x, y in mapa.orillas:
        assert mapa.casillas[y][x] != "agua" and mapa.casillas[y][x + 1] == "agua"
    for x, y in mapa.solares + mapa.muralla:
        assert mapa.casillas[y][x] not in ("agua", "bosque", "campo")
    assert all(mapa.casillas[y][x] == "bosque" for x, y in mapa.arboles)
    assert len(mapa.muralla) == m.TRAMOS_MURALLA
    px, py = mapa.puente                     # el puente cruza el río y el camino llega a él
    assert mapa.casillas[py][px] == "agua" and mapa.casillas[py][px - 3] == "camino"


def test_misma_semilla_mismo_mundo():
    a, b = Aldea(5), Aldea(5)
    a.avanzar(3000)
    b.avanzar(3000)
    assert [(h.nombre, round(h.x, 6), round(h.y, 6), h.accion) for h in a.habitantes.values()] == \
           [(h.nombre, round(h.x, 6), round(h.y, 6), h.accion) for h in b.habitantes.values()]
    assert a.comida == b.comida and [s.texto for s in a.cronica] == [s.texto for s in b.cronica]


def test_limites_de_poblacion_y_casas_durante_años():
    aldea = Aldea(3)
    for _ in range(8 * m.DIAS_POR_ANO):
        aldea.avanzar(m.TURNOS_POR_DIA)
        assert 0 < len(aldea.habitantes) <= m.POBLACION_MAXIMA
        ocupadas = Counter(h.casa for h in aldea.habitantes.values() if h.casa is not None)
        assert all(n <= m.CAPACIDAD_CASA for n in ocupadas.values())
        assert all(0 <= v <= 100 for h in aldea.habitantes.values()
                   for v in (h.hambre, h.energia, h.salud, h.animo))


def test_cronica_guarda_un_año_y_cada_año_deja_resumen():
    aldea = Aldea(1)
    aldea.avanzar(2 * m.TURNOS_POR_ANO)
    assert all(s.turno > aldea.turno - m.TURNOS_POR_ANO for s in aldea.cronica)
    assert [r["ano"] for r in aldea.resumenes] == [1, 2]


def test_registro_guarda_a_todos_para_el_arbol_genealogico():
    aldea = Aldea(3)
    aldea.avanzar(40 * m.TURNOS_POR_ANO)
    reg = aldea.registro
    assert set(aldea.habitantes) <= set(reg)
    assert any(p.salida for p in reg.values()) and any(p.llegada == "nacimiento" for p in reg.values())
    for p in reg.values():
        assert (p.salida is None) == (p.id in aldea.habitantes)
        for padre in p.padres or ():
            assert p.id in reg[padre].hijos
        for hijo in p.hijos:
            assert p.id in reg[hijo].padres
        for pareja in p.parejas:
            assert p.id in reg[pareja].parejas


def test_de_noche_todos_duermen():
    aldea = Aldea(2)
    aldea.avanzar(3 * m.TURNOS_POR_HORA + m.TURNOS_POR_DIA)     # las 3:00 del segundo día
    presentes = [h for h in aldea.habitantes.values() if not h.fuera_hasta]
    assert presentes and all(h.accion in ("dormir", "explorar", "marcharse") for h in presentes)


def test_cada_adulto_decide_cada_5_minutos_mientras_esta_despierto():
    aldea = Aldea(4)
    aldea.avanzar(m.TURNOS_POR_DIA)
    adultos = sum(1 for h in aldea.habitantes.values() if h.adulto(aldea.turno))
    antes = sum(aldea.decisiones.values())
    aldea.avanzar(m.TURNOS_POR_DIA)
    despierto = (m.HORA_DORMIR - m.HORA_DESPERTAR) * m.TURNOS_POR_HORA
    esperadas = adultos * despierto / m.TURNOS_ENTRE_DECISIONES
    assert 0.6 * esperadas <= sum(aldea.decisiones.values()) - antes <= 1.05 * esperadas


def test_un_mundo_que_empieza_por_la_manana_decide_desde_el_principio():
    aldea = Aldea(4, hora_inicial=7)
    assert aldea.hora == 7 and not aldea.de_noche()
    aldea.avanzar(m.TURNOS_ENTRE_DECISIONES)
    assert sum(aldea.decisiones.values()) > 0
    assert all(h.edad(aldea.turno) >= 0 for h in aldea.habitantes.values())


def test_decisor_de_reglas_elige_una_opcion_de_la_lista():
    aldea = Aldea(0)
    aldea.avanzar(7 * m.TURNOS_POR_HORA)
    h = next(h for h in aldea.habitantes.values() if h.adulto(aldea.turno))
    situacion = aldea.situacion(h)
    decisor = DecisorReglas()
    for _ in range(50):
        d = decisor.decidir(situacion)
        assert d.opcion in situacion.opciones and d.motivo


class DecisorRoto:
    nombre = "jev"

    def decidir(self, situacion):
        raise TimeoutError("OpenRouter no responde")


class DecisorInventa:
    nombre = "jev"

    def decidir(self, situacion):
        return Decision(Opcion("volar", "volar", "Salir volando"), "Porque sí")


@pytest.mark.parametrize("decisor", [DecisorRoto(), DecisorInventa()])
def test_si_jev_falla_decide_el_respaldo(decisor):
    aldea = Aldea(0, decisor=decisor)
    aldea.avanzar(m.TURNOS_POR_DIA)
    assert aldea.decisiones["respaldo"] > 0 and aldea.decisiones["jev"] == 0
    assert aldea.fallos_seguidos == aldea.decisiones["respaldo"]
    assert len(aldea.habitantes) > 0


def test_las_rutas_rodean_casas_y_muralla_y_cruzan_el_rio_por_el_puente():
    from jevmura.motor.caminos import BLOQUEADA, Caminos

    aldea = Aldea(2026)
    mapa, caminos = aldea.mapa, Caminos(aldea.mapa)
    aldea.muralla = 20
    caminos.preparar(aldea.casas, aldea.muralla)
    w = caminos.ancho
    # De la plaza al bosque oeste: sale por la puerta, sin pisar casas ni tramos de muralla.
    ruta = caminos.ruta(mapa.almacen, (2, mapa.almacen[1]))
    assert ruta and all(caminos.coste[y * w + x] != BLOQUEADA for x, y in ruta)
    # Del oeste del río al este: el único paso es el puente.
    px, py = mapa.puente
    ruta = caminos.ruta((px - 6, py), (px + 6, py))
    agua = [(x, y) for x, y in ruta if mapa.casillas[y][x] == "agua"]
    assert agua and all(y in (py, py + 1) for _, y in agua)


def test_si_no_llega_la_piedra_para_la_muralla_se_pide_cantero():
    aldea = Aldea(2026)
    aldea.piedra, aldea.madera, aldea.muralla = 16, 200, 0
    for h in aldea.habitantes.values():
        if h.oficio == "cantero":
            h.oficio = "campesino"
    if not aldea._falta_casa():
        assert "cantero" in aldea.estado().oficios_necesarios
    aldea.piedra = m.OBRAS["casa"]["piedra"] + m.OBRAS["muralla"]["piedra"]
    assert "cantero" not in aldea.estado().oficios_necesarios
