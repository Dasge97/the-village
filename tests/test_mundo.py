from jevmura.bucle import SEGUNDA, Mundo
from jevmura.motor import modelos as m
from jevmura.motor.aldea import Aldea
from jevmura.motor.decisores import DecisorReglas
from jevmura.mundo import zonas
from jevmura.mundo.presupuesto import DecisorConPresupuesto, Presupuesto


def marcharse(aldea, h):
    """Lo que hace el motor cuando alguien llega al borde del mapa para marcharse."""
    aldea.emigrantes.append({"id": h.id, "nombre": h.nombre, "sexo": h.sexo, "edad": h.edad(aldea.turno),
                             "oficio": h.oficio, "caracter": h.caracter, "aspecto": h.aspecto})
    aldea._quitar(h, "marcha")


def test_quien_se_marcha_funda_la_segunda_aldea_y_los_siguientes_se_unen(tmp_path):
    ruta = str(tmp_path / "mundo.db")
    mundo = Mundo(ruta, semilla=4, segundos_por_turno=0)
    primera = mundo.aldea
    a, b = [h for h in primera.habitantes.values() if h.oficio][:2]
    marcharse(primera, a)
    mundo.paso()
    assert len(mundo.aldeas) == 2
    segunda = mundo.aldeas[2]
    assert segunda.nombre == SEGUNDA and segunda.turno == primera.turno
    assert [h.nombre for h in segunda.habitantes.values()] == [a.nombre]
    assert segunda.registro[next(iter(segunda.habitantes))].llegada == "colono"
    assert any("funda" in t for _, _, t in primera.registro[a.id].hitos)
    assert mundo.meta[2]["zona"] in [list(z) for z in zonas.vecinas(*zonas.CENTRO)]

    marcharse(primera, b)
    mundo.paso()
    assert len(mundo.aldeas) == 2 and len(segunda.habitantes) == 2

    # Todas las aldeas y el mundo se guardan y se cargan, y siguen avanzando juntas.
    mundo.guardar()
    otra = Mundo(ruta)
    assert len(otra.aldeas) == 2 and otra.aldeas[2].nombre == SEGUNDA
    assert {h.nombre for h in otra.aldeas[2].habitantes.values()} == {a.nombre, b.nombre}
    for _ in range(2 * m.TURNOS_POR_DIA):
        otra.paso()
    assert otra.aldeas[1].turno == otra.aldeas[2].turno


def test_con_la_hija_llena_se_funda_otra_aldea_en_otra_zona(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=9, segundos_por_turno=0)
    primera = mundo.aldea
    marcharse(primera, next(h for h in primera.habitantes.values() if h.oficio))
    mundo.paso()
    hija = mundo.aldeas[2]
    while len(hija.habitantes) < m.POBLACION_MAXIMA:     # se llena con gente de fuera
        hija._forastero()
    marcharse(primera, next(h for h in primera.habitantes.values() if h.oficio))
    mundo.paso()
    assert len(mundo.aldeas) == 3 and mundo.meta[3]["madre"] == 1
    assert mundo.meta[3]["zona"] != mundo.meta[2]["zona"]
    assert mundo.meta[3]["bioma"] == zonas.bioma(primera.semilla, *mundo.meta[3]["zona"])
    assert mundo.aldeas[3].nombre.startswith("Aldea de ")


def test_una_aldea_llena_manda_gente_fuera_sin_esperar_a_jev():
    aldea = Aldea(6)
    while len(aldea.habitantes) < m.POBLACION_MAXIMA:
        aldea._forastero()
    for _ in range(10 * m.TURNOS_POR_DIA):
        aldea.paso()
        if aldea.emigrantes:
            break
    assert aldea.emigrantes


def test_el_presupuesto_reparte_las_llamadas_a_lo_largo_del_dia():
    ahora = [0.0]
    p = Presupuesto({"vecinos": 2880, "consejos": 0}, reloj=lambda: ahora[0])   # 2 por minuto
    gastadas = sum(p.gastar("vecinos") for _ in range(1000))
    assert gastadas < 100                     # al principio solo hay lo de media hora
    ahora[0] += 60
    assert p.gastar("vecinos", importante=True)
    # Sin bolsa, las aldeas que no importan no gastan; las importantes, hasta la última.
    while p.gastar("vecinos", importante=True):
        pass
    assert not p.gastar("vecinos")


def test_sin_presupuesto_deciden_las_reglas_y_se_dice_en_la_ficha():
    class JevFalso(DecisorReglas):
        nombre = "jev"

    p = Presupuesto({"vecinos": 0, "consejos": 0}, reloj=lambda: 0.0)
    p.bolsa["vecinos"] = 0
    aldea = Aldea(3)
    aldea.decisor = DecisorConPresupuesto(JevFalso(), aldea.respaldo, p, importante=lambda: False)
    aldea.avanzar(m.TURNOS_POR_DIA // 2)
    assert aldea.decisiones["presupuesto"] > 0 and aldea.decisiones["jev"] == 0


def _aldea_con_jovenes(mundo, madre):
    """Una aldea nueva junto a `madre`, con gente de fuera (forasteros) para poder repartir."""
    id = mundo.fundar(madre)
    aldea = mundo.aldeas[id]
    while len(aldea.habitantes) < 10:
        aldea._forastero()
    return id


def test_cuatro_aldeas_cerca_fundan_un_pueblo_que_crece_y_decide(tmp_path):
    ruta = str(tmp_path / "mundo.db")
    mundo = Mundo(ruta, semilla=11, segundos_por_turno=0)
    for _ in range(3):
        _aldea_con_jovenes(mundo, 1)
    mundo._crecer()
    pueblos = [i for i in mundo.meta if mundo.tipo(i) == "pueblo"]
    assert len(pueblos) == 1
    p = mundo.grandes[pueblos[0]]
    assert p.nombre.startswith("Pueblo de ") and p.poblacion >= 30 and len(p.notables) == 4
    assert any("Nace el primer pueblo del mundo: el Pueblo" in t for _, t, *_ in mundo.cronica)
    mundo._crecer()                                   # no se funda otro al lado
    assert len([i for i in mundo.meta if mundo.tipo(i) == "pueblo"]) == 1
    antes = p.poblacion
    for _ in range(3 * m.TURNOS_POR_ANO):
        p.paso()
        if p.toca_consejo():
            p.aplicar(p.eleccion_reglas(), "reglas")
    assert p.poblacion > antes and p.consejo["quien"] == "reglas"
    # El mundo con pueblo se guarda y se carga igual.
    mundo.guardar()
    otra = Mundo(ruta)
    q = otra.grandes[pueblos[0]]
    assert q.poblacion == p.poblacion and q.edificios == p.edificios and len(q.notables) == 4
    assert {a["tipo"] for a in otra.publico()["asentamientos"]} == {"aldea", "pueblo"}


def test_tres_pueblos_cerca_fundan_una_villa_y_tres_villas_una_ciudad(tmp_path):
    from jevmura.mundo.mundo import distancia

    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=13, segundos_por_turno=0)
    centro = tuple(mundo.meta[1]["zona"])
    pueblos = [mundo.fundar_grande("pueblo", centro, [25] * 300, [1]) for _ in range(3)]
    assert all(pueblos)
    mundo._crecer()
    villas = [i for i in mundo.meta if mundo.tipo(i) == "villa"]
    assert len(villas) == 1 and mundo.grandes[villas[0]].poblacion == 3 * 45
    assert all(distancia(mundo.meta[v]["zona"], centro) <= 6 for v in villas)
    for _ in range(2):
        mundo.fundar_grande("villa", centro, [25] * 3000, pueblos)
    mundo._crecer()
    ciudades = [i for i in mundo.meta if mundo.tipo(i) == "ciudad"]
    assert len(ciudades) == 1 and mundo.grandes[ciudades[0]].nombre.startswith("Ciudad de ")
    assert any("primera ciudad del mundo: la Ciudad" in m["texto"] for m in mundo.publico()["momentos"])


def test_las_caravanas_llevan_comida_al_que_le_falta(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=14, segundos_por_turno=0)
    centro = tuple(mundo.meta[1]["zona"])
    a = mundo.fundar_grande("pueblo", centro, [25] * 100, [1])
    b = mundo.fundar_grande("pueblo", centro, [25] * 100, [a])
    for i in (a, b):
        mundo.grandes[i].edificios["mercado"] = 1
    mundo.grandes[a].comida, mundo.grandes[b].comida = 9000, 10
    mundo._comercio()
    assert mundo.grandes[b].comida > 10 and any("caravana" in s.texto for s in mundo.grandes[b].cronica)


def test_el_mundo_guarda_una_foto_por_ano_y_los_grandes_momentos(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=15, segundos_por_turno=0)
    centro = tuple(mundo.meta[1]["zona"])
    mundo._crecer()
    mundo.fundar_grande("pueblo", centro, [25] * 1200, [1])
    mundo.aldeas[1].turno += m.TURNOS_POR_ANO
    mundo._crecer()
    anual = mundo.publico()["anual"]
    assert [f["ano"] for f in anual] == [1, 2]
    assert anual[-1]["gente"]["pueblo"] == 1200 and anual[-1]["asentamientos"]["aldea"] == 1
    assert any(t["texto"] == "El mundo llega a 1.000 personas." for t in mundo.publico()["momentos"])
    mundo.guardar()
    otro = Mundo(str(tmp_path / "mundo.db"), semilla=15, segundos_por_turno=0)
    assert otro.anual == anual


def test_cuando_se_acaban_los_nombres_dicen_donde_quedan(tmp_path):
    mundo = Mundo(str(tmp_path / "mundo.db"), semilla=16, segundos_por_turno=0)
    for i, n in enumerate(zonas.NOMBRES):
        mundo.meta[100 + i] = {"nombre": f"Pueblo de {n}"}
    assert mundo._nombre_nuevo("villa") == f"Villa de {zonas.NOMBRES[0]}{zonas.COLETILLAS[0]}"
