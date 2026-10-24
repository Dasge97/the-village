"""Presupuesto de llamadas a Jev para todo el mundo: 5.000 al día real como máximo.

Se reparte en dos bolsas que se van llenando poco a poco a lo largo del día: 3.000 llamadas
para los vecinos de las aldeas y 2.000 para los consejos de pueblos, villas y ciudades. Cada
llamada gasta una. Si una bolsa se vacía, decide la regla hasta que vuelva a llenarse.

Las aldeas importantes (la que alguien mira y La aldea) pueden gastar hasta la última llamada;
las demás solo mientras quede más del 20 % de la bolsa, para no dejar sin Jev a las importantes.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from ..motor.decisores import Decision, Situacion

SEGUNDOS_DIA = 24 * 3600
LLAMADAS_DIA = {"vecinos": 3000, "consejos": 2000}
MINUTOS_DE_RESERVA = 30          # la bolsa guarda como mucho lo de media hora
RESERVA_IMPORTANTES = 0.2


class Presupuesto:
    def __init__(self, llamadas_dia: dict[str, int] | None = None, reloj: Callable[[], float] = time.monotonic):
        self.por_dia = dict(llamadas_dia or LLAMADAS_DIA)
        self.reloj = reloj
        self.activo = True                       # apagado desde el panel de administración: solo reglas
        self.capacidad = {k: max(1.0, v * MINUTOS_DE_RESERVA * 60 / SEGUNDOS_DIA) for k, v in self.por_dia.items()}
        self.bolsa = dict(self.capacidad)
        self.ultimo = reloj()
        self.gastadas = {k: 0 for k in self.por_dia}
        self.denegadas = {k: 0 for k in self.por_dia}

    def _llenar(self) -> None:
        ahora = self.reloj()
        pasado = max(0.0, ahora - self.ultimo)
        self.ultimo = ahora
        for k, v in self.por_dia.items():
            self.bolsa[k] = min(self.capacidad[k], self.bolsa[k] + v * pasado / SEGUNDOS_DIA)

    def cambiar(self, llamadas_dia: dict[str, int]) -> None:
        """Otro máximo de llamadas al día. Lo que quede en cada bolsa no pasa de su nuevo tope."""
        self._llenar()
        self.por_dia = dict(llamadas_dia)
        self.capacidad = {k: max(1.0, v * MINUTOS_DE_RESERVA * 60 / SEGUNDOS_DIA) for k, v in self.por_dia.items()}
        self.bolsa = {k: min(self.bolsa.get(k, 0.0), self.capacidad[k]) for k in self.por_dia}

    def gastar(self, bolsa: str, importante: bool = False) -> bool:
        """Gasta una llamada de la bolsa si se puede. Devuelve si se ha podido."""
        if not self.activo:
            self.denegadas[bolsa] += 1
            return False
        self._llenar()
        minimo = 1.0 if importante else max(1.0, self.capacidad[bolsa] * RESERVA_IMPORTANTES)
        if self.bolsa[bolsa] >= minimo:
            self.bolsa[bolsa] -= 1
            self.gastadas[bolsa] += 1
            return True
        self.denegadas[bolsa] += 1
        return False

    def resumen(self) -> dict:
        self._llenar()
        return {k: {"por_dia": self.por_dia[k], "quedan_ahora": round(self.bolsa[k], 1),
                    "gastadas": self.gastadas[k], "sin_presupuesto": self.denegadas[k]} for k in self.por_dia}


class DecisorConPresupuesto:
    """Decide con Jev si queda presupuesto; si no, con las reglas de la aldea. `quien` dice quién
    ha decidido la última vez («jev» o «presupuesto»), para la ficha del habitante."""

    nombre = "jev"

    def __init__(self, jev, reglas, presupuesto: Presupuesto, importante: Callable[[], bool]):
        self.jev = jev
        self.reglas = reglas
        self.presupuesto = presupuesto
        self.importante = importante
        self.quien = "jev"

    def decidir(self, situacion: Situacion) -> Decision:
        if self.presupuesto.gastar("vecinos", self.importante()):
            self.quien = "jev"
            return self.jev.decidir(situacion)
        self.quien = "presupuesto"
        return self.reglas.decidir(situacion)

    # Los totales de Jev son del decisor compartido; se guardan y se cargan con cada aldea.
    def __getattr__(self, nombre):
        if nombre in ("llamadas", "errores", "coste", "segundos"):
            return getattr(self.jev, nombre)
        raise AttributeError(nombre)

    def __setattr__(self, nombre, valor):
        if nombre in ("llamadas", "errores", "coste", "segundos"):
            setattr(self.jev, nombre, valor)
        else:
            super().__setattr__(nombre, valor)
