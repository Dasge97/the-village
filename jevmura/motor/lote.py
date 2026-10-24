"""Simula muchos años de varias aldeas con el decisor de reglas y muestra cómo evolucionan.

Uso: python -m jevmura.motor.lote [años] [aldeas] [--detalle]

Sirve para comprobar que la aldea aguanta sin vaciarse y sin quedarse siempre en 20 habitantes.
Cada aldea usa una semilla distinta y se calcula en un núcleo del procesador. Con `--detalle`
muestra además el resumen de cada año de la primera aldea.
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from statistics import mean

from . import modelos as m
from .aldea import Aldea


def _simular(args: tuple[int, int]) -> dict:
    semilla, anos = args
    inicio = time.perf_counter()
    aldea = Aldea(semilla)
    poblaciones = []
    for _ in range(anos * m.DIAS_POR_ANO):
        aldea.avanzar(m.TURNOS_POR_DIA)
        poblaciones.append(len(aldea.habitantes))
    return {"semilla": semilla, "resumenes": aldea.resumenes, "poblaciones": poblaciones,
            "decisiones": sum(aldea.decisiones.values()), "segundos": time.perf_counter() - inicio,
            "oficios": Counter(h.oficio for h in aldea.habitantes.values())}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    anos = int(args[0]) if args else 100
    n = int(args[1]) if len(args) > 1 else 4
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(_simular, [(s, anos) for s in range(n)]))

    print(f"{n} aldeas, {anos} años cada una\n")
    print(f"{'semilla':<9}{'min':>5}{'media':>7}{'max':>5}{'en 20':>8}{'< 4':>6}"
          f"{'nac.':>6}{'muert.':>8}{'marchas':>9}{'decis./día real':>17}{'segundos':>10}")
    for r in res:
        p = r["poblaciones"]
        muertes = sum(sum(a["muertes"].values()) for a in r["resumenes"])
        print(f"{r['semilla']:<9}{min(p):>5}{mean(p):>7.1f}{max(p):>5}"
              f"{sum(x >= m.POBLACION_MAXIMA for x in p) / len(p):>8.0%}{sum(x < 4 for x in p) / len(p):>6.0%}"
              f"{sum(a['nacimientos'] for a in r['resumenes']):>6}{muertes:>8}"
              f"{sum(a['marchas'] for a in r['resumenes']):>9}"
              f"{r['decisiones'] / anos:>17.0f}{r['segundos']:>10.0f}")

    causas: Counter = Counter()
    for r in res:
        for a in r["resumenes"]:
            causas.update(a["muertes"])
    total = sum(causas.values()) or 1
    print("\nmuertes por causa: " + ", ".join(f"{c} {v / total:.0%}" for c, v in causas.most_common()))
    print("\n'en 20': parte de los días con la aldea llena. '< 4': parte de los días con menos de 4 habitantes.")
    print("Un año del mundo es un día real, así que 'decis./día real' es lo que se pediría a Jev cada día.")

    if "--detalle" in sys.argv:
        print(f"\nAldea {res[0]['semilla']}, año a año:")
        print(f"{'año':>4}{'pob.':>6}{'nac.':>6}{'muert.':>8}{'casas':>7}{'mur.':>6}"
              f"{'comida':>8}{'madera':>8}{'piedra':>8}{'ataques':>9}")
        for a in res[0]["resumenes"]:
            print(f"{a['ano']:>4}{a['poblacion']:>6}{a['nacimientos']:>6}{sum(a['muertes'].values()):>8}"
                  f"{a['casas']:>7}{a['muralla']:>6}{a['comida']:>8}{a['madera']:>8}{a['piedra']:>8}{a['ataques']:>9}")


if __name__ == "__main__":
    main()
