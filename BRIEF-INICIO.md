# Brief de diseño — Pantalla de inicio de "Signia" (reconocedor de LSE)

Este documento describe una pantalla de inicio nueva para la aplicación Signia. El objetivo
es que, al entrar en la web, la persona vea primero una pantalla que explica qué es y qué
puede hacer, y que con un botón pase a la aplicación que ya existe.

Antes de escribir código, carga la skill `artifact-design` para calibrar el nivel de diseño,
aunque esta pantalla NO es un Artifact (ver restricciones). Debe quedar visualmente al mismo
nivel, o mejor, que la aplicación a la que da paso.

Muy importante: esta pantalla tiene que verse claramente de la misma familia que la
aplicación. No es una página aparte con otra estética. Comparte colores, tipografías, logo y
motivos visuales, que se detallan más abajo.

---

## 1. Qué es Signia

Aplicación web que reconoce signos de la Lengua de Signos Española a partir de la cámara, y
funciona entera en el navegador. Es una herramienta de accesibilidad para dos públicos:
personas que están aprendiendo LSE y personas sordas que quieren comunicarse con alguien que
no signa.

Dos ideas que conviene transmitir en la pantalla de inicio porque son puntos fuertes reales:
- Funciona sin enviar nada a ningún servidor. La imagen de la cámara se procesa en el propio
  dispositivo y no sale de él. Es un buen argumento de privacidad.
- Reconoce tanto signos completos como el alfabeto dactilológico, que es deletrear palabras
  con la mano letra a letra.

Tono: claro, cercano y de confianza. Es una herramienta de accesibilidad, así que la
legibilidad y el buen contraste son prioritarios.

---

## 2. Qué debe contener la pantalla

La pantalla de inicio debe explicar la aplicación de un vistazo y llevar a ella. Contenido
recomendado, en orden:

**Cabecera**: el logo de Signia y, arriba a la derecha, el botón de cambio de tema claro y
oscuro (el mismo comportamiento que en la app, ver contrato técnico).

**Zona principal**: una frase grande que diga qué es la aplicación. Por ejemplo, "Reconoce la
Lengua de Signos Española con la cámara, desde el navegador". Debajo, una frase más pequeña
que explique para quién es y que funciona sin conexión y sin enviar la imagen a ningún sitio.

**Los dos modos**: explicar brevemente las dos formas de usarla, que son el corazón de la
aplicación.
- Aprender: eliges un signo o una letra, ves cómo se hace y lo imitas frente a la cámara; la
  aplicación te dice si lo has hecho bien.
- Comunicar: signas y la aplicación va escribiendo lo que reconoce, en español o en inglés;
  también puedes deletrear con el alfabeto.

**Cómo funciona en tres pasos**, para que quede claro que es sencillo: permitir el acceso a
la cámara, elegir un modo, y signar frente a la cámara.

**Botón principal**: un único botón claro y destacado, del tipo "Empezar" o "Abrir la
aplicación", que lleva a la aplicación. Es la acción principal de la pantalla y debe ser
inconfundible. El destino técnico del enlace está en el contrato de abajo.

**Nota honesta de alcance**, discreta, al pie: la aplicación reconoce un vocabulario concreto
de signos y una parte del alfabeto; es un proyecto de fin de máster centrado en demostrar el
reconocimiento, no un traductor completo de LSE. No hace falta que sea llamativa, pero es
importante que esté para no prometer de más.

No debe pedir la cámara en esta pantalla. La cámara se pide ya dentro de la aplicación. La
pantalla de inicio es solo presentación y punto de entrada.

---

## 3. Contrato técnico: lo único que no se puede cambiar

Esta pantalla es un archivo HTML autónomo, servido como web estática. Lo único que la lógica
necesita es que el botón principal lleve a la aplicación:

- El botón principal debe ser un enlace a `app.html`. Puede ser un `<a href="app.html">` con
  aspecto de botón, o un botón que navegue a esa dirección. Esa es la aplicación que ya
  existe y funciona.

**Tema claro y oscuro.** Debe funcionar igual que en la aplicación, para que al pasar de una
pantalla a otra el tema no cambie de golpe:
- La preferencia se guarda en `localStorage` con la clave `signia-tema`, con valor `"light"`
  o `"dark"`.
- El tema activo se aplica poniendo el atributo `data-theme` con ese valor en el elemento
  raíz (`<html>`).
- Al cargar, si hay una preferencia guardada en `signia-tema`, se aplica; si no, se respeta
  la preferencia del sistema con `prefers-color-scheme`.
- El botón de tema alterna entre claro y oscuro y guarda la elección.

Este es exactamente el mismo comportamiento del conmutador de tema que ya tiene la
aplicación, para que sean consistentes.

---

## 4. Restricciones técnicas

- Es una web normal, no un Artifact. Se sirve como archivo estático. Puede usar CSS moderno y
  fuentes de Google por enlace.
- Responsive de verdad. Se usará mucho en móvil. Nada debe desbordar en horizontal y el botón
  principal tiene que quedar cómodo en pantalla pequeña.
- Accesibilidad: buen contraste, foco de teclado visible, respetar `prefers-reduced-motion`.
  Es una herramienta para personas sordas, así que la claridad visual manda.
- Sin dependencias raras. Solo HTML, CSS y, si hace falta, un poco de JavaScript para el
  conmutador de tema.

---

## 5. Identidad visual: debe coincidir con la aplicación

La aplicación ya tiene una identidad definida. La pantalla de inicio la comparte. Estos son
los valores exactos que usa hoy la app; conviene reutilizarlos como tokens de color.

**Tipografías** (por enlace de Google Fonts):
- Space Grotesk para títulos y para la interfaz en general.
- IBM Plex Mono para etiquetas pequeñas, estados y detalles tipo terminal.

**Logo**: la palabra "Signia" en mayúsculas, con un guion bajo final en color de acento, así:
`SIGNIA_`. La parte final y el guion pueden ir en el turquesa de acento. Es un guiño a lo
técnico, sobrio.

**Colores en tema oscuro** (es el tema por defecto):
- Fondo `#0b0f0e`, superficie `#121a19`, superficie secundaria `#0d1413`, superficie elevada
  `#141d1b`.
- Texto `#e9efee`, texto apagado `#8fa09d`, borde `#263230`.
- Acento turquesa `#1cc3b8`, tinta sobre acento `#04211e`, acento tenue
  `rgba(28,195,184,0.25)`.
- Estados: correcto `#5fdc85`, aviso `#f0b45e`, error `#ff7a7a`.

**Colores en tema claro**:
- Fondo `#eef1f0`, superficie `#ffffff`, superficie secundaria `#e4e9e8`, superficie elevada
  `#e4e9e8`.
- Texto `#14201e`, texto apagado `#5a6a68`, borde `#d3dcda`.
- Acento turquesa `#0c9c93`, tinta sobre acento `#ffffff`.

**Motivos visuales que ya usa la app** y que dan cohesión si se reaprovechan con criterio:
- Esquinas de encuadre de cámara: cuatro pequeñas escuadras turquesa en las esquinas de un
  recuadro, como el visor de una cámara.
- Chip de estado en IBM Plex Mono, en mayúsculas y con un punto turquesa que parece encendido.
- Botones de acción en turquesa con texto oscuro, y botones secundarios sobrios.
- Esquinas redondeadas medias, ni cuadradas ni excesivamente redondas.

**Dirección de diseño**: el acento turquesa está ligado al color de los puntos de la mano que
dibuja la aplicación, así que es coherente apoyarse en la idea de manos y comunicación. Hay
libertad para proponer una composición atractiva para el inicio, un poco más expresiva que la
app porque aquí sí es una portada, siempre que:
- Se note que es la misma familia visual que la aplicación.
- Evite los looks genéricos de aplicación hecha por inteligencia artificial: crema con serif y
  terracota; gradiente morado a azul; verde ácido sobre negro; todo centrado y con esquinas
  muy redondeadas por defecto.
- Concentre la audacia en un sitio, por ejemplo el titular o una representación de la mano y
  sus puntos, y mantenga el resto tranquilo.

---

## 6. Cómo verlo en marcha

Desde la carpeta del proyecto:

```
python3 src/servidor.py
```

Y abrir la dirección local que indique. El servidor no usa caché, así que los cambios se ven
al recargar. Durante el desarrollo, el archivo de inicio puede probarse por su nombre; en el
despliegue se hará que sea la primera página que se carga y que la aplicación pase a
`app.html`.
