// Versiones de La aldea, de la más nueva a la más antigua. Las enseña la barra de estado de abajo
// y la sección Novedades. Cada cambio que se publique añade una versión arriba del todo.

export const VERSIONES = [
  {
    version: "3.4.1",
    fecha: "27-10-2026",
    titulo: "Minimapa del mundo",
    cambios: [
      "El minimapa ya no enseña solo tu asentamiento: enseña el trozo del mundo donde está la vista, con las zonas de alrededor.",
      "Cada zona sale con el color de su terreno, y los asentamientos vecinos como bloques del color de su tipo.",
      "Al moverte por el mundo, el minimapa te sigue. Al pulsarlo, la vista salta a ese punto, también fuera de tu asentamiento.",
    ],
  },
  {
    version: "3.4",
    fecha: "25-10-2026",
    titulo: "Un solo mapa",
    cambios: [
      "El mundo entero es un solo mapa. Aleja la vista o arrastra más allá de los árboles y verás los asentamientos de al lado, con su gente moviéndose.",
      "Entre un asentamiento y otro hay bosque, pradera, charcas y los caminos que los unen.",
      "Pulsa en otro asentamiento para entrar en él: la vista se queda en el mismo sitio.",
      "Solo se carga lo que tienes cerca, así que puedes recorrer el mundo sin que la web se haga pesada.",
      "Las villas y ciudades de antes de la 3.3 también pueden crecer.",
    ],
  },
  {
    version: "3.3",
    fecha: "25-10-2026",
    titulo: "Ciudades de verdad",
    cambios: [
      "El mundo es cuatro veces más grande: 48 × 48 zonas. Todo lo que había se ha movido al centro.",
      "Las villas y las ciudades ya no se fundan aparte: un pueblo lleno sube a villa creciendo sobre las zonas de al lado, y absorbe a los pueblos que vivían allí.",
      "Una villa llena sube a ciudad, y una ciudad llena se hace todavía más grande.",
      "Un pueblo ocupa una zona entera; una villa, 2 × 2; una ciudad, 3 × 3 o 4 × 4. Para recorrer una ciudad hay que moverse mucho.",
      "Los asentamientos que se quedan casi vacíos durante dos años se abandonan y su zona queda libre.",
      "El mapa del mundo marca el cuadrado que ocupa cada villa y cada ciudad.",
      "Las frases ya dicen «de la Villa» y «de la Ciudad», y los nombres repetidos llevan una coletilla al azar.",
    ],
  },
  {
    version: "3.2.1",
    fecha: "25-10-2026",
    titulo: "Menos rivales",
    cambios: [
      "Con el mapa del mundo lleno, casi todos los vecinos acababan siendo rivales y sus líneas tapaban el mapa.",
      "Ahora dos vecinos llenos compiten menos por el sitio, y la rivalidad vuelve a ser rara.",
    ],
  },
  {
    version: "3.2",
    fecha: "25-10-2026",
    titulo: "Cada sitio con su forma",
    cambios: [
      "Las aldeas nuevas ya no son todas iguales. Hay cuatro formatos: de río, de camino, de lago y de claro.",
      "En la de río, el río cruza la aldea y tiene dos puentes. La de camino tiene una calle larga y la muralla alargada. La de lago tiene el agua junto a la plaza; en el desierto es un oasis. La de claro está en medio del bosque, con la muralla redonda.",
      "El terreno elige el formato más a menudo: en el bosque salen más claros y en el desierto, más oasis.",
      "Cada aldea tiene su tamaño, y las casas, los campos, la cantera y los edificios se colocan donde hay sitio.",
      "Los pueblos, villas y ciudades son mucho más grandes. Los pueblos tienen calles que salen de la plaza; las villas, dos plazas; las ciudades, calles en cuadrícula y doble muralla.",
      "La aldea de siempre se queda como está, para no estropear su partida.",
    ],
  },
  {
    version: "3.1",
    fecha: "25-10-2026",
    titulo: "El mundo se expande",
    cambios: [
      "Las aldeas ya no se estancan en 8 o 10 personas. En cada casa caben 6 y una pareja puede tener más de dos hijos.",
      "Desde 14 habitantes, algún joven soltero se marcha a fundar otra aldea, siempre que queden solteros para formar parejas.",
      "A las aldeas pequeñas llega de vez en cuando un forastero joven.",
      "Los niños comen menos, y solo nacen niños si hay comida guardada para 5 días por persona.",
      "Si queda comida para menos de 3 días, la mitad de los leñadores y canteros se ponen a sacar comida.",
      "Medido sin Jev: en 30 años del mundo hay 10 aldeas y 2 pueblos, y nadie muere de hambre.",
    ],
  },
  {
    version: "3.0",
    fecha: "25-10-2026",
    titulo: "Una evolución larga",
    cambios: [
      "Las aldeas crecen por etapas. Con la muralla completa construyen pozo, granero, taller, torre de vigía y huertos nuevos.",
      "Después llegan el almacén de piedra, el templo, el dojo y el mercado. Al final mejoran lo que tienen: casas de piedra, muralla reforzada y faroles.",
      "Cada edificio hace algo y sale en el mapa. Con los años se estropea y hay que repararlo.",
      "Cada estación, el consejo de la aldea elige la siguiente obra o una fiesta. Lo decide Jev sin gastar más: sale del presupuesto de consejos.",
      "Bodas, inviernos duros y caravanas del mercado con lo que sobra.",
      "Pueblos, villas y ciudades tienen oro e impuestos, nueve edificios nuevos, avances que investigar y monumentos que tardan años.",
      "Hay descontento, protestas, revueltas y elecciones, y sucesos grandes como terremotos, inundaciones, la peste o un cometa.",
      "Los vecinos se alían, se hacen rivales con escaramuzas o pagan tributo a una ciudad. Se ve en el mapa del mundo.",
      "En Historia de cada aldea se ve su etapa y el estado de sus edificios. En Habitantes de los asentamientos grandes, su oro, avances, monumentos y relaciones.",
      "El panel de administración puede acelerar el mundo hasta ×1000.",
    ],
  },
  {
    version: "2.2",
    fecha: "25-10-2026",
    titulo: "Móvil más limpio e instalable",
    cambios: [
      "En el móvil, la barra de arriba es una sola línea baja: nombre, año y hora, gente del mundo y recursos.",
      "El año del mundo se ve siempre, también en el móvil y en pantallas medianas.",
      "Las cifras grandes se abrevian («311 mil», «1,7 M») para que la barra no se salga de la pantalla.",
      "En el móvil se acerca el mapa pellizcando; los botones de zoom dejan sitio y la barra de abajo es más baja.",
      "Icono nuevo con una casa de la aldea, y se puede instalar como aplicación en el móvil y en el ordenador.",
    ],
  },
  {
    version: "2.1",
    fecha: "24-10-2026",
    titulo: "Panel de administración",
    cambios: [
      "Nuevo panel de administración con contraseña, desde «Administración» en la barra de abajo.",
      "Tiempo: acelera el mundo hasta 60 veces o ponlo en pausa. Arriba se ve «En directo · ×10» o «En pausa».",
      "Gasto: lo que cuesta Jev hoy y cada día, un límite de dólares al día y un botón para apagar Jev.",
      "Servidor: cuándo se guardó el mundo por última vez, cuánta gente lo está mirando y un botón para guardarlo ya.",
    ],
  },
  {
    version: "2.0",
    fecha: "24-10-2026",
    titulo: "Un mundo que crece",
    cambios: [
      "Todo junto: aldeas sin límite, pueblos, villas y ciudades, caravanas, epidemias que se contagian y la historia del mundo.",
      "El mundo crece más deprisa: si nada se tuerce, llegará a medio millón de personas en unos 90 años del mundo, unos tres meses reales.",
      "El nombre del asentamiento de arriba a la izquierda ya no se parte en dos líneas en el móvil.",
    ],
  },
  {
    version: "1.5",
    fecha: "24-10-2026",
    titulo: "La historia del mundo",
    cambios: [
      "El mapa del mundo tiene dos subpestañas: Asentamientos e Historia.",
      "En Historia, una gráfica con la gente de todo el mundo año a año. Al pasar por encima se ve cuántos viven en aldeas, pueblos, villas y ciudades.",
      "Los grandes momentos quedan apartados y con su año: la segunda aldea, el primer pueblo, la primera villa, cada ciudad y cuando el mundo llega a 1.000, 10.000 o 100.000 personas.",
      "Debajo, lo último que ha pasado en el mundo.",
    ],
  },
  {
    version: "1.4",
    fecha: "24-10-2026",
    titulo: "Villas y ciudades",
    cambios: [
      "Cuando hay 3 pueblos cerca, nace una villa, de hasta 4.000 habitantes. Con 3 villas cerca nace una ciudad, de hasta 60.000.",
      "Las villas y ciudades tienen más notables, torres, muralla y barrios enteros de casas.",
      "Los asentamientos unidos por un camino y con mercado se mandan caravanas con lo que les sobra.",
      "Una epidemia puede pasar a los asentamientos de alrededor.",
      "Cuando un sitio se llena, su gente funda otro igual cerca o se va al más grande de la zona.",
      "Cuando se acaban los nombres, los nuevos dicen dónde quedan: «Villa de Mizuno del Norte».",
    ],
  },
  {
    version: "1.3",
    fecha: "24-10-2026",
    titulo: "Pueblos",
    cambios: [
      "Cuando hay 4 aldeas cerca, nace un pueblo con gente de cada una. Puede llegar a 400 habitantes.",
      "Un pueblo tiene mercado, templo, dojo, granero, posada y muchas casas, y gente andando por sus calles.",
      "Su consejo decide cada estación qué construir, si hacer una fiesta o si mandar gente a fundar una aldea.",
      "Sus notables (alcaldesa, sacerdote, capitán…) tienen nombre y ficha.",
      "Contador de personas de todo el mundo en la barra de arriba; al pulsarlo se abre el mapa del mundo.",
    ],
  },
  {
    version: "1.2",
    fecha: "24-10-2026",
    titulo: "Mapa del mundo",
    cambios: [
      "Nuevo botón arriba en la columna de iconos: el mapa del mundo, con sus zonas, sus terrenos y la niebla de lo que nadie ha visto.",
      "Cada asentamiento sale con su nombre y su población, unido por un camino con el que lo fundó. Púlsalo para entrar.",
      "Al lado, cuánta gente hay en el mundo, todos los asentamientos y los grandes momentos.",
      "Al entrar en la web se ve el asentamiento más poblado.",
    ],
  },
  {
    version: "1.1",
    fecha: "24-10-2026",
    titulo: "Aldeas sin límite",
    cambios: [
      "El mundo ya no se queda en dos aldeas: cuando una se llena, los que se van fundan otra en una zona de al lado.",
      "Cada zona del mundo tiene su terreno: pradera, bosque, desierto, nieve o pantano, con su suelo, sus árboles y su tiempo.",
      "Una aldea llena manda gente fuera aunque Jev no lo decida, para que el mundo siga creciendo.",
      "Jev tiene un presupuesto fijo al día. Si se acaba, deciden las reglas y la ficha lo dice.",
    ],
  },
  {
    version: "1.0.2",
    fecha: "24-10-2026",
    titulo: "La muralla ya avanza",
    cambios: [
      "La aldea se quedaba sin canteros con 15-19 de piedra y no empezaba nunca la muralla, que cuesta 20.",
      "Ahora, si no llega la piedra o la madera para la siguiente obra, Jev sabe que hace falta un cantero o un leñador.",
    ],
  },
  {
    version: "1.0.1",
    fecha: "24-10-2026",
    titulo: "Elegir con un clic",
    cambios: [
      "Vuelve a funcionar pulsar sobre un habitante en el mapa para elegirlo, y es más fácil acertar.",
      "Al pasar el ratón por encima de alguien se ve su nombre y el cursor cambia.",
      "«Qué es La aldea» ocupa todo el ancho del panel, sin hueco a la derecha.",
    ],
  },
  {
    version: "1.0",
    fecha: "24-10-2026",
    titulo: "Dos aldeas",
    cambios: [
      "Cuando la aldea llegue a 20 habitantes, el primero que se marche fundará la Aldea del río.",
      "Los que se marchen después irán a vivir con él. Las dos aldeas viven a la vez, cada una con su mapa, sus familias y su historia.",
      "Pulsa el nombre de arriba a la izquierda para cambiar de aldea.",
      "En la ficha de cada habitante, el año de llegada ya es el de verdad, también para los forasteros.",
    ],
  },
  {
    version: "0.13",
    fecha: "24-10-2026",
    titulo: "Música y sonidos",
    cambios: [
      "Botón de altavoz arriba: música tranquila de día y otra de noche, el río, la lluvia, el viento y algún pájaro.",
      "Suena una alerta cuando atacan los monstruos, golpes en la pelea y una melodía cuando nace alguien o se forma una pareja.",
      "Empieza apagado y se recuerda lo que elijas.",
      "En el móvil, los botones de zoom ya no se ven a través de los paneles.",
    ],
  },
  {
    version: "0.12",
    fecha: "24-10-2026",
    titulo: "La vida de cada uno",
    cambios: [
      "La ficha de cada habitante tiene una subpestaña «Su vida»: cómo llegó, sus parejas, hijos, oficios, exploraciones y heridas.",
      "En Familias, la vida de cualquier persona, también de las que ya no están, hasta cómo murió o se marchó.",
      "Un resumen del día bajo la barra de arriba con lo más importante de las últimas horas.",
    ],
  },
  {
    version: "0.11",
    fecha: "24-10-2026",
    titulo: "Por los caminos",
    cambios: [
      "Los habitantes ya no atraviesan casas ni muros: los rodean y salen por las puertas de la muralla.",
      "Prefieren ir por los caminos y cruzan el río por el puente.",
    ],
  },
  {
    version: "0.10",
    fecha: "24-10-2026",
    titulo: "Monstruos a la vista",
    cambios: [
      "Los ataques se ven en el mapa: slimes, serpientes, murciélagos, arañas, lagartos o topos salen del bosque.",
      "Si los guardias los frenan, pelean en la puerta de la muralla y huyen entre humo.",
      "Si no, entran hasta la plaza a llevarse comida y después se van.",
    ],
  },
  {
    version: "0.9",
    fecha: "24-10-2026",
    titulo: "Iconos, luces y clima",
    cambios: [
      "Cada habitante lleva sobre la cabeza lo que está haciendo: su herramienta, comida, un corazón, una bolsa o una «z» si duerme.",
      "De noche se encienden las ventanas, la puerta del almacén, los faroles y el molino.",
      "Llueve de vez en cuando, nieva en invierno, caen hojas en otoño y pétalos en primavera.",
    ],
  },
  {
    version: "0.8",
    fecha: "24-10-2026",
    titulo: "Historia y crónica, juntas",
    cambios: [
      "Historia y Crónica pasan a ser una sola sección: cifras de hoy, filtros por tipo y lo que ha pasado por días.",
      "En grande añade la historia año a año al lado.",
      "Las llamadas y el coste de Jev se guardan con la partida y ya no vuelven a cero al reiniciar.",
    ],
  },
  {
    version: "0.7",
    fecha: "24-10-2026",
    titulo: "Qué es La aldea y novedades",
    cambios: [
      "Nueva sección «Qué es La aldea», con el botón de información de la columna izquierda.",
      "Barra de estado abajo del todo con la versión actual.",
      "Sección «Novedades» con los cambios de cada versión.",
    ],
  },
  {
    version: "0.6",
    fecha: "24-10-2026",
    titulo: "Historia en grande",
    cambios: [
      "Historia se abre desde la columna izquierda con los últimos sucesos.",
      "El botón de maximizar la pasa a toda la pantalla: los sucesos de todo el año y la historia año a año.",
    ],
  },
  {
    version: "0.5",
    fecha: "24-10-2026",
    titulo: "Secciones rediseñadas",
    cambios: [
      "Habitantes con subpestañas por edad y un punto que dice si están despiertos, durmiendo o fuera.",
      "Ficha de cada habitante con subpestañas Ahora, Familia y Decisiones.",
      "Crónica con filtros por tipo de suceso y agrupada por días.",
      "Leyenda para leer el árbol de familias.",
    ],
  },
  {
    version: "0.4",
    fecha: "24-10-2026",
    titulo: "Se llama La aldea",
    cambios: [
      "El mundo pasa a llamarse La aldea.",
      "Ya no sale un habitante elegido al azar; la selección se quita pulsando en el mapa o con Escape.",
    ],
  },
  {
    version: "0.3",
    fecha: "24-10-2026",
    titulo: "Una aldea nueva",
    cambios: [
      "Hierba más viva, caminos de tierra con curvas y bosque espeso en los bordes.",
      "Almacén de paja, cuatro tipos de casa, puestos y faroles en la plaza.",
      "Huertos vallados con trigo, muralla de piedra y un puente sobre el río.",
    ],
  },
  {
    version: "0.2",
    fecha: "24-10-2026",
    titulo: "La ventana",
    cambios: [
      "El mapa ocupa toda la pantalla y la interfaz flota encima.",
      "Modo claro y modo oscuro.",
    ],
  },
  {
    version: "0.1",
    fecha: "24-10-2026",
    titulo: "Nace la aldea",
    cambios: [
      "Ocho habitantes empiezan a vivir. Jev decide por ellos.",
      "Mapa en directo, crónica, árbol de familias e historia.",
    ],
  },
];

export const ACTUAL = VERSIONES[0];
