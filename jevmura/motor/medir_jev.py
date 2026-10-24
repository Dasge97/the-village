"""Simula unos días del mundo con Jev y con el decisor de reglas, y compara.

Uso: python -m jevmura.motor.medir_jev [días] [semilla]

Mide llamadas, coste, tiempo de respuesta y fallos de Jev, y calcula lo que costaría un día real
(24 días del mundo). Enseña qué tipo de acciones elige cada decisor y cómo queda la aldea.
"""

from __future__ import annotations

import sys
import time
from collections import Counter

from . import modelos as m
from .aldea import Aldea
from .jev import DecisorJev, clave_openrouter


def _simular(aldea: Aldea, dias: int) -> Counter:
    elegidas: Counter = Counter()
    aplicar = aldea._aplicar

    def contar(h, d, quien):
        elegidas[d.opcion.tipo] += 1
        aplicar(h, d, quien)

    aldea._aplicar = contar
    aldea.avanzar(dias * m.TURNOS_POR_DIA)
    return elegidas


def _linea(nombre: str, aldea: Aldea) -> str:
    return (f"{nombre:<8} población {len(aldea.habitantes):>2}  comida {aldea.comida:>4.0f}  "
            f"madera {aldea.madera:>4.0f}  piedra {aldea.piedra:>4.0f}  muralla {aldea.muralla:>2}  "
            f"casas {len(aldea.casas)}")


def main() -> None:
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    clave_openrouter()                       # se lee antes para no medir el SSH

    jev = DecisorJev()
    con_jev = Aldea(semilla, decisor=jev)
    inicio = time.perf_counter()
    tipos_jev = _simular(con_jev, dias)
    total = time.perf_counter() - inicio

    con_reglas = Aldea(semilla)
    tipos_reglas = _simular(con_reglas, dias)

    llamadas = jev.llamadas + jev.errores
    print(f"{dias} días del mundo, semilla {semilla}, {total:.0f} s reales de cálculo\n")
    print(f"llamadas a Jev   {llamadas}  (fallos {jev.errores}, decidió el respaldo {con_jev.decisiones['respaldo']})")
    print(f"coste            {jev.coste:.5f} USD, {jev.coste / max(jev.llamadas, 1):.7f} USD por decisión")
    print(f"tiempo           {jev.segundos / max(llamadas, 1):.2f} s por llamada")
    al_dia = jev.coste / dias * m.DIAS_POR_ANO
    print(f"un día real      unas {llamadas / dias * m.DIAS_POR_ANO:.0f} decisiones, {al_dia:.3f} USD; "
          f"al mes {al_dia * 30:.2f} USD\n")

    print(f"{'acción':<18}{'Jev':>6}{'reglas':>8}")
    for tipo in sorted(set(tipos_jev) | set(tipos_reglas), key=lambda t: -tipos_jev[t]):
        print(f"{tipo:<18}{tipos_jev[tipo]:>6}{tipos_reglas[tipo]:>8}")
    print()
    print(_linea("Jev", con_jev))
    print(_linea("reglas", con_reglas))
    print("\nCrónica con Jev:")
    for s in con_jev.cronica[-12:]:
        print(f"  día {s.turno // m.TURNOS_POR_DIA + 1}: {s.texto}")


if __name__ == "__main__":
    main()
