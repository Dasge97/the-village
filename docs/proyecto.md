# La aldea

Un mundo pequeño que vive en una web y avanza sin parar. Los habitantes los decide Jev.

Documento de diseño. Recoge lo decidido antes y durante la programación.
Estado: desplegado en https://aldea.code-hive.space desde el 24-10-2026. Cómo se instala y se
despliega: el `README.es.md` de la raíz. Última revisión: 25-10-2026.

## Qué es

**El primer objetivo del proyecto es probar las capacidades de Jev**: si decide con sentido, si
se nota el carácter de cada habitante, si una aldea sobrevive solo con sus decisiones y cuánto
cuesta. El segundo objetivo es ver crecer un mundo entero sin nada escrito de antemano.

Una web en la que vive una colonia de habitantes. Cada habitante tiene necesidades, recursos y
objetivos. Jev (`typesafe/jev-1.14` por OpenRouter) decide a qué se dedica cada uno: trabajar,
descansar, explorar, cooperar o competir.

Desde la web solo se observa. Nadie puede intervenir en el mundo.

El mundo no termina nunca. Sigue avanzando aunque nadie esté mirando.

## Decidido

### Ambientación

- La marca el paquete de gráficos `Ninja Adventure - Asset Pack`, de
  Pixel-boy y AAA. Licencia CC0: se puede usar sin pedir permiso.
- Pixel art de 16 × 16 visto desde arriba.
- Una aldea de estilo Japón feudal con toques de fantasía: casas de tejado naranja, campos de
  cultivo, molino de agua, aldeanos, monjes, samuráis y ninjas.
- El paquete trae herramientas de granja, semillas, comida, animales de granja y monstruos
  (slimes, serpientes, murciélagos). Todo lo que haya en el mundo tiene que poder dibujarse con
  el paquete.

### Población

- La aldea empieza con 8 habitantes.
- Solo nace un habitante si hay una casa con sitio libre y comida guardada. Así la población
  sube y baja sola con las cosechas.
- Si la aldea llega a 20 habitantes, los jóvenes adultos pueden decidir marcharse. Lo decide Jev.
  La marcha queda en la crónica. El primero que se marcha funda la Aldea del río y los siguientes
  se van a vivir allí (ver «Segunda aldea»). De la segunda aldea, quien se marcha se va lejos.
- Tope fijo de 20 habitantes. Con 20 no nace nadie más. Protege el coste si fallan los otros límites.

### Necesidades

Cada habitante tiene 4 necesidades: hambre, energía, salud y ánimo.

### Oficios

| Oficio | Qué hace | Herramienta del paquete |
|---|---|---|
| Campesino | Cultiva los campos | Azada y semillas |
| Leñador | Corta árboles | Hacha |
| Pescador | Pesca en el río | |
| Cantero | Saca piedra | Pico |
| Guardia | Defiende la aldea de los monstruos | Armas |

- Un habitante puede cambiar de oficio cuando Jev decide por él. Por ejemplo, si falta comida,
  Jev puede pasar al leñador al campo.

### Recursos

| Recurso | Quién lo produce | Para qué se gasta | Cómo se regenera |
|---|---|---|---|
| Comida | Campesino y pescador | Bajar el hambre | Los campos dan cosecha según la estación. Los peces del río se reponen poco a poco |
| Madera | Leñador | Construir casas y calentarse en invierno | Los árboles cortados vuelven a crecer |
| Piedra | Cantero | Construir casas y la muralla | No se acaba, pero sacarla cansa mucho |

### Relaciones

- Cada par de habitantes tiene una puntuación de -100 a 100. Por debajo de 0 son rivales.
  Por encima, amigos.
- La puntuación sube si trabajan juntos o comparten comida.
- La puntuación baja si discuten o si uno le quita recursos al otro.
- Jev ve las relaciones de cada habitante al decidir por él. Así puede elegir con quién cooperar
  o a quién evitar.

### Parejas y nacimientos

- Dos adultos con mucha amistad pueden formar pareja. Lo decide Jev.
- La pareja vive en la misma casa.
- La pareja puede tener un hijo si se cumplen los límites de población: casa con sitio libre,
  comida guardada y menos de 20 habitantes.
- Los niños no trabajan hasta que crecen.

### Muertes

- Por vejez.
- Por hambre, si la comida se acaba durante mucho tiempo.
- Por ataques de monstruos, si no hay guardias suficientes.
- Por enfermedad, como suceso aleatorio poco frecuente.

### Tiempo

- El servidor calcula un turno cada 10 segundos, las 24 horas.
- En cada turno las reglas mueven a los habitantes y aplican sus efectos: caminar, comer,
  gastar energía, recoger recursos.
- El turno no llama a Jev y no cuesta nada.

| Tiempo del mundo | Tiempo real |
|---|---|
| 1 turno (4 minutos del mundo) | 10 segundos |
| 1 día, con su noche | 1 hora |
| 1 estación | 6 horas |
| 1 año (primavera, verano, otoño e invierno) | 1 día |

- Un niño se hace adulto a los 16 años: 16 días reales.
- Un habitante vive unos 60 años: unos 2 meses reales.
- Por la noche los habitantes duermen en casa y los monstruos se acercan a la aldea.
- En invierno los campos no dan cosecha y las casas gastan madera para calentarse.

### Decisiones de Jev

- Jev decide por cada habitante cada 5 minutos.
- Las decisiones van por orden: en cada momento le toca a un solo habitante, y después al siguiente.
- Jev decide lo importante: a qué dedicarse, con quién cooperar, si explorar.
- Una decisión dura varios turnos. Por ejemplo, "ir al bosque a cortar leña".
- El intervalo de 5 minutos se puede cambiar sin tocar el resto.
- Jev recibe la situación del habitante: necesidades, oficio, edad, relaciones, recursos de la
  aldea, estación, hora y sucesos recientes.
- Jev elige una acción de una lista cerrada. Nunca escribe texto libre que el motor tenga que
  interpretar.
- Jev no escribe texto: la API de decisiones de OpenRouter solo devuelve la opción elegida, la
  probabilidad de cada opción y la confianza. Cada decisión lleva un motivo corto que sale de una
  plantilla según la opción y la situación. La web enseña el motivo y la confianza de Jev en la
  ficha del habitante.
- Clave: llega por la variable de entorno `OPENROUTER_API_KEY`. Nunca está en el repositorio.

Acciones que puede elegir Jev:

| Acción | Efecto |
|---|---|
| Trabajar en su oficio | Produce el recurso de su oficio |
| Cambiar de oficio | Pasa a otro oficio desde ese momento |
| Construir | Gasta madera y piedra para levantar una casa o un tramo de muralla |
| Descansar | Recupera energía |
| Comer | Gasta comida y baja el hambre |
| Hablar con otro habitante | Sube el ánimo de los dos y su relación |
| Ayudar a otro habitante | Trabaja a su lado. Sube la relación y la producción |
| Discutir con otro habitante | Baja la relación. Puede subir el ánimo del que gana |
| Quitar recursos | Coge comida del almacén para sí. Baja la relación con quien lo ve |
| Proponer pareja | Si la amistad es alta, forman pareja |
| Explorar | Sale del mapa conocido. Puede volver con recursos, con un hallazgo o herido |
| Marcharse de la aldea | Solo si la aldea tiene 20 habitantes. Deja de simularse |

### Lo urgente lo deciden las reglas

- Si el hambre o la salud de un habitante bajan de un límite, va a comer o a descansar sin
  preguntar a Jev.
- Si pasa un suceso grave, como un incendio o un ataque, los habitantes afectados pasan a decidir
  antes de que les toque.

### Si Jev falla

- Decide un decisor de reglas sencillo por ese habitante.
- El mundo nunca se detiene por un fallo de Jev o de OpenRouter.
- Si Jev falla muchas veces seguidas, `/api/salud` lo dice (`fallos_seguidos`) para que un
  vigilante externo pueda avisar.

### Coste

Datos de Jev medidos en otro proyecto: unos 0,5 segundos y 0,000036 USD por decisión.

Solo deciden los adultos despiertos: de noche se duerme y los niños los mueven las reglas. Con
el motor de reglas, 8 aldeas durante 100 años piden entre 1.250 y 2.150 decisiones por día real.

| Decisiones al día | Coste al día | Coste al mes |
|---|---|---|
| 1.250 (aldea de unos 9 habitantes) | 0,045 USD | unos 1,4 USD |
| 2.150 (aldea de unos 16 habitantes) | 0,077 USD | unos 2,3 USD |

Medido con Jev en el motor (3 días del mundo, 167 llamadas, `python -m jevmura.motor.medir_jev`):

| Dato | Valor |
|---|---|
| Coste por decisión | 0,000056 USD (algo más que en el póker: la pregunta lleva más datos) |
| Tiempo por llamada | 0,2 segundos |
| Fallos | 0 |
| Coste con 8 habitantes | 0,074 USD al día real, unos 2,2 USD al mes |

En la primera prueba Jev elegía trabajar en el 97 % de las decisiones. Se corrigió así:

- El ánimo afecta al trabajo: con ánimo 50 se produce lo normal, con más se produce más y con
  menos, menos. Trabajar sin parar baja el ánimo.
- Cada opción explica lo que consigue, por ejemplo "si nadie construye, la obra no se termina".
- El objetivo que recibe Jev habla de una vida completa, no solo de producir.

Después de los cambios, Jev trabaja en el 78 % de las decisiones, habla en el 16 % y ayuda a
otros en el 6 %.

### Que el mundo no se quede muerto

El mundo necesita mecanismos que lo renueven, para que no mueran todos ni se estabilice del todo:

- nacimientos,
- recursos que se regeneran,
- estaciones,
- sucesos aleatorios.

Sucesos aleatorios:

| Suceso | Frecuencia | Efecto |
|---|---|---|
| Ataque de monstruos | Algunas noches | Monstruos del paquete entran por el borde del bosque. Los guardias los frenan. Si no hay guardias suficientes, hay heridos o muertos |
| Sequía | Rara, en verano | La cosecha de esa estación baja a la mitad |
| Incendio | Raro | Una casa se quema y hay que reconstruirla |
| Enfermedad | Rara | Un habitante pierde salud durante varios días |
| Buena pesca | Frecuente | El río da el doble de pescado ese día |
| Forastero | Rara, solo si hay menos de 4 habitantes | Llega un habitante nuevo de fuera |

El forastero es la última red de seguridad: la aldea nunca se queda vacía del todo.

### Mapa

- Un mapa fijo de 64 × 48 casillas de 16 píxeles, dibujado con los tilesets del paquete.
- Se genera una sola vez al crear el mundo, a partir de una semilla, y después no cambia de forma.
- Zonas: aldea en el centro, campos de cultivo, río con molino de agua y puente, bosque en los
  bordes y cantera.
- Si cambia el generador del mapa, un mundo guardado lo recibe al reiniciar: las casas siguen en
  su sitio y los árboles nuevos empiezan crecidos.
- Lo que sí cambia: casas nuevas, tramos de muralla, árboles cortados que vuelven a crecer y el
  estado de los campos según la estación.

### Habitantes

- Cada habitante tiene un nombre de estilo japonés, sacado de una lista.
- Su aspecto es uno de los personajes del paquete: aldeanos, ancianos y niños para la mayoría,
  y samuráis o ninjas para los guardias.
- Al nacer, cada habitante recibe un carácter que se le pasa a Jev en cada decisión: trabajador,
  perezoso, sociable, solitario, valiente o prudente. Así dos habitantes en la misma situación
  pueden decidir distinto.

### Crónica

- Cada suceso importante queda escrito en la crónica: nacimientos, muertes, parejas, casas nuevas,
  ataques, cambios de oficio y marchas.
- Las frases se escriben con plantillas. Jev no escribe textos.
- Se guardan con detalle los sucesos del último año del mundo, es decir, del último día real.
- Al terminar cada año se guarda un resumen: población, nacimientos, muertes, cosechas y sucesos
  destacados. Los resúmenes anuales se guardan siempre.

### Árbol genealógico

- El motor guarda una ficha de cada habitante que ha vivido en la aldea, aunque haya muerto o
  se haya marchado: nombre, nacimiento, padres, parejas por orden, hijos, último oficio, cómo
  llegó (fundador, nacido en la aldea o forastero) y cuándo y por qué salió.
- Estas fichas no se borran nunca. Ocupan poco: unas pocas personas nuevas por día real.
- La web enseña el árbol completo de la aldea desde los fundadores. Al pulsar a una persona se
  ven sus antepasados y sus descendientes. Los que siguen vivos se distinguen de los que no.
- Datos que salen del árbol: número de generaciones, la familia con más descendientes y cuántos
  vivos descienden de cada fundador.

### Web

- Pública y sin registro. Solo se observa.
- Mapa de la aldea visto desde arriba, con los habitantes moviéndose en directo.
- Al pulsar un habitante se abre su ficha: nombre, edad, oficio, carácter, necesidades, pareja,
  amigos, rivales y la última decisión de Jev con su motivo.
- Panel de la aldea: año, estación, hora, población y recursos guardados.
- Crónica de sucesos recientes y lista de resúmenes anuales.
- En el móvil, el mapa ocupa la parte de arriba y la ficha, la aldea y la crónica van en
  pestañas debajo.
- Música y sonidos del paquete, apagados al entrar, con un botón para activarlos.

### Interfaz "La ventana" (validada el 24-10-2026)

- El mapa ocupa toda la pantalla. La interfaz flota encima en paneles: verde bosque oscuro en
  modo oscuro y crema en modo claro, con el dorado como acento.
- Arriba a la izquierda, el nombre de la aldea (al pulsarlo se elige otra) y "En directo". Arriba
  a la derecha, la fecha, la comida, la madera, la piedra, la muralla, el sonido y los ajustes de color.
- En escritorio, una columna de iconos a la izquierda abre los paneles Habitantes, Historia,
  Familias y Qué es La aldea. Familias ocupa casi toda la pantalla.
- Bajo la barra de arriba, el resumen del día: el suceso más importante de las últimas 24 horas
  del mundo y los recuentos (nacimientos, muertes, parejas, ataques, obras). Se puede cerrar
  hasta el día siguiente.
- Abajo a la izquierda, la tarjeta del habitante elegido en el mapa, solo si hay alguno. La
  selección se quita con la X de la tarjeta, pulsando en un sitio vacío del mapa o con Escape.
  Abajo a la derecha, el minimapa y los botones de zoom.
- Historia (antes Historia y Crónica por separado) se abre como panel estrecho: cifras de hoy, la
  muralla con barra y lo que ha pasado en el último año, agrupado por días, con subpestañas Todo,
  Vida, Obras, Peligros y Fuera. El botón de maximizar la pasa a toda la pantalla y añade a la
  derecha la historia año a año: cifras, gráfica de población y tabla (`#/historia/grande`).
- Interior de las secciones (rediseñado el 24-10-2026):
  - Habitantes: subpestañas Todos, Adultos, Niños y Mayores con su recuento. Cada fila lleva un
    punto de estado (despierto, durmiendo, fuera) y el oficio en una etiqueta.
  - Ficha: cabecera con edad, oficio y carácter en etiquetas, y subpestañas Ahora (qué hace y
    cómo está), Su vida, Familia (familia, amistades y rivales) y Decisiones (línea de tiempo).
  - Su vida (también en Familias, para quien ya no está): cómo llegó, parejas, hijos, cambios de
    oficio (los seguidos en una línea), vueltas de explorar, heridas y cómo murió o se marchó.
    El motor apunta cada momento en la ficha permanente de la persona (`Persona.hitos`).
  - Familias: si no hay nadie elegido, una leyenda de cómo se lee el árbol.
  - Las cifras (`Cifra.vue`), las subpestañas (`Subpestanas.vue`) y la lista de sucesos
    (`ListaSucesos.vue`) son componentes comunes.
  - Qué es La aldea (botón de información, abajo en la columna de iconos): explica el
    experimento. Portada con la situación de ahora mismo y tarjetas: nada está escrito, las
    reglas básicas, quién decide (Jev), cuando algo es urgente, la segunda aldea, el tiempo y qué
    puedes hacer tú.
- Barra de estado abajo del todo, fina y discreta: si hay conexión y la versión actual. Al
  pulsar la versión se abre Novedades, con cada versión y sus cambios.
- Versiones: se apuntan en `web/src/versiones.js`, de la más nueva a la más antigua. Cada cambio
  que se publica añade una versión arriba del todo, con número, fecha, título y lista de cambios.
- Sonido: música de día y de noche, río, lluvia, viento, pájaros, alerta en los ataques, golpes
  en la pelea y una melodía al nacer alguien o formarse una pareja. Empieza apagado y se recuerda.
- En el móvil, pestañas abajo (Mapa, Habitantes, Historia, Linajes); Qué es La aldea, el sonido y
  los colores van en el menú de arriba. Sin minimapa, y sin zoom con un panel abierto.
- Direcciones: `#/`, `#/habitantes`, `#/habitantes/ninos`, `#/habitantes/12`,
  `#/habitantes/12/vida`, `#/historia`, `#/historia/peligros`, `#/historia/grande`, `#/familias`,
  `#/familias/12`, `#/info` y `#/novedades`. La segunda aldea añade `?aldea=2`. Las direcciones
  antiguas `#/cronica…` llevan a Historia. La subpestaña cambia la dirección sin añadir pasos al botón de volver.

### Vista del mapa (paso 4)

- Al entrar, el mapa se ve a doble tamaño centrado en la plaza (a tamaño real en el móvil). Se
  arrastra con el ratón o el dedo y se acerca o aleja con la rueda, pellizcando o con botones.
  El botón "Ver toda la aldea" enseña el mapa entero.
- Entre dos turnos, cada habitante anda desde su posición anterior hasta la nueva durante los
  10 segundos del turno, con la animación de andar del paquete.
- Aspecto (rehecho el 24-10-2026 a partir de una imagen de referencia): hierba verde viva,
  caminos de tierra arenosa que serpentean fuera de la muralla, bosque espeso en los bordes,
  árboles sueltos, flores, arbustos y piedras por la hierba, y ondas en el río.
- Edificios: el almacén es la nave alta de tejado de paja; las casas se reparten entre cuatro
  modelos según su número. Alrededor de la plaza hay puestos, barriles, una caja y faroles.
- Un camino al noreste cruza el río por un puente de tablones con barandillas.
- Los árboles tienen tres formas: redondos, pinos y grandes. Cambian con la estación: algunos
  rosas en primavera, verdes en verano, anaranjados en otoño y nevados en invierno. Los
  cortados se ven como tocón y luego como brote.
- Los campos se dibujan como tres huertos con valla baja de madera. El del centro es de trigo,
  dorado ya en verano. Brotes en primavera, todo dorado en otoño y nada en invierno.
- La muralla es un cuadrado de muro de piedra gris con cuatro puertas donde la cruzan los
  caminos. Se ven los tramos construidos y, medio transparente, el que se está construyendo.
- De noche el mapa se oscurece y se encienden las ventanas, la puerta del almacén, los faroles
  y el molino.
- Sobre cada habitante, un icono de lo que hace: la herramienta de su oficio, un martillo, comida,
  un globo de alegría o enfado, un corazón, una bolsa o una «z» si duerme (`mapa/iconos.js`).
- Clima, solo visual y igual para todos los que miran: lluvia algunos ratos según la estación,
  nieve en invierno, hojas en otoño y pétalos en primavera. Con lluvia el día se ve más apagado
  (`mapa/efectos.js`). Para probar, `?clima=lluvia|nieve|hoja|petalo|ninguno` en la dirección.
- Los ataques de monstruos se ven unos 3 minutos: los monstruos salen del borde del mapa hacia la
  puerta de la muralla. Si los guardias los frenan, pelean allí con tajos y huyen entre humo; si
  no, llegan a la plaza y se van (`mapa/monstruos.js`; el motor guarda el último ataque en
  `Aldea.ataque`, sin guardarlo en la base de datos).
- Los habitantes van por rutas (`motor/caminos.py`, A*): prefieren caminos, plaza y puente,
  rodean casas, almacén y tramos de muralla, y cruzan el río por el puente.
- Colores de marca sacados del paquete: naranja teja (tono OKLCH 50) como principal y azul agua
  (tono 230) como acento. Fuentes: Pixelify Sans para el nombre e Inter para el texto.
- Los gráficos que usa la web se copian del paquete a `web/public/sprites` con
  `python web/copiar_sprites.py`. El mismo script crea en `sprites/Aldea` copias con otros
  colores: suelo, agua, naturaleza, muralla gris y trigo. `node web/capturas.mjs` saca capturas en 375, 768, 1280 y
  1440 px, en modo claro y oscuro, y avisa de errores de la consola.

### Técnica

- Servidor: Python con FastAPI. Un único proceso calcula los turnos y atiende la web.
- El estado se envía a la web por websocket después de cada turno.
- Base de datos: SQLite. No hay usuarios y solo escribe un proceso, así que no hace falta PostgreSQL.
- El estado del mundo se guarda cada 30 turnos (5 minutos reales). Si el servidor se reinicia,
  sigue desde el último guardado. Las llamadas y el coste de Jev se guardan con él.
- Segunda aldea: `jevmura/bucle.py` (`Mundo`) lleva las aldeas, que avanzan a la vez. La segunda
  se guarda en `mundo-2.db`, junto a `mundo.db`, con su propio mapa (semilla + 7777). La API y el
  websocket admiten `?aldea=2`, y `GET /api/aldeas` dice cuáles existen.
- Si el servidor estuvo apagado, no se calculan los turnos perdidos: el mundo se queda parado
  mientras tanto. Así un apagón largo no provoca miles de llamadas a Jev de golpe.
- Tablas de SQLite: `mundo` (todo el estado en JSON; el mapa sale de la semilla y solo se guarda
  el crecimiento de los árboles), `cronica` (último año), `resumenes` (para siempre) y
  `personas` (fichas del árbol genealógico, para siempre).
- Web: Vue. Mapa y habitantes: PixiJS.
- Despliegue: Docker Compose.
- Credenciales (clave de OpenRouter y contraseña del panel) en `secrets.env`, nunca en el repositorio.

### Nombre

- Nombre: La aldea (cambiado el 24-10-2026; antes, Jevmura). El código sigue en el paquete `jevmura`.
- Dominio: `aldea.code-hive.space`.

### Ajustes decididos al programar el motor

- Cada almacén tiene tope: 400 de comida, 250 de madera y 250 de piedra. Con el almacén lleno,
  trabajar en ese recurso no sirve, y el decisor lo sabe.
- Tras cambiar de oficio, un habitante no puede volver a cambiar en 3 días del mundo.
- Las relaciones se acercan un 3 % a 0 cada día. Si dos habitantes dejan de hablarse, se olvidan.
- Para hablar se ofrece a la pareja, al mejor amigo y a alguien al azar, para que se conozcan todos.
- Dos solteros de edad parecida se hacen amigos el doble de rápido al hablar.
- Una pareja no puede llevarse más de 12 años.
- Cada pareja con sus hijos menores vive siempre junta. Si no tiene casa propia, la aldea construye una.
- Los hijos solteros de 18 años o más se van de casa de sus padres si hay sitio en otra.
- Los ataques de monstruos rompen tramos de muralla. Cuanto más grande es la aldea, más
  fuertes son los ataques.

Resultado con el decisor de reglas, 8 aldeas durante 100 años: la población media va de 9 a 16
habitantes, la aldea está llena como mucho el 5 % de los días y nunca se vacía. Casi todas las
muertes son por vejez.

## Orden de trabajo

1. ~~Motor de la aldea sin web, con el decisor de reglas.~~ Hecho. Se prueba con
   `python -m jevmura.motor.lote [años] [aldeas] [--detalle]` y con `pytest`.
2. ~~Jev dentro del motor.~~ Hecho: `jevmura/motor/jev.py`. Se mide con
   `python -m jevmura.motor.medir_jev [días] [semilla]`.
3. ~~Guardado en SQLite, crónica y resúmenes anuales.~~ Hecho: `jevmura/guardado.py` guarda y
   recupera el mundo, y `jevmura/bucle.py` lo hace avanzar en tiempo real. Se prueba sin web con
   `python -m jevmura.bucle [--jev] [--rapido]`.
4. ~~Emisión por websocket y vista del mapa con PixiJS y los gráficos del paquete.~~ Hecho:
   `jevmura/servidor.py` (FastAPI) y la web en `web/` (Vue, PixiJS). Se arranca con
   `python -m jevmura.servidor` después de `npm run build` en `web/`.
5. ~~Ficha de habitante, panel de la aldea, crónica y diseño de la web.~~ Hecho. La web tiene
   tres secciones: "En directo" (mapa, datos, crónica, lista de habitantes y ficha de cada uno),
   "Familias" (árbol genealógico) e "Historia" (gráfica de población y tabla por años). La
   pantalla va en la dirección (`#/directo/habitantes/12`, `#/familias/persona/12`), así que se
   puede recargar y compartir. Cada habitante recuerda sus 5 últimas decisiones, que se ven en
   su ficha. Desde la ficha se puede seguir al habitante con la cámara del mapa.
6. ~~Despliegue y avisos al móvil.~~ Hecho: un contenedor Docker detrás de un proxy con HTTPS.
   Un vigilante revisa `/api/salud` cada 5 minutos y avisa al móvil si la web cae, el mundo se
   para o Jev falla 20 veces seguidas.

## Versión 1.0 (24-10-2026)

Versiones 0.8 a 1.0, en `web/src/versiones.js`: Historia y Crónica juntas, totales de Jev que no
vuelven a cero, iconos sobre la cabeza, luces de noche, clima, monstruos visibles, rutas por los
caminos, la vida de cada persona, resumen del día, música y sonidos, y la segunda aldea.

## Mundo grande (versión 2, decidido el 24-10-2026)

El mundo deja de tener un tope de 20 personas. Crece solo: las aldeas llenas fundan aldeas nuevas,
varias aldeas dan lugar a un pueblo, varios pueblos a una villa y varias villas a una ciudad. Lo
construye todo el propio juego con los gráficos del paquete. Desde la web se sigue solo mirando.

### Decisiones del dueño del proyecto

| Pregunta | Respuesta |
|---|---|
| Gasto máximo en Jev | 0,30 USD al día real (unos 9 USD al mes) |
| Partida actual | Sigue: la aldea de ahora es el primer asentamiento del mundo grande |
| Ritmo | Medio millón de personas en unos 3 meses reales (unos 90 años del mundo) |
| Pantalla al entrar | El asentamiento más poblado; el mapa del mundo está a un botón |

### El tiempo no cambia

Sigue un turno cada 10 segundos, un día del mundo por hora real y un año del mundo por día real.
Las vidas duran lo mismo. Lo que cambia es cuánta gente hay y cómo se simula.

### Tres niveles de detalle

| Nivel | Dónde | Cómo se simula | Quién decide |
|---|---|---|---|
| Vecinos | Las aldeas | El motor de ahora: cada persona con nombre, necesidades, familia, ruta por el mapa y crónica | Jev mientras quede presupuesto; si no, las reglas |
| Notables | Pueblos, villas y ciudades | Hasta 8 personas con nombre y cargo (alcalde, maestra, capitán…), con su vida y su ficha | Las reglas |
| Población | Pueblos, villas y ciudades | Números: cuántas personas hay de cada edad, recursos, edificios y producción. Se calcula una vez al día del mundo | El consejo del asentamiento, con Jev |

Las aldeas nunca se convierten en otra cosa: siguen siendo aldeas detalladas para siempre. Los
pueblos, villas y ciudades son asentamientos nuevos que se fundan al lado.

### Asentamientos

| Tipo | Tope de población | Se funda cuando… | Con quién |
|---|---|---|---|
| Aldea | 20 | una aldea está llena y alguien se marcha | el que se marcha (y los siguientes que se marchen de la misma) |
| Pueblo | 400 | hay 4 aldeas a menos de 3 zonas unas de otras sin pueblo cerca | 3 jóvenes de cada aldea cercana y 30 de fuera |
| Villa | 4.000 | hay 3 pueblos a menos de 4 zonas sin villa cerca | el 15 % de la gente de cada pueblo cercano |
| Ciudad | 60.000 | hay 3 villas a menos de 7 zonas sin ciudad cerca | el 10 % de la gente de cada villa cercana |

(Al programarlo, los radios de 6 y 10 zonas salían demasiado grandes: casi no nacían villas.
Se bajaron a 4 y 7.)

- Cada asentamiento ocupa una zona del mapa del mundo. No hay dos en la misma zona.
- Una aldea llena hace que, cada día del mundo, un joven soltero pueda marcharse (lo decide la
  regla si Jev no lo ha decidido antes). Así las aldeas siempre empujan hacia fuera.
- Un pueblo, villa o ciudad por encima del 90 % de su tope junta cada día gente que se va (el
  0,4 % de su población). Cuando son 25 o más, van, por este orden: a otro del mismo tipo con
  sitio a 6 zonas o menos; a fundar uno nuevo del mismo tipo, si hay una zona libre a 3 zonas o
  menos y son 20 o más; a uno de un tipo más grande con sitio a 8 zonas o menos. Si no, se quedan.
  Un grupo pequeño (8 o más) a veces funda una aldea.
- Nombres: «La aldea» y «Aldea del río» se quedan. Los nuevos se llaman «Aldea de Mizuno»,
  «Pueblo de Takada»… con 68 nombres japoneses, sin repetir. Cuando se acaban, se les añade dónde
  quedan: «Villa de Mizuno del Norte», «Pueblo de Takada Alto»… (14 coletillas, unos 1.000 nombres).

### El mapa del mundo

- Una cuadrícula de 24 × 24 zonas. Cada zona es un mapa de 64 × 48 casillas como el de ahora.
- La aldea de ahora está en el centro (zona 12, 12) y la Aldea del río al este (zona 13, 12).
- Cada zona tiene un terreno fijo que sale de la semilla: pradera, bosque, desierto, nieve o
  pantano. Cerca del centro casi todo es pradera; más lejos aparece lo demás.
- Las zonas sin nadie se ven con niebla. Una zona se descubre cuando hay un asentamiento en ella
  o al lado.
- Los asentamientos que comercian o se han mandado gente quedan unidos por caminos.

| Terreno | Suelo del paquete | Árboles |
|---|---|---|
| Pradera | Hierba clara y tierra arenosa (los de ahora) | Redondos, pinos y grandes |
| Bosque | Hierba oscura | Muchos más pinos |
| Desierto | Arena naranja (`TilesetFloor`, bloque naranja) | Pocos, y rocas |
| Nieve | Nieve (`TilesetFloor`, bloque blanco) | Árboles nevados todo el año |
| Pantano | Tierra marrón (`TilesetFloor`, bloque marrón) | Árboles muertos (`TilesetNature`) |

### El presupuesto de Jev

- 5.000 llamadas al día real como máximo (0,28 USD con 0,000056 USD por llamada).
- 3.000 para los vecinos de las aldeas y 2.000 para los consejos.
- Se reparten a lo largo del día: unas 2 por minuto para los vecinos y 1,4 para los consejos.
  Si se acaban, decide la regla y la ficha lo dice («Jev estaba ocupado; decidieron las reglas»).
- Primero se sirven la aldea que alguien está mirando y La aldea. Las demás aldeas solo usan
  Jev si queda más del 20 % del presupuesto de ese rato.
- El consejo de cada pueblo, villa o ciudad decide una vez por estación del mundo (6 horas
  reales): qué construir, si fundar una aldea, si mandar gente a otro sitio, si celebrar una
  fiesta o si reforzar la defensa.

### Pueblos, villas y ciudades por dentro

- Población por edades (0 a 90 años). Cada día del mundo nacen, envejecen y mueren según tasas
  fijas que dependen de la comida, las casas libres, la salud y los sucesos.
- Recursos: comida, madera y piedra, como en las aldeas, con producción por trabajador y
  consumo por persona. El terreno cambia la producción (en el desierto se cultiva peor).
- Edificios que se construyen con recursos y dan algo: casas (sitio para vivir, se construyen
  por tandas), granero (guarda comida), taller (más madera y piedra), mercado (caravanas),
  templo (salud y ánimo), dojo, muralla y torres (defensa) y posada (llega gente de fuera).
- Sucesos: ataques, epidemias, incendios, buenas cosechas, sequías, fiestas y llegadas de gente.
  Todo queda en su crónica.
- Notables: 4 en un pueblo, 6 en una villa y 8 en una ciudad, con nombre y cargo. Nacen, se
  emparejan, envejecen y mueren con las reglas. Al morir, otro ocupa su cargo.
- Caravanas: cada estación, dos asentamientos unidos por un camino y con mercado se mandan el
  10 % de un recurso cuando uno tiene, por persona, más del triple que el otro.
- Contagios: una epidemia puede pasar a los asentamientos a 2 zonas o menos (un 4 % al día).
- Grandes momentos del mundo: la segunda aldea, el primer pueblo, la primera villa, cada ciudad y
  cuando el mundo pasa de 100, 1.000, 10.000, 50.000, 100.000, 250.000, 500.000 y 1.000.000 de
  personas. No se borran nunca de la crónica del mundo.
- Cada día del mundo se pone al día una foto del año: cuánta gente hay y cuántos asentamientos
  de cada tipo. Con ella se dibuja la historia del mundo.
- El ritmo se ajusta para llegar a medio millón en unos 90 años del mundo. Se comprueba con la
  simulación rápida: `python -m jevmura.mundo.simular [años] [semilla] [carpeta]`. Avanza solo los
  pueblos, villas y ciudades con todas las reglas del mundo y escribe la población cada 5 años.
  Con una carpeta, guarda el mundo para abrirlo con `python -m jevmura.servidor --db <carpeta>/mundo.db`.
- Resultado medido en la 2.0 (1,3 hijos al año por mujer de 18 a 40 años): 137.000 personas en el
  año 75, 423.000 en el 90 y 557.000 en el 95, en unos 570 asentamientos (5 ciudades). Desde la 3.0
  la natalidad es 1,4 (ver «Evolución de los asentamientos»). La partida
  real arranca algo más lenta, porque las aldeas detalladas tienen que llenarse antes de que nazca
  el primer pueblo.

### Cómo se ve en la web

- **Mapa del mundo** (`#/mundo`): las 24 × 24 zonas con su terreno, la niebla, los caminos y un
  icono por asentamiento (casa, dojo, torre o castillo según el tipo) con su nombre y su
  población. Se arrastra y se acerca. Al pulsar un asentamiento se entra en él.
- **Dentro de una aldea:** como ahora.
- **Dentro de un pueblo, villa o ciudad:** un mapa que el juego monta con sus edificios (casas,
  mercado, templo, dojo, torres…) y gente andando por las calles. Esa gente es solo dibujo; los
  notables sí tienen ficha. Habitantes enseña los notables y la población por edades; Historia y
  Familias funcionan como en las aldeas, con los notables.
- **Selector de arriba a la izquierda:** los 8 asentamientos más poblados y «Ver el mapa del
  mundo».
- **Historia del mundo:** subpestaña Historia del mapa del mundo (`#/mundo/historia`). Una
  gráfica con la gente del mundo año a año; al pasar por encima, cuántos viven en cada tipo de
  asentamiento. Debajo, los grandes momentos con su año y lo último que ha pasado.
- **Contador de la barra de arriba:** la gente de todo el mundo. Al pulsarlo se abre el mapa del mundo.
- Al entrar se ve el asentamiento más poblado.

### Técnica

- `jevmura/mundo/`: el mundo grande (zonas, asentamientos, caminos, presupuesto, crónica del
  mundo). El motor de aldea (`jevmura/motor/`) no cambia de idea: cada aldea sigue siendo un `Aldea`.
- Cada aldea se guarda en su propia base de datos (`mundo.db` La aldea, `mundo-2.db` la Aldea
  del río, `aldea-<id>.db` las siguientes). El mundo y los asentamientos grandes, en `mundo-global.db`.
- La API y el websocket usan `?aldea=<id>` para cualquier asentamiento. `GET /api/mundo` da las
  zonas descubiertas, los asentamientos, los caminos, la foto de cada año (`anual`), los grandes
  momentos (`momentos`) y los últimos sucesos (`sucesos`).

### Versiones

Todas publicadas el 24-10-2026.

1. 1.1: presupuesto de Jev, emigración de las aldeas llenas y aldeas sin límite en zonas con terreno.
2. 1.2: mapa del mundo y selector nuevo.
3. 1.3: pueblos con su población, consejo, notables y mapa. Contador de gente del mundo.
4. 1.4: villas y ciudades, caravanas, contagios, reparto de gente y nombres que no se acaban.
5. 1.5: historia del mundo.
6. 2.0: todo junto y comprobado, con esta documentación al día.

## Panel de administración (versión 2.1, 24-10-2026)

Un panel con contraseña para el dueño del proyecto, en `#/admin`. El acceso está en la barra de
abajo. Lo decide el propio panel, no Jev ni las reglas.

- **Tiempo:** la velocidad del mundo se elige entre ×1, ×2, ×5, ×10, ×30, ×60, ×300 y ×1000. A
  ×1, un turno dura 10 segundos; a ×1000, una centésima. Por encima de ×60, la web recibe como
  mucho unos 7 estados por segundo. También se puede pausar. La web recibe la duración
  real de cada turno para que los habitantes anden a la velocidad buena. Arriba a la izquierda
  pone «En directo · ×10» o «En pausa».
- **Gasto:** el gasto de Jev se cuenta por día real y se guardan 60 días. El límite se pone en
  dólares al día (0,30 al empezar, 5 como mucho) y se pasa a llamadas con 0,000056 USD por
  llamada: 60 % para los vecinos y 40 % para los consejos. Jev se puede apagar: entonces todo lo
  deciden las reglas.
- **Servidor:** tiempo encendido, último guardado, webs conectadas, asentamientos, personas,
  tamaño de las bases de datos y un botón para guardar ya.
- Con el mundo acelerado se guarda como mucho una vez por minuto real.
- La contraseña llega en la variable de entorno `ALDEA_ADMIN_CLAVE`. La
  sesión es una cookie firmada con la contraseña, solo para `/api/admin`, de 7 días.
- Código: `jevmura/admin.py` (API) y `web/src/componentes/VistaAdmin.vue` (pantalla).


## Evolución de los asentamientos (versión 3, decidido el 25-10-2026)

Hasta la 2.2, una aldea termina pronto sus obras: casas hasta 20 personas y 20 tramos de muralla,
que se acaban en uno o dos años del mundo. Después la piedra y la madera llegan al tope del
almacén y no hay en qué gastarlas. Los pueblos, villas y ciudades solo eligen entre unas pocas
obras. La versión 3 les da una evolución larga, con cosas que hacer y en qué gastar durante toda
su vida.

### La regla del coste

El gasto en Jev no sube. Jev cobra por llamada, no por opción.

- Los habitantes siguen decidiendo igual (un adulto cada 5 minutos, con el límite de dólares al
  día). Las obras nuevas son opciones dentro de esas mismas decisiones.
- El orden de las obras lo deciden las reglas, según lo que más falte.
- Nuevo: un **consejo de la aldea** elige con Jev, una vez por estación del mundo, la siguiente
  obra o si hacer una fiesta. Son 4 llamadas por aldea y día real a ×1, de la bolsa de consejos.
- En pueblos, villas y ciudades todo lo nuevo son números y reglas. El consejo sigue llamando a
  Jev una vez por estación; solo tiene más opciones entre las que elegir.

### La aldea: etapas

Una aldea sigue siendo pequeña (20 personas como mucho). Su evolución son edificios por etapas.
Cada etapa se abre al terminar la anterior. Cada edificio tiene un efecto concreto, sale en el
mapa con un gráfico del paquete y aparece como opción «construir» en las decisiones.

| Etapa | Se abre cuando… | Edificios |
|---|---|---|
| 1. Asentamiento | desde el principio | Casas y muralla (como ahora) |
| 2. Aldea | la muralla está completa por primera vez | Pozo, granero, taller, torre de vigía y huertos nuevos |
| 3. Aldea próspera | están los cinco edificios de la etapa 2 | Templo, dojo, mercado y almacén de piedra |
| 4. Mejoras | están los cuatro de la etapa 3 | Casas de piedra, muralla reforzada y faroles, tramo a tramo y casa a casa |

| Edificio | Efecto |
|---|---|
| Pozo | Menos enfermedades; la salud se recupera antes |
| Granero | Cabe más comida y se pierde menos cada día |
| Taller | Leñadores y canteros sacan más |
| Torre de vigía | Más defensa de noche; los ataques rompen menos muralla |
| Huertos nuevos | Más campo: más cosecha |
| Templo | Más ánimo; una muerte baja menos el ánimo de los demás |
| Dojo | Cada guardia defiende más |
| Mercado | La aldea puede mandar caravanas a las aldeas y pueblos cercanos con lo que le sobra |
| Almacén de piedra | Cabe más madera y piedra |
| Casa de piedra | No se quema tan fácil; más salud y ánimo para los que viven en ella |
| Muralla reforzada | Un ataque casi nunca rompe ese tramo |
| Faroles | Los ataques de noche se frenan mejor |

Costes finales (madera, piedra y turnos de obra; un turno son 10 segundos a ×1):

| Obra | Madera | Piedra | Turnos |
|---|---|---|---|
| Pozo | 50 | 150 | 900 |
| Granero | 200 | 100 | 1.200 |
| Taller | 180 | 180 | 1.200 |
| Torre de vigía | 150 | 240 | 1.200 |
| Huertos nuevos | 150 | 60 | 1.000 |
| Almacén de piedra (el primero de la etapa 3) | 160 | 220 | 1.500 |
| Templo | 300 | 480 | 2.400 |
| Dojo | 400 | 400 | 2.100 |
| Mercado | 350 | 300 | 1.800 |
| Casa de piedra (cada una) | 40 | 200 | 1.000 |
| Tramo reforzado (cada uno) | 15 | 120 | 700 |
| Faroles (cuatro, uno por puerta) | 80 | 40 | 450 |
| Reparar un edificio | 30 % | 30 % | 40 % |

Ritmo medido con 8 aldeas y el decisor de reglas: la etapa 2 se abre hacia el año 2 o 3 y se
termina entre el 5 y el 7; la aldea llega a la etapa 4 entre el año 10 y el 13 y termina las
mejoras hacia el 21. Ninguna aldea se vacía. Dos frenos lo hacen posible: no se empieza una obra
de la evolución con comida para menos de 4 días, y la leña de reserva para el invierno nunca
pide más de lo que cabe en el almacén (sin esto, el almacén de piedra no se podía pagar nunca).

Todos los edificios van dentro de la muralla, donde nunca hay árboles, salvo los huertos nuevos,
que van junto a los campos y quitan los árboles de su sitio. El código está en
`jevmura/motor/evolucion.py`.

### La aldea: gastos que no se acaban

- **Desgaste:** cada edificio, casa y tramo de muralla tiene un estado de 0 a 100. Baja poco a
  poco con los años, con los ataques y con los incendios. Por debajo de 50 su efecto se queda en
  la mitad, y a 0 se pierde. Repararlo es una obra («reparar el granero») que cuesta una parte de
  lo que costó hacerlo.
- **Fiesta de la cosecha:** en otoño, si sobra comida, el consejo puede celebrarla. Gasta comida
  y sube el ánimo de todos.
- **Invierno duro:** algunos inviernos hace falta el doble de leña.
- **Boda:** al formar pareja se gasta algo de comida en la celebración y sube el ánimo.
- **Comercio:** con mercado, lo que llega al tope del almacén sale en caravana hacia una aldea o
  un pueblo cercano que lo necesite, y vuelve lo que a la aldea le falta.

### Pueblos, villas y ciudades: mucha más vida

Como todo son reglas, aquí cabe mucha más profundidad.

| Tema | Qué se añade |
|---|---|
| Riqueza | Un recurso nuevo, el oro, que sale de impuestos por persona y del comercio. Se gasta en monumentos, en comprar comida en una hambruna y en pagar defensa |
| Edificios nuevos | Herrería, escuela, hospital, acueducto, puerto (si hay río), mina, biblioteca, teatro y cuartel, cada uno con su efecto |
| Avances | Herramientas de hierro, molinos, rueda, escritura, medicina, ingeniería… Se abren con años y edificios, y cada uno mejora algo para siempre. El consejo puede elegir investigar |
| Especialidad del terreno | Pieles en la nieve, especias y vidrio en el desierto, hierbas en el pantano, madera noble en el bosque, trigo en la pradera. El comercio entre terrenos distintos vale más |
| Sociedad | El ánimo bajo durante mucho tiempo trae protestas y, si sigue, una revuelta que cambia al consejo. El alcalde (o gobernador) se elige cada 4 años entre los notables |
| Relaciones | Alianzas (comercio y ayuda en los ataques) y rivalidades entre vecinos. Una ciudad puede pedir tributo a los pueblos de alrededor. Escaramuzas pequeñas, sin guerras que vacíen el mapa |
| Sucesos grandes | Inundaciones, terremotos, un gran incendio, hambrunas, peste, un cometa, la visita de un mercader extranjero, el descubrimiento de una mina, el festival anual |
| Monumentos | Gran templo, castillo, faro, estatua. Años de obra, se ven en el mapa y atraen gente |

El consejo gana opciones nuevas (investigar, aliarse, empezar un monumento, subir o bajar
impuestos) en la misma llamada de cada estación. Todo queda en la crónica y en la historia del
mundo, y lo importante sale en los grandes momentos.

### Aldeas que crecen y se expanden (3.1)

Al simular el mundo entero con las aldeas se vio que una aldea se quedaba en 8 o 10 personas
durante décadas y nunca llegaba a 20, así que el mundo no se expandía nunca:

- en una casa cabían 4 personas, y una pareja con dos hijos ya no podía tener más;
- los dos jóvenes solteros de la fundación se marchaban y no quedaba nadie para formar pareja.

Cambios:

| Qué | Antes | Ahora |
|---|---|---|
| Personas por casa | 4 | 6 |
| Desde cuántos habitantes se marcha alguien a fundar otra aldea | 20 (uno de cada dos días) | 14 (un 8 % de los días; con 20, uno de cada dos), y solo si quedan al menos dos jóvenes solteros |
| Forasteros | solo con menos de 4 habitantes | además, con menos de 14, uno cada 36 días de media |
| Hambre de los niños de menos de 12 años | como un adulto | el 60 % |
| Comida guardada para que nazca alguien | 3 por persona | 5 por persona |
| Con comida para menos de 3 días | cada uno cambia de oficio cuando decide | la mitad de los leñadores y canteros pasan a campesinos (o a pescadores en invierno) |

Medido simulando el mundo entero con las reglas: en el año 18 nace el primer pueblo y en el año 30
hay 10 aldeas, 2 pueblos y 530 personas, sin ninguna muerte por hambre.

### Formatos y tamaños de los mapas (3.2)

Hasta la 3.1 todos los asentamientos salían del mismo mapa de 64 × 48 casillas: plaza en el
centro, muralla cuadrada, campos al este, cantera al sur y río al este. Desde la 3.2, cada
asentamiento nuevo tiene un formato y un tamaño (`jevmura/motor/formatos.py`):

| Formato | Para | Cómo es | Tamaño (casillas) |
|---|---|---|---|
| Clásica | La aldea y las aldeas de antes | El mapa de siempre (`motor/mapa.py`) | 64 × 48 |
| Río | Aldeas | El río cruza la aldea por dentro de la muralla, con dos puentes | 60–72 × 44–54 |
| Camino | Aldeas | Una calle larga de punta a punta y la muralla alargada | 60–72 × 44–54 |
| Lago | Aldeas | Un lago junto a la plaza (en el desierto, un oasis); la muralla se corta en la orilla | 60–72 × 44–54 |
| Claro | Aldeas | En medio del bosque, muralla octogonal y una charca | 60–72 × 44–54 |
| Pueblo | Pueblos | Calles que salen de la plaza en varias direcciones | 90–100 × 66–74 |
| Villa | Villas | Dos plazas unidas por una calle y muralla grande | 120–132 × 88–98 |
| Ciudad | Ciudades | Calles en cuadrícula cada 9 casillas y doble muralla (la interior, siempre entera) | 152–166 × 112–122 |

- El formato de una aldea nueva sale al azar, con más peso según el terreno: claro en el bosque
  (×3) y en la nieve (×2), lago en el desierto (×3) y en el pantano (×2). Además, la mitad de los
  mapas salen en espejo (el río o el lago al otro lado).
- En vez de casillas fijas, el generador busca sitio: primero el agua, la plaza, los caminos y la
  muralla; después los campos y la cantera junto a la muralla; luego los 12 solares y los sitios de
  los 8 edificios de la evolución, de la plaza hacia fuera; y al final los árboles en lo que queda.
- Pueblos, villas y ciudades dibujan como mucho 140, 300 y 600 parcelas; las que no caben dentro
  de la muralla salen fuera, como barrios. Su mapa se genera solo cuando alguien lo mira (tarda
  una décima de segundo y puede haber cientos).
- Una vez publicado, el generador de un formato de aldea no se puede cambiar: las aldeas guardan
  sus árboles por orden y el mapa se vuelve a generar al cargarlas. Un cambio es un formato nuevo.

### Cómo quedó en pueblos, villas y ciudades

- Código: `jevmura/mundo/sociedad.py` (oro, edificios nuevos, avances, sociedad, sucesos y
  monumentos) y `jevmura/mundo/relaciones.py` (alianzas, rivalidades y tributos).
- Impuestos: bajo, normal o alto. Dan 0,0005, 0,001 o 0,002 de oro por persona y día, y cambian
  el ánimo (+0,03, 0 o −0,07). Una mina da 1,5 de oro y 3 de piedra al día.
- Edificios nuevos: herrería, escuela, hospital y mina desde pueblo; acueducto, puerto, teatro y
  cuartel desde villa; biblioteca en ciudad. Uno por cada 3.000 habitantes.
- Avances: 8, de 80 a 160 días de estudio. Investigar cuesta 0,5 de oro al día más 0,0005 por
  habitante. La escuela, la escritura y la biblioteca lo aceleran.
- Monumentos: estatua y gran templo desde villa; castillo y faro en ciudad (el faro pide
  puerto). Cuestan madera, piedra y oro y tardan de 120 a 280 días.
- Descontento: sube cuando el ánimo está por debajo de 0,45. Con 0,5 puede haber protestas (se
  trabaja un 20 % menos) y con 0,9, una revuelta que echa al jefe y baja los impuestos. Cada 4
  años hay elecciones del alcalde o gobernador.
- Sucesos grandes, con su probabilidad al día: inundación (1/900), terremoto (1/2.400), gran
  incendio (1/1.200, desde villa), sequía larga (1/1.500), peste (1/3.000, desde villa), cometa
  (1/4.000), mercader extranjero (1/400) y veta de mina (1/1.500).
- Relaciones, una vez por estación, entre vecinos a 3 zonas o menos. Alianza con 60 o más (se
  rompe por debajo de 20) y rivalidad con −40 o menos. Dos vecinos del mismo tipo y llenos restan
  1 punto por estación (en la 3.2 restaban 3, y con el mapa lleno casi todos eran rivales). Entre rivales, una escaramuza el 6 % de
  las estaciones: el que pierde pierde el 0,4 % de su gente y el 5 % de sus recursos. Una villa o
  ciudad puede exigir tributo a un pueblo vecino 20 veces más pequeño y 5 veces más débil: el 15 %
  del oro y el 5 % de la comida cada estación, hasta que el pueblo se rebela.
- Las reglas del consejo eligen investigar, un monumento o los impuestos solo cuando no hay nada
  útil que construir o una de cada cinco veces. Un monumento solo se empieza si sobra el doble de
  lo que cuesta. Sin estas condiciones, el mundo crecía la mitad de rápido.
- Ritmo: para compensar estos gastos, la natalidad pasa de 1,3 a 1,4 hijos al año por mujer de
  18 a 40 años. Medido con la simulación rápida: 377.000 personas en el año 90 y 468.000 en el 95.

### Versiones

Todo se publicó junto en la versión 3.0 (25-10-2026).
