// Aplicación con dos modos (Aprender / Comunicar), y dentro de cada uno dos submodos:
// Signos (dinámicos) y Abecedario (letras estáticas de la mano).

import { extraerFrame, prepararEntrada, manoAEntrada } from "./preprocesado.js";
import { cargarModelo, predecir, cargarAbecedario, predecirLetra, UMBRAL } from "./modelo.js";

const UMBRAL_LETRA = 0.7;
const DURACION_GRABACION_MS = 2500;
// Tiempo que hay que sostener una letra para darla por buena. Evita el parpadeo.
const SOSTENER_LETRA_MS = 600;

const $ = (id) => document.getElementById(id);
const video = $("video"), lienzo = $("lienzo"), contexto = lienzo.getContext("2d"), estado = $("estado");
const tabAprender = $("tab-aprender"), tabComunicar = $("tab-comunicar");
const panelAprender = $("panel-aprender"), panelComunicar = $("panel-comunicar");
// Aprender
const subAprSignos = $("sub-apr-signos"), subAprAbc = $("sub-apr-abc");
const aprSignos = $("apr-signos"), aprAbc = $("apr-abc");
const selector = $("selector"), referencia = $("referencia");
const botonAprender = $("grabar-aprender"), resultadoAprender = $("resultado-aprender");
const selectorLetra = $("selector-letra"), refLetra = $("ref-letra");
const letraVivaApr = $("letra-viva-apr"), resultadoLetra = $("resultado-letra");
const anilloApr = $("anillo-apr");
const fallo = $("fallo");
// Comunicar
const subComSignos = $("sub-com-signos"), subComAbc = $("sub-com-abc");
const comSignos = $("com-signos"), comAbc = $("com-abc");
const selectorIdioma = $("idioma"), botonComunicar = $("grabar-comunicar"), botonBorrar = $("borrar"), mensaje = $("mensaje");
const letraVivaCom = $("letra-viva-com"), mensajeAbc = $("mensaje-abc"), anilloCom = $("anillo-com");
const botonAnadir = $("anadir-letra"), botonEspacio = $("espacio"), botonBorrarAbc = $("borrar-abc");

let vocab = [], letras = [];
let idioma = "es";
let modoActual = "aprender";
let submodoApr = "signos", submodoCom = "signos";
let grabando = false, bufferFrames = [];
let fraseComunicar = [], fraseAbc = [];
let letraActual = null, reconociendoLetra = false;
// Estado del sostenido: qué letra se está sosteniendo, desde cuándo, y cuál quedó confirmada.
let letraCandidata = null, candidataDesde = 0, letraConfirmada = null;

const nombreSigno = (i) => vocab[i][idioma];

const espejo = document.createElement("canvas");
const contextoEspejo = espejo.getContext("2d");

// --- MediaPipe ---
const holistic = new Holistic({ locateFile: (a) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${a}` });
holistic.setOptions({ modelComplexity: 1, smoothLandmarks: true, refineFaceLandmarks: false, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });

holistic.onResults((r) => {
  if (lienzo.width !== r.image.width) { lienzo.width = r.image.width; lienzo.height = r.image.height; }
  contexto.clearRect(0, 0, lienzo.width, lienzo.height);
  contexto.drawImage(r.image, 0, 0, lienzo.width, lienzo.height);
  if (r.poseLandmarks) {
    drawConnectors(contexto, r.poseLandmarks, POSE_CONNECTIONS, { color: "rgba(230,238,237,0.55)", lineWidth: 2 });
    drawLandmarks(contexto, r.poseLandmarks, { color: "rgba(230,238,237,0.75)", lineWidth: 1, radius: 2 });
  }
  for (const mano of [r.leftHandLandmarks, r.rightHandLandmarks]) {
    if (mano) {
      drawConnectors(contexto, mano, HAND_CONNECTIONS, { color: "#1cc3b8", lineWidth: 4 });
      drawLandmarks(contexto, mano, { color: "#8fe6df", lineWidth: 1, radius: 3 });
    }
  }

  if (grabando) { bufferFrames.push(extraerFrame(r)); return; }
  const submodo = modoActual === "aprender" ? submodoApr : submodoCom;
  if (submodo === "abecedario") reconocerLetraEnVivo(r);
});

function enviarFrameVolteado() {
  if (espejo.width !== video.videoWidth && video.videoWidth) { espejo.width = video.videoWidth; espejo.height = video.videoHeight; }
  contextoEspejo.save();
  contextoEspejo.translate(espejo.width, 0);
  contextoEspejo.scale(-1, 1);
  contextoEspejo.drawImage(video, 0, 0, espejo.width, espejo.height);
  contextoEspejo.restore();
  return holistic.send({ image: espejo });
}
const camara = new Camera(video, { onFrame: enviarFrameVolteado, width: 640, height: 480 });

// --- Reconocimiento de letra en vivo (abecedario) ---
// La letra solo se da por buena cuando se mantiene estable SOSTENER_LETRA_MS.
// Mientras tanto, el anillo se va rellenando y la letra se muestra atenuada.
function refsLetra() {
  const enApr = modoActual === "aprender";
  return { letraEl: enApr ? letraVivaApr : letraVivaCom, anilloEl: enApr ? anilloApr : anilloCom };
}

// Deja el estado de la letra a cero (sin candidata, sin confirmar, anillos vacíos).
function reiniciarLetra() {
  letraCandidata = null; letraConfirmada = null; letraActual = null;
  for (const el of [letraVivaApr, letraVivaCom]) { el.textContent = "–"; el.classList.remove("pendiente"); }
  for (const el of [anilloApr, anilloCom]) el.style.setProperty("--p", 0);
  resultadoLetra.textContent = "";
}

async function reconocerLetraEnVivo(r) {
  if (reconociendoLetra) return;
  const mano = r.leftHandLandmarks || r.rightHandLandmarks;
  const { letraEl, anilloEl } = refsLetra();

  // Sin mano: se reinicia el sostenido.
  if (!mano) {
    letraCandidata = null; letraConfirmada = null; letraActual = null;
    letraEl.textContent = "–"; letraEl.classList.remove("pendiente");
    anilloEl.style.setProperty("--p", 0);
    return;
  }

  reconociendoLetra = true;
  try {
    const { letra, confianza } = await predecirLetra(manoAEntrada(mano));
    const ahora = Date.now();

    // Mano presente pero forma poco clara: no cuenta como candidata.
    if (confianza < UMBRAL_LETRA) {
      letraCandidata = null; letraConfirmada = null; letraActual = null;
      letraEl.textContent = "…"; letraEl.classList.remove("pendiente");
      anilloEl.style.setProperty("--p", 0);
      return;
    }

    // Si cambia la letra respecto al fotograma anterior, empieza a contar de cero.
    if (letra !== letraCandidata) { letraCandidata = letra; candidataDesde = ahora; }

    const progreso = Math.min((ahora - candidataDesde) / SOSTENER_LETRA_MS, 1);
    anilloEl.style.setProperty("--p", progreso);
    letraEl.textContent = letra;

    if (progreso >= 1) {
      // Sostenida el tiempo suficiente: se confirma.
      letraEl.classList.remove("pendiente");
      if (letraConfirmada !== letra) {
        letraConfirmada = letra;
        letraActual = letra;
        if (modoActual === "aprender" && submodoApr === "abecedario") {
          const acierto = letra === selectorLetra.value;
          resultadoLetra.textContent = acierto ? "¡Correcto!" : `Estás haciendo la ${letra}`;
          resultadoLetra.style.color = acierto ? "var(--good)" : "var(--warn)";
        }
      }
    } else {
      // Aún sostiéndola: se muestra atenuada y no se puede añadir todavía.
      letraEl.classList.add("pendiente");
      letraActual = null;
    }
  } finally {
    reconociendoLetra = false;
  }
}

// --- Grabación de un signo (submodo Signos) ---
async function grabarSigno() {
  botonAprender.disabled = true; botonComunicar.disabled = true;
  bufferFrames = []; grabando = true;
  let n = Math.round(DURACION_GRABACION_MS / 1000);
  estado.textContent = `Grabando… (${n})`;
  const cuenta = setInterval(() => { n -= 1; if (n > 0) estado.textContent = `Grabando… (${n})`; }, 1000);
  await new Promise((res) => setTimeout(res, DURACION_GRABACION_MS));
  clearInterval(cuenta); grabando = false;
  estado.textContent = "Reconociendo…";
  let prediccion = null;
  if (bufferFrames.length >= 3) prediccion = await predecir(prepararEntrada(bufferFrames));
  estado.textContent = "Listo.";
  botonAprender.disabled = false; botonComunicar.disabled = false;
  return prediccion;
}

async function practicar() {
  resultadoAprender.textContent = "";
  const p = await grabarSigno();
  const objetivo = parseInt(selector.value, 10);
  if (!p) { resultadoAprender.textContent = "No se detectaron manos"; resultadoAprender.style.color = "var(--muted)"; return; }
  const pct = Math.round(p.confianza * 100);
  if (p.confianza < UMBRAL) { resultadoAprender.textContent = `No lo tengo claro (${pct}%)`; resultadoAprender.style.color = "var(--muted)"; }
  else if (p.indice === objetivo) { resultadoAprender.textContent = `Correcto: ${vocab[objetivo].es} (${pct}%)`; resultadoAprender.style.color = "var(--good)"; }
  else { resultadoAprender.textContent = `Has hecho ${vocab[p.indice].es}; el objetivo era ${vocab[objetivo].es}`; resultadoAprender.style.color = "var(--warn)"; }
}

function cargarReferencia() { referencia.src = `referencias/${selector.value}.mp4`; referencia.play().catch(() => {}); }
function cargarRefLetra() { refLetra.src = `abecedario_ref/${selectorLetra.value}.jpg`; resultadoLetra.textContent = ""; }

// --- Comunicar: signos ---
const renderMensaje = () => { mensaje.textContent = fraseComunicar.map(nombreSigno).join(" "); };
async function signarComunicar() {
  const p = await grabarSigno();
  if (p && p.confianza >= UMBRAL) { fraseComunicar.push(p.indice); renderMensaje(); }
  else estado.textContent = idioma === "es" ? "No lo tengo claro, repite." : "Not sure, try again.";
}

// --- Comunicar: abecedario ---
const renderMensajeAbc = () => { mensajeAbc.textContent = fraseAbc.join(""); };

// --- Cambio de modo y submodo ---
function activarModo(modo) {
  modoActual = modo;
  const ap = modo === "aprender";
  tabAprender.classList.toggle("activa", ap);
  tabComunicar.classList.toggle("activa", !ap);
  panelAprender.classList.toggle("oculto", !ap);
  panelComunicar.classList.toggle("oculto", ap);
  reiniciarLetra();
}
function activarSubAprender(sub) {
  submodoApr = sub;
  subAprSignos.classList.toggle("activa", sub === "signos");
  subAprAbc.classList.toggle("activa", sub === "abecedario");
  aprSignos.classList.toggle("oculto", sub !== "signos");
  aprAbc.classList.toggle("oculto", sub !== "abecedario");
  reiniciarLetra();
}
function activarSubComunicar(sub) {
  submodoCom = sub;
  subComSignos.classList.toggle("activa", sub === "signos");
  subComAbc.classList.toggle("activa", sub === "abecedario");
  comSignos.classList.toggle("oculto", sub !== "signos");
  comAbc.classList.toggle("oculto", sub !== "abecedario");
  reiniciarLetra();
}

tabAprender.addEventListener("click", () => activarModo("aprender"));
tabComunicar.addEventListener("click", () => activarModo("comunicar"));
subAprSignos.addEventListener("click", () => activarSubAprender("signos"));
subAprAbc.addEventListener("click", () => activarSubAprender("abecedario"));
subComSignos.addEventListener("click", () => activarSubComunicar("signos"));
subComAbc.addEventListener("click", () => activarSubComunicar("abecedario"));
botonAprender.addEventListener("click", practicar);
botonComunicar.addEventListener("click", signarComunicar);
botonBorrar.addEventListener("click", () => { fraseComunicar = []; renderMensaje(); });
selector.addEventListener("change", cargarReferencia);
selectorLetra.addEventListener("change", cargarRefLetra);
selectorIdioma.addEventListener("change", () => { idioma = selectorIdioma.value; renderMensaje(); });
botonAnadir.addEventListener("click", () => { if (letraActual) { fraseAbc.push(letraActual); renderMensajeAbc(); } });
botonEspacio.addEventListener("click", () => { fraseAbc.push(" "); renderMensajeAbc(); });
botonBorrarAbc.addEventListener("click", () => { fraseAbc = []; renderMensajeAbc(); });

// --- Manejo de errores del arranque ---
// Muestra un aviso claro encima de la cámara y oculta el chip de estado.
function mostrarFallo(texto) {
  estado.classList.add("oculto");
  fallo.textContent = texto;
  fallo.classList.remove("oculto");
}

// Traduce el error de la cámara a un mensaje que la persona pueda entender y resolver.
function mensajeCamara(e) {
  const nombre = (e && e.name) || "";
  if (nombre === "NotAllowedError" || nombre === "SecurityError" || nombre === "PermissionDeniedError")
    return "Has bloqueado el acceso a la cámara. Actívalo en el icono de la barra de direcciones y recarga la página.";
  if (nombre === "NotFoundError" || nombre === "DevicesNotFoundError" || nombre === "OverconstrainedError")
    return "No encuentro ninguna cámara. Conecta una y recarga la página.";
  if (nombre === "NotReadableError" || nombre === "TrackStartError")
    return "La cámara está siendo usada por otra aplicación. Ciérrala y recarga la página.";
  return "No he podido iniciar la cámara. Revisa los permisos y recarga la página.";
}

// --- Arranque ---
async function iniciar() {
  // 1) Cargar los modelos. Si falla, suele ser el navegador.
  estado.textContent = "Cargando el modelo…";
  try {
    vocab = await cargarModelo();
    letras = await cargarAbecedario();
  } catch (e) {
    console.error(e);
    mostrarFallo("No he podido cargar el modelo en este navegador. Prueba con Chrome o Edge actualizados.");
    return;
  }

  vocab.forEach((c, i) => { const o = document.createElement("option"); o.value = i; o.textContent = c.es; selector.appendChild(o); });
  letras.forEach((l) => { const o = document.createElement("option"); o.value = l; o.textContent = l; selectorLetra.appendChild(o); });
  cargarReferencia(); cargarRefLetra();

  // 2) Pedir la cámara. Aquí cada fallo tiene una causa distinta.
  estado.textContent = "Pidiendo acceso a la cámara…";
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    mostrarFallo("Tu navegador no permite usar la cámara. Prueba con Chrome o Edge actualizados.");
    return;
  }
  try {
    await camara.start();
  } catch (e) {
    console.error(e);
    mostrarFallo(mensajeCamara(e));
    return;
  }

  estado.textContent = "Listo.";
  botonAprender.disabled = false; botonComunicar.disabled = false;
}

iniciar().catch((e) => { console.error(e); mostrarFallo("Algo no ha ido bien al iniciar. Recarga la página."); });
