"""Simulación rápida del mundo grande, para ajustar el ritmo de crecimiento.

Los pueblos, villas y ciudades avanzan día a día con todas las reglas del mundo (fundaciones,
reparto de gente, comercio, contagios y consejos con las reglas). Las aldeas detalladas no se
simulan, porque serían horas de cálculo y como mucho tienen 20 personas cada una.

Uso: python -m jevmura.mundo.simular [años] [semilla] [carpeta donde guardarlo]
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

from ..motor import modelos as m
from .mundo import Mundo


def simular(anos: int = 90, semilla: int = 2026, cada: int = 5, carpeta: str | None = None) -> list[tuple]:
    """Con `carpeta`, el mundo simulado se guarda allí (para abrirlo con el servidor y mirarlo)."""
    carpeta = carpeta or tempfile.mkdtemp()
    mundo = Mundo(os.path.join(carpeta, "mundo.db"), semilla=semilla, segundos_por_turno=0)
    for _ in range(3):                           # el arranque: 4 aldeas juntas, como pasará en la partida
        id = mundo.fundar(1)
        while len(mundo.aldeas[id].habitantes) < 10:
            mundo.aldeas[id]._forastero()
    filas = []
    principal = mundo.aldeas[1]
    for dia in range(anos * m.DIAS_POR_ANO):
        principal.turno += m.TURNOS_POR_DIA       # el reloj del mundo es el de La aldea
        for g in mundo.grandes.values():
            g.turno = principal.turno - 1
            g.paso()
            if (g.dia % m.DIAS_POR_ESTACION) == 0:
                g.aplicar(g.eleccion_reglas(), "reglas")
        mundo._crecer()
        if dia % (m.DIAS_POR_ANO * cada) == 0:
            tipos = {t: sum(1 for i in mundo.meta if mundo.tipo(i) == t) for t in ("aldea", "pueblo", "villa", "ciudad")}
            por_tipo = {t: sum(mundo.poblacion(i) for i in mundo.meta if mundo.tipo(i) == t) for t in ("pueblo", "villa", "ciudad")}
            filas.append((dia // m.DIAS_POR_ANO, mundo.resumen()["poblacion"], tipos, por_tipo))
    for g in mundo.grandes.values():
        g.turno = principal.turno
    mundo.guardar()
    return filas


if __name__ == "__main__":
    anos = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    carpeta = sys.argv[3] if len(sys.argv) > 3 else None
    inicio = time.perf_counter()
    for ano, poblacion, tipos, por_tipo in simular(anos, semilla, carpeta=carpeta):
        print(f"año {ano:3d}: {poblacion:9,d} personas  {tipos}  gente: {por_tipo}".replace(",", "."))
    print(f"({time.perf_counter() - inicio:.0f} s)")
