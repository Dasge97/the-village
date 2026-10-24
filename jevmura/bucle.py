"""Hace avanzar el mundo en tiempo real: un turno cada 10 segundos y un guardado cada 30 turnos.

El mundo y sus asentamientos están en `jevmura/mundo/mundo.py`; aquí solo se prueba sin web.

Al arrancar carga el mundo de la base de datos. Si no existe, crea uno nuevo con la semilla
indicada. Si se retrasa (por ejemplo, porque Jev ha tardado), no intenta recuperar turnos: sigue
desde donde está.

Uso para probar sin web: python -m jevmura.bucle [--db ruta] [--semilla N] [--jev] [--rapido]
Con `--rapido` no espera entre turnos. Enseña la crónica a medida que pasa.
"""

from __future__ import annotations

import argparse

from .motor import modelos as m
from .motor.aldea import Aldea
from .mundo.mundo import SEGUNDA, Mundo  # noqa: F401  (se importan desde aquí en otros sitios)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="datos/mundo.db")
    p.add_argument("--semilla", type=int, default=0)
    p.add_argument("--jev", action="store_true")
    p.add_argument("--rapido", action="store_true")
    args = p.parse_args()

    import os
    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    decisor = None
    if args.jev:
        from .motor.jev import DecisorJev
        decisor = DecisorJev()
    mundo = Mundo(args.db, args.semilla, decisor, 0.0 if args.rapido else m.TURNO_SEGUNDOS)
    a = mundo.aldea
    print(f"Año {a.ano}, {a.estacion}, {a.hora:04.1f} h, {len(a.habitantes)} habitantes. Ctrl+C para parar.")
    vistos = len(a.cronica)

    def contar(aldea: Aldea, n: int) -> None:
        nonlocal vistos
        if n != 1:
            return
        vistos = min(vistos, len(aldea.cronica))   # la crónica se recorta una vez al día
        for s in aldea.cronica[vistos:]:
            dia = s.turno // m.TURNOS_POR_DIA
            estacion = m.ESTACIONES[(dia % m.DIAS_POR_ANO) // m.DIAS_POR_ESTACION]
            hora = (s.turno % m.TURNOS_POR_DIA) / m.TURNOS_POR_HORA
            print(f"año {dia // m.DIAS_POR_ANO + 1} {estacion} {hora:04.1f} h  {s.texto}")
        vistos = len(aldea.cronica)

    mundo.al_avanzar.append(contar)
    try:
        mundo.ejecutar()
    except KeyboardInterrupt:
        with mundo.cerrojo:
            mundo.guardar()
        print(f"\nGuardado en el turno {mundo.aldea.turno}.")


if __name__ == "__main__":
    main()
