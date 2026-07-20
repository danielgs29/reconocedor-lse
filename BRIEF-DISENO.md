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

## 2. Funcionalidades y modos

La aplicación tiene dos modos, elegibles con un interruptor arriba:

- **Aprender**: la persona elige un signo de una lista, ve un vídeo de cómo se hace, lo imita
  frente a la cámara y la aplicación le dice si lo ha hecho bien (correcto / casi / no seguro).
  Todo en español. Sin selector de idioma.
- **Comunicar**: la persona signa libremente y cada signo reconocido se añade a un texto. Hay
  un selector de idioma (Español / English) que cambia el idioma de ese texto, para que quien
  no sepa signar pueda leer. Botón para signar y botón para borrar.

Ampliación prevista (aún no implementada, deja hueco en el diseño): un submodo **abecedario**
dentro de cada modo, para practicar y deletrear letras con la mano.

---

## 3. Contrato técnico: NO cambiar (o la aplicación deja de funcionar)

La lógica está en `web/app.js` y usa estos elementos por su `id`. El rediseño puede cambiar
por completo el aspecto, la maquetación y las clases de estilo, pero DEBE conservar estos
`id` y estas dos clases que el código activa y desactiva.

Elementos por `id` que deben existir:

- `video` — elemento `<video>` (oculto, fuente de la cámara).
- `lienzo` — `<canvas>` donde se dibuja la cámara y los puntos. Es la vista principal.
- `estado` — texto de estado (cargando, grabando, etc.). El código escribe su contenido.
- `tab-aprender`, `tab-comunicar` — los dos botones del interruptor de modo.
- `panel-aprender`, `panel-comunicar` — los dos contenedores de cada modo.
- `selector` — `<select>` de signo a practicar (modo Aprender). El código lo rellena.
- `referencia` — `<video>` con la demostración del signo (modo Aprender).
- `grabar-aprender` — botón para grabar el signo (modo Aprender).
- `resultado-aprender` — donde se escribe el resultado. El código le pone el color inline.
- `idioma` — `<select>` de idioma con opciones `value="es"` y `value="en"` (modo Comunicar).
- `grabar-comunicar` — botón para signar (modo Comunicar).
- `borrar` — botón para borrar el texto (modo Comunicar).
- `mensaje` — contenedor del texto reconocido (modo Comunicar).

Clases que el código activa/desactiva (deben existir en el CSS con ese nombre):

- `activa` — se pone en el botón de modo activo. Estíla el estado seleccionado del interruptor.
- `oculto` — se pone en el panel que no está visible. Debe ocultar el elemento (`display: none`).

Otros contratos:

- El `<canvas id="lienzo">` se redimensiona por código al tamaño del vídeo; su contenedor debe
  poder mostrarlo completo (relación de aspecto 4:3).
- El código escribe en `estado`, `resultado-aprender` y `mensaje` mediante texto; deja sitio
  para textos de longitud variable.
- Los `<script>` del final (MediaPipe y `app.js` como módulo) deben mantenerse tal cual.

---

## 4. Restricciones técnicas

- **Es una web normal, NO un Artifact.** Usa la cámara, carga librerías externas por CDN
  (MediaPipe y LiteRT.js) y un modelo local. El formato Artifact bloquea todo eso, así que no
  se puede publicar como Artifact. El rediseño es un `index.html` autónomo que se sirve como
  web estática.
- Se puede usar CSS moderno y fuentes de Google por enlace (no hay CSP que lo impida).
- **Tema claro y oscuro**: debe verse bien en los dos, con tokens de color y respetando
  `prefers-color-scheme` y el atributo `data-theme` en la raíz.
- **Responsive**: se usa mucho en móvil (la cámara del teléfono). La cámara debe ser grande y
  cómoda; nada debe desbordar en horizontal.
- **Accesibilidad**: buen contraste, foco de teclado visible, respetar
  `prefers-reduced-motion`. Es una herramienta para personas sordas; la claridad visual es
  prioritaria.

---

## 5. Dirección de diseño (punto de partida, se puede mejorar)

El diseño actual usa: acento turquesa (comunicación y claridad, ligado al color de los puntos
de la mano), neutros fríos, tipografías Bricolage Grotesque para títulos y Onest para la
interfaz. La cámara con esquinas redondeadas y una etiqueta de estado superpuesta.

Libertad para proponer una identidad mejor, siempre que:

- Siga anclada al tema: manos, comunicación, accesibilidad, LSE.
- Evite los looks genéricos de IA (crema con serif y terracota; gradiente morado-azul; verde
  ácido sobre negro; todo centrado y con esquinas muy redondeadas por defecto).
- Concentre la audacia en un sitio y mantenga el resto tranquilo.
- Cuide los estados (grabando, acierto, error) con color y forma, no solo texto.

---

## 6. Archivos

En la carpeta `web/`:

- `index.html` — la página. Es lo que se rediseña.
- `app.js` — lógica (no tocar salvo para acompañar cambios de `id`/clases; si se cambian, hay
  que actualizarlo en consecuencia).
- `modelo.js`, `preprocesado.js` — carga y ejecución del modelo. No tocar.
- `modelo.tflite`, `vocabulario.json`, `referencias/` — modelo, nombres y vídeos. No tocar.

## 7. Cómo verlo en marcha

Desde la carpeta del proyecto:

```
python3 -m http.server 8000 --directory web
```

Y abrir http://localhost:8000 en el navegador, permitiendo el acceso a la cámara.
