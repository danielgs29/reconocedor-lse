// Aplicación con dos modos (Aprender / Comunicar), y dentro de cada uno dos submodos:
// Signos (dinámicos) y Abecedario (letras estáticas de la mano).

import { extraerFrame, prepararEntrada, manoAEntrada } from "./preprocesado.js";
import { cargarModelo, predecir, cargarAbecedario, predecirLetra, UMBRAL } from "./modelo.js";

const UMBRAL_LETRA = 0.7;
const DURACION_GRABACION_MS = 2500;

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
// Comunicar
const subComSignos = $("sub-com-signos"), subComAbc = $("sub-com-abc");
const comSignos = $("com-signos"), comAbc = $("com-abc");
const selectorIdioma = $("idioma"), botonComunicar = $("grabar-comunicar"), botonBorrar = $("borrar"), mensaje = $("mensaje");
const letraVivaCom = $("letra-viva-com"), mensajeAbc = $("mensaje-abc");
const botonAnadir = $("anadir-letra"), botonEspacio = $("espacio"), botonBorrarAbc = $("borrar-abc");

let vocab = [], letras = [];
let idioma = "es";
let modoActual = "aprender";
let submodoApr = "signos", submodoCom = "signos";
let grabando = false, bufferFrames = [];
let fraseComunicar = [], fraseAbc = [];
let letraActual = null, reconociendoLetra = false;

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
async function reconocerLetraEnVivo(r) {
  if (reconociendoLetra) return;
  const mano = r.leftHandLandmarks || r.rightHandLandmarks;
  const destino = modoActual === "aprender" ? letraVivaApr : letraVivaCom;
  if (!mano) { letraActual = null; destino.textContent = "–"; return; }
  reconociendoLetra = true;
  try {
    const { letra, confianza } = await predecirLetra(manoAEntrada(mano));
    if (confianza >= UMBRAL_LETRA) {
      letraActual = letra;
      destino.textContent = letra;
      if (modoActual === "aprender" && submodoApr === "abecedario") {
        const acierto = letra === selectorLetra.value;
        resultadoLetra.textContent = acierto ? "¡Correcto!" : "";
        resultadoLetra.style.color = "var(--good)";
      }
    } else {
      letraActual = null;
      destino.textContent = "…";
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
}
function activarSubAprender(sub) {
  submodoApr = sub;
  subAprSignos.classList.toggle("activa", sub === "signos");
  subAprAbc.classList.toggle("activa", sub === "abecedario");
  aprSignos.classList.toggle("oculto", sub !== "signos");
  aprAbc.classList.toggle("oculto", sub !== "abecedario");
}
function activarSubComunicar(sub) {
  submodoCom = sub;
  subComSignos.classList.toggle("activa", sub === "signos");
  subComAbc.classList.toggle("activa", sub === "abecedario");
  comSignos.classList.toggle("oculto", sub !== "signos");
  comAbc.classList.toggle("oculto", sub !== "abecedario");
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

// --- Arranque ---
async function iniciar() {
  estado.textContent = "Cargando el modelo…";
  vocab = await cargarModelo();
  letras = await cargarAbecedario();

  vocab.forEach((c, i) => { const o = document.createElement("option"); o.value = i; o.textContent = c.es; selector.appendChild(o); });
  letras.forEach((l) => { const o = document.createElement("option"); o.value = l; o.textContent = l; selectorLetra.appendChild(o); });
  cargarReferencia(); cargarRefLetra();

  estado.textContent = "Pidiendo acceso a la cámara…";
  await camara.start();
  estado.textContent = "Listo.";
  botonAprender.disabled = false; botonComunicar.disabled = false;
}

iniciar().catch((e) => { estado.textContent = "Algo falló al iniciar. Revisa la consola."; console.error(e); });
