# Brief de diseño — Aplicación "Señas" (reconocedor de LSE)

Este documento describe la aplicación y todo lo necesario para rediseñar su interfaz sin
romper la lógica. Objetivo: mejorar mucho el diseño visual manteniendo intacta la
funcionalidad.

Antes de escribir código, carga la skill `artifact-design` para calibrar el nivel de diseño,
aunque esta aplicación NO es un Artifact (ver restricciones).

---

## 1. Qué es

Aplicación web que reconoce signos de la Lengua de Signos Española (LSE) a partir de la
cámara, y funciona entera en el navegador. Es una herramienta de accesibilidad. Público:
personas que aprenden LSE y personas sordas que quieren comunicarse. El diseño debe
transmitir claridad, cercanía y confianza.

Es una interfaz que se opera, no un documento: prima el diseño de información. La cámara es
la protagonista. Los estados (cargando, grabando, reconociendo, acierto, error) deben leerse
de un vistazo.

---

## 2. Estructura de modos y funcionalidades

Dos modos principales, elegibles con un interruptor arriba. Dentro de cada uno, un
subinterruptor entre "Signos" y "Abecedario". En total, cuatro vistas:

**Aprender → Signos**: la persona elige un signo de una lista, ve un vídeo de cómo se hace,
lo imita frente a la cámara y pulsa un botón para grabar; la aplicación le dice si lo ha
hecho bien (correcto / casi / no seguro). En español.

**Aprender → Abecedario**: elige una letra, ve una imagen de cómo se hace, y forma la letra
con la mano; el reconocimiento es en vivo (por fotograma, sin botón) y muestra la letra que
detecta; cuando coincide con la elegida, indica que es correcta.

**Comunicar → Signos**: la persona signa (con botón) y cada signo reconocido se añade a un
texto. Hay un selector de idioma (Español / English) que cambia el idioma de ese texto.
Botón para borrar.

**Comunicar → Abecedario**: la persona forma letras con la mano; el reconocimiento en vivo
muestra la letra actual, y con botones va deletreando: "Añadir letra", "Espacio", "Borrar".

Notas de alcance: el reconocedor de abecedario cubre 19 letras estáticas (faltan las que
llevan movimiento). El selector de idioma solo aparece en Comunicar → Signos.

---

## 3. Contrato técnico: NO cambiar (o la aplicación deja de funcionar)

La lógica está en `web/app.js` y usa estos elementos por su `id`. El rediseño puede cambiar
por completo el aspecto, la maquetación y las clases de estilo, pero DEBE conservar estos
`id`, y las dos clases que el código activa y desactiva.

**Generales**
- `video` — `<video>` oculto (fuente de la cámara).
- `lienzo` — `<canvas>` donde se dibuja la cámara y los puntos. Vista principal, relación 4:3.
- `estado` — texto de estado. El código escribe su contenido.

**Interruptor de modo y paneles**
- `tab-aprender`, `tab-comunicar` — botones del interruptor principal.
- `panel-aprender`, `panel-comunicar` — contenedores de cada modo.

**Modo Aprender**
- `sub-apr-signos`, `sub-apr-abc` — subinterruptor Signos / Abecedario.
- `apr-signos` — subpanel de signos. Contiene:
  - `selector` — `<select>` de signo a practicar (el código lo rellena).
  - `referencia` — `<video>` de demostración del signo.
  - `grabar-aprender` — botón para grabar el signo.
  - `resultado-aprender` — resultado (el código le pone el color inline).
- `apr-abc` — subpanel de abecedario. Contiene:
  - `selector-letra` — `<select>` de letra a practicar (el código lo rellena).
  - `ref-letra` — `<img>` con la forma de la letra.
  - `letra-viva-apr` — muestra la letra reconocida en vivo (el código escribe su texto).
  - `resultado-letra` — resultado (el código le pone el color inline).

**Modo Comunicar**
- `sub-com-signos`, `sub-com-abc` — subinterruptor Signos / Abecedario.
- `com-signos` — subpanel de signos. Contiene:
  - `idioma` — `<select>` con opciones `value="es"` y `value="en"`.
  - `grabar-comunicar` — botón para signar.
  - `borrar` — botón para borrar el texto.
  - `mensaje` — contenedor del texto reconocido.
- `com-abc` — subpanel de abecedario. Contiene:
  - `letra-viva-com` — muestra la letra reconocida en vivo (el código escribe su texto).
  - `mensaje-abc` — contenedor del texto deletreado.
  - `anadir-letra`, `espacio`, `borrar-abc` — botones para deletrear.

**Clases que el código activa/desactiva (deben existir en el CSS con ese nombre)**
- `activa` — se pone en el botón (de modo o de subinterruptor) que está activo.
- `oculto` — se pone en el panel o subpanel que no está visible. Debe ocultar (`display: none`).

**Otros contratos**
- El `<canvas id="lienzo">` se redimensiona por código al tamaño del vídeo; su contenedor
  debe mostrarlo completo (4:3).
- El código escribe texto en `estado`, `resultado-aprender`, `resultado-letra`, `mensaje`,
  `mensaje-abc`, `letra-viva-apr`, `letra-viva-com`; deja sitio para textos variables.
- Los `<script>` del final (MediaPipe y `app.js` como módulo) se mantienen tal cual.

---

## 4. Restricciones técnicas

- **Es una web normal, NO un Artifact.** Usa la cámara, carga librerías externas por CDN
  (MediaPipe y LiteRT.js) y modelos locales. El formato Artifact bloquea todo eso. El
  rediseño es un `index.html` autónomo servido como web estática.
- Se puede usar CSS moderno y fuentes de Google por enlace.
- **Tema claro y oscuro** con tokens de color, respetando `prefers-color-scheme` y el atributo
  `data-theme` en la raíz.
- **Responsive**: se usa mucho en móvil; la cámara debe ser grande; nada desborda en horizontal.
- **Accesibilidad**: buen contraste, foco de teclado visible, respetar `prefers-reduced-motion`.
  Es una herramienta para personas sordas; la claridad visual es prioritaria.

---

## 5. Dirección de diseño (punto de partida, se puede mejorar)

El diseño actual usa: acento turquesa (comunicación y claridad, ligado al color de los puntos
de la mano), neutros fríos, tipografías Bricolage Grotesque para títulos y Onest para la
interfaz, cámara con esquinas redondeadas y etiqueta de estado superpuesta.

Libertad para proponer una identidad mejor, siempre que:
- Siga anclada al tema: manos, comunicación, accesibilidad, LSE.
- Evite los looks genéricos de IA (crema con serif y terracota; gradiente morado-azul; verde
  ácido sobre negro; todo centrado y esquinas muy redondeadas por defecto).
- Concentre la audacia en un sitio y mantenga el resto tranquilo.
- Cuide los estados (grabando, acierto, error, letra en vivo) con color y forma, no solo texto.

---

## 6. Archivos

En la carpeta `web/`:
- `index.html` — la página. Es lo que se rediseña.
- `app.js` — lógica. No tocar salvo para acompañar cambios de `id`/clases; si se cambian, hay
  que actualizarlo en consecuencia.
- `modelo.js`, `preprocesado.js` — carga y ejecución de los modelos. No tocar.
- `modelo.tflite`, `abecedario.tflite` — modelos. No tocar.
- `vocabulario.json` — nombres de los signos en español e inglés. No tocar.
- `abecedario.json` — lista de letras. No tocar.
- `referencias/` — vídeos de demostración de los signos. No tocar.
- `abecedario_ref/` — imágenes de las letras. No tocar.

## 7. Cómo verlo en marcha

Desde la carpeta del proyecto:

```
python3 src/servidor.py
```

Y abrir http://localhost:8000, permitiendo el acceso a la cámara. El servidor no usa caché,
así que los cambios se ven al recargar.
