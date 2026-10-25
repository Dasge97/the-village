<div align="center">

# The Village · La aldea

Un banco de pruebas para **Jev**, el modelo de decisiones de OpenRouter.<br>
Cada habitante de una aldea decide su vida con Jev. Lo ves en directo en el navegador.

[English](README.md) · **Español**

[![Versión](https://img.shields.io/badge/versi%C3%B3n-3.4-2ea44f)](web/src/versiones.js)
[![Jev](https://img.shields.io/badge/Jev-typesafe%2Fjev--1.14-8A2BE2)](https://openrouter.ai)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![PixiJS](https://img.shields.io/badge/PixiJS-8-E91E63?logo=pixijs&logoColor=white)](https://pixijs.com)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)](#con-docker)
[![Licencia](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)
[![Último cambio](https://img.shields.io/github/last-commit/Dasge97/the-village?label=%C3%BAltimo%20cambio)](https://github.com/Dasge97/the-village/commits/main)

<img src="docs/img/portada.png" alt="Mapa de La aldea en pixel art: un almacén de paja en la plaza, casas, huertos vallados con trigo a la derecha, la muralla a medio hacer arriba y bosque a la izquierda. Llueve. Arriba, la fecha del mundo, los recursos y el contador de personas del mundo; un aviso dice que unos murciélagos han roto un tramo de muralla." width="100%">

[![Ver en directo](https://img.shields.io/badge/Ver%20en%20directo-2ea44f?style=for-the-badge)](https://aldea.code-hive.space)
&nbsp;
[![Instalar](https://img.shields.io/badge/Instalar-555?style=for-the-badge)](#instalación)
&nbsp;
[![Cómo funciona](https://img.shields.io/badge/C%C3%B3mo%20funciona-555?style=for-the-badge)](#cómo-funciona)

</div>

## Para qué sirve

> **El primer objetivo de este proyecto es probar las capacidades de Jev.**

Jev (`typesafe/jev-1.14`) es un modelo de OpenRouter que no escribe texto: recibe una situación
y una lista de opciones, y devuelve la opción elegida, la probabilidad de cada una y su confianza.
Este proyecto lo pone a prueba en un caso difícil y fácil de mirar: decidir, una y otra vez, la
vida de personas con hambre, sueño, carácter, familia y miedo a los monstruos.

Las preguntas que intenta responder:

- ¿Toma Jev decisiones con sentido cuando la situación cambia sin parar?
- ¿Se nota el carácter de cada habitante (perezoso, valiente, sociable…) en lo que Jev elige?
- ¿Sobrevive una aldea a largo plazo solo con sus decisiones?
- ¿Cuánto cuesta y cuánto tarda, con miles de decisiones al día?

El segundo objetivo es ver crecer un mundo entero sin nada escrito de antemano: de una aldea de
8 personas a pueblos, villas y ciudades con cientos de miles de habitantes.

## Qué hace

- **Una aldea que vive sola**, turno a turno, las 24 horas. Los habitantes trabajan, comen,
  duermen, se hacen amigos, forman parejas, tienen hijos, envejecen y mueren.
- **Jev decide** qué hace cada adulto en las dos horas siguientes. La ficha de cada habitante
  enseña la decisión, el motivo y la confianza de Jev. Lo urgente (comer cuando hay mucha hambre o dormir cuando no queda energía) lo
  resuelven reglas fijas.
- **El mundo crece:** cuando una aldea se llena, alguien se marcha y funda otra. Varias aldeas
  dan un pueblo, varios pueblos una villa y varias villas una ciudad. Los consejos de pueblos,
  villas y ciudades también deciden con Jev.
- **Una evolución larga:** cada aldea pasa por cuatro etapas de edificios (pozo, granero, taller,
  templo, dojo, mercado…) que se estropean y hay que reparar. Los pueblos, villas y ciudades
  tienen oro e impuestos, avances, monumentos, elecciones y revueltas, y se alían, se hacen
  rivales o pagan tributo. Todo esto son reglas: Jev no hace más llamadas.
- **Un solo mapa:** el mundo entero se puede recorrer arrastrando la vista: entre un asentamiento y
  otro hay bosque y caminos, y los vecinos se ven con su gente moviéndose.
- **Cada sitio con su forma:** las aldeas salen con uno de cuatro formatos (de río, de camino, de
  lago o de claro) y su propio tamaño. Pueblos, villas y ciudades son mucho más grandes y tienen su
  propia forma: calles desde la plaza, dos plazas o una cuadrícula con doble muralla.
- **Peligros y vida:** ataques de monstruos que se ven en el mapa, epidemias que se contagian,
  incendios, caravanas de comercio, clima y estaciones.
- **Todo en directo en la web:** mapa en pixel art, ficha de cada habitante, árbol de familias,
  historia año a año y mapa del mundo con todos los asentamientos.
- **Gasto controlado:** Jev tiene un límite de dólares al día. Si se acaba, deciden las reglas
  y la ficha lo dice.
- **Se instala como aplicación** en el móvil y en el ordenador, con su icono.
- **Panel de administración** con contraseña: acelerar o pausar el mundo, ver el gasto de Jev y
  cambiar su límite.

<div align="center">
<table>
<tr>
<td align="center"><img src="docs/img/ficha.png" alt="Ficha de Ichiro, guardia de 58 años y fundador de la aldea: está vigilando la muralla; lo decidió Jev con un 24 % de confianza. Debajo, sus barras de hambre, energía, salud y ánimo." width="420"><br><sub>Ficha de un habitante: qué hace y por qué lo decidió Jev</sub></td>
<td align="center"><img src="docs/img/ciudad.png" alt="Una ciudad de noche: muchas casas con las ventanas encendidas, templo, mercados, dojo, huertos y muralla completa." width="420"><br><sub>Una ciudad de 63.000 personas, de noche</sub></td>
</tr>
<tr>
<td align="center"><img src="docs/img/mundo.png" alt="Mapa del mundo: cuadrícula de zonas con pradera, bosque, desierto, nieve y pantano; cientos de iconos de aldeas, pueblos, villas y ciudades unidos por caminos. Al lado, la lista de asentamientos." width="420"><br><sub>Mapa del mundo</sub></td>
<td align="center"><img src="docs/img/mundo-historia.png" alt="Historia del mundo: gráfica de personas año a año con forma de curva que sube; el globo del año señalado separa la gente por aldeas, pueblos, villas y ciudades. Debajo, los grandes momentos." width="420"><br><sub>Historia del mundo y grandes momentos</sub></td>
</tr>
<tr>
<td align="center"><img src="docs/img/familias.png" alt="Árbol de familias de la aldea con los habitantes unidos por parejas e hijos." width="420"><br><sub>Árbol de familias</sub></td>
<td align="center"><img src="docs/img/admin.png" alt="Panel de administración, subpestaña Tiempo: fecha del mundo, cuánto dura un día y un año del mundo, botones de velocidad de ×1 a ×60 con ×10 elegido, y el botón para pausar el mundo." width="420"><br><sub>Panel de administración</sub></td>
</tr>
</table>
</div>

## Instalación

Hace falta Python 3.14 y Node.js 24.

```bash
git clone https://github.com/Dasge97/the-village.git
cd the-village

python -m venv .venv
.venv/bin/pip install -r requirements.txt        # en Windows: .venv\Scripts\pip

cd web && npm ci && npm run build && cd ..
```

### Arrancar sin Jev

Deciden las reglas. No hace falta ninguna clave y no se gasta nada.

```bash
.venv/bin/python -m jevmura.servidor
```

Abre <http://localhost:8000>.

### Arrancar con Jev

Necesitas una clave de [OpenRouter](https://openrouter.ai).

```bash
export OPENROUTER_API_KEY=...       # en PowerShell: $env:OPENROUTER_API_KEY = "..."
export ALDEA_ADMIN_CLAVE=...        # opcional: contraseña del panel de administración
.venv/bin/python -m jevmura.servidor --jev
```

### Con Docker

```bash
cp secrets.env.example secrets.env      # y rellena los valores
docker compose -f docker-compose.production.yml up -d --build
```

El fichero de Compose no publica ningún puerto, para que lo pongas detrás de tu proxy. Para
probarlo en tu equipo, crea un `docker-compose.override.yml` con esto y añádelo con otro `-f`:

```yaml
services:
  app:
    ports:
      - "8000:8000"
```

Los datos del mundo se guardan en el volumen `aldea_datos`.

## Uso

La web solo se mira: el mundo avanza solo y nadie lo dirige.

| Dónde | Qué ves |
|---|---|
| Mapa | La aldea en directo. Pulsa a alguien para ver su ficha; arrastra y usa la rueda para moverte |
| Habitantes | Quién vive allí y qué hace. En pueblos, villas y ciudades, sus cifras y sus notables |
| Historia | Lo que ha pasado por días y, maximizada, la historia año a año |
| Familias | El árbol de familias de todos los que han vivido allí |
| Mapa del mundo | Todos los asentamientos, la historia del mundo y sus grandes momentos |
| Nombre de arriba a la izquierda | Cambiar de asentamiento |
| Administración (barra de abajo) | Velocidad, pausa, gasto de Jev y estado del servidor |

Las pantallas van en la dirección (`#/habitantes/12`, `#/mundo/historia`, `#/?aldea=5`), así que se
pueden recargar y compartir.

## Configuración

| Variable | Para qué | Por defecto |
|---|---|---|
| `OPENROUTER_API_KEY` | Clave de OpenRouter para Jev | — |
| `ALDEA_ADMIN_CLAVE` | Contraseña del panel de administración. Vacía: panel cerrado | — |
| `JEVMURA_JEV` | `1` para decidir con Jev (igual que `--jev`) | apagado |
| `JEVMURA_DB` | Dónde se guarda el mundo | `datos/mundo.db` |
| `JEVMURA_SEMILLA` | Semilla del mapa y del azar al crear un mundo nuevo | `0` |
| `JEVMURA_HORA_INICIAL` | Hora del mundo a la que empieza un mundo nuevo | `7` |

Opciones de `python -m jevmura.servidor`: `--db`, `--semilla`, `--jev`, `--puerto` (8000) y
`--rapido <segundos por turno>` para pruebas.

Desde el panel de administración se cambian, y se guardan con la partida:

| Ajuste | Valores |
|---|---|
| Velocidad | ×1 (un turno cada 10 s, un año del mundo al día), ×2, ×5, ×10, ×30, ×60, ×300, ×1000 |
| Pausa | Sí o no |
| Límite de Jev | Dólares al día (0,30 al empezar): 60 % para vecinos, 40 % para consejos |
| Jev | Encendido o apagado |

## Cómo funciona

```
 navegador (Vue + PixiJS)  ◄── websocket: estado tras cada turno ──  servidor (FastAPI)
                                                                         │
                                         hilo del mundo: un turno cada 10 s
                                         ├─ aldeas: cada persona, con nombre y necesidades
                                         │    └─ ¿decisión? → Jev (si queda presupuesto) o reglas
                                         ├─ pueblos, villas y ciudades: gente por edades + notables
                                         │    └─ consejo cada estación → Jev o reglas
                                         └─ mundo: fundaciones, mudanzas, caravanas, epidemias
                                                    │
                                              SQLite (una base por aldea + mundo-global.db)
```

- **Decisiones:** el motor calcula para cada adulto las opciones posibles y lo que consigue cada
  una. Se las manda a Jev con su situación (necesidades, carácter, relaciones, lo que le falta a
  la aldea). Jev elige; el motor lo hace. Si Jev falla, tarda o no queda presupuesto, decide un
  decisor de reglas y el mundo nunca se para.
- **Tiempo:** un turno son 10 segundos reales. Un día del mundo dura una hora y un año del mundo,
  un día real.
- **Tres niveles de detalle:** en las aldeas se simula cada persona. En pueblos, villas y ciudades
  se simula la gente por edades, con recursos y edificios, y solo los notables tienen nombre.
- **Presupuesto:** dos bolsas de llamadas que se llenan poco a poco durante el día. La aldea que
  alguien está mirando tiene prioridad.
- **Crecimiento:** ajustado para llegar a medio millón de personas en unos 90 años del mundo. Se
  comprueba con la simulación rápida:

```bash
.venv/bin/python -m jevmura.mundo.simular 90 2026      # años, semilla y, si quieres, carpeta para guardarlo
```

El diseño completo, con todas las reglas y decisiones, está en [docs/proyecto.md](docs/proyecto.md)
(en español). Los cambios de cada versión, en [web/src/versiones.js](web/src/versiones.js).

### Pruebas

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Licencia

El código está bajo licencia [MIT](LICENSE).

Los gráficos y sonidos de `web/public/sprites` son del paquete
[Ninja Adventure](https://pixel-boy.itch.io/ninja-adventure-asset-pack) de Pixel-boy y AAA, con
licencia [CC0](web/public/sprites/LICENSE.txt).
