// Aplicación con dos modos:
//  - Aprender: eliges un signo, lo imitas y te corrige. Todo en español.
//  - Comunicar: signas libremente y se escribe el significado, en el idioma elegido.

import { extraerFrame, prepararEntrada } from "./preprocesado.js";
import { cargarModelo, predecir, UMBRAL } from "./modelo.js";

const video = document.getElementById("video");
const lienzo = document.getElementById("lienzo");
const contexto = lienzo.getContext("2d");
const estado = document.getElementById("estado");

// Pestañas y paneles
const tabAprender = document.getElementById("tab-aprender");
const tabComunicar = document.getElementById("tab-comunicar");
const panelAprender = document.getElementById("panel-aprender");
const panelComunicar = document.getElementById("panel-comunicar");

// Modo Aprender
const selector = document.getElementById("selector");
const referencia = document.getElementById("referencia");
const botonAprender = document.getElementById("grabar-aprender");
const resultadoAprender = document.getElementById("resultado-aprender");

// Modo Comunicar
const selectorIdioma = document.getElementById("idioma");
const botonComunicar = document.getElementById("grabar-comunicar");
const botonBorrar = document.getElementById("borrar");
const mensaje = document.getElementById("mensaje");

const DURACION_GRABACION_MS = 2500;

let vocab = [];
let idioma = "es";
let grabando = false;
let bufferFrames = [];
let fraseComunicar = [];   // signos reconocidos en el modo comunicar (por índice)

// Lienzo oculto para voltear la imagen en espejo antes de analizarla,
// igual que se hizo con los datos de entrenamiento.
const espejo = document.createElement("canvas");
const contextoEspejo = espejo.getContext("2d");

function nombreSigno(indice) {
  return vocab[indice][idioma];
}

// --- MediaPipe ---
const holistic = new Holistic({
  locateFile: (archivo) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${archivo}`,
});
holistic.setOptions({
  modelComplexity: 1, smoothLandmarks: true, refineFaceLandmarks: false,
  minDetectionConfidence: 0.5, minTrackingConfidence: 0.5,
});

holistic.onResults((resultados) => {
  if (lienzo.width !== resultados.image.width) {
    lienzo.width = resultados.image.width;
    lienzo.height = resultados.image.height;
  }
  contexto.clearRect(0, 0, lienzo.width, lienzo.height);
  contexto.drawImage(resultados.image, 0, 0, lienzo.width, lienzo.height);
  if (resultados.poseLandmarks) {
    drawConnectors(contexto, resultados.poseLandmarks, POSE_CONNECTIONS, { color: "rgba(230,238,237,0.55)", lineWidth: 2 });
    drawLandmarks(contexto, resultados.poseLandmarks, { color: "rgba(230,238,237,0.75)", lineWidth: 1, radius: 2 });
  }
  for (const mano of [resultados.leftHandLandmarks, resultados.rightHandLandmarks]) {
    if (mano) {
      drawConnectors(contexto, mano, HAND_CONNECTIONS, { color: "#1cc3b8", lineWidth: 4 });
      drawLandmarks(contexto, mano, { color: "#8fe6df", lineWidth: 1, radius: 3 });
    }
  }
  if (grabando) bufferFrames.push(extraerFrame(resultados));
});

function enviarFrameVolteado() {
  if (espejo.width !== video.videoWidth && video.videoWidth) {
    espejo.width = video.videoWidth;
    espejo.height = video.videoHeight;
  }
  contextoEspejo.save();
  contextoEspejo.translate(espejo.width, 0);
  contextoEspejo.scale(-1, 1);
  contextoEspejo.drawImage(video, 0, 0, espejo.width, espejo.height);
  contextoEspejo.restore();
  return holistic.send({ image: espejo });
}

const camara = new Camera(video, { onFrame: enviarFrameVolteado, width: 640, height: 480 });

// --- Grabación de un signo (común a los dos modos) ---
async function grabarSigno() {
  botonAprender.disabled = true;
  botonComunicar.disabled = true;
  bufferFrames = [];
  grabando = true;

  let restante = Math.round(DURACION_GRABACION_MS / 1000);
  estado.textContent = `Grabando… (${restante})`;
  const cuenta = setInterval(() => {
    restante -= 1;
    if (restante > 0) estado.textContent = `Grabando… (${restante})`;
  }, 1000);

  await new Promise((r) => setTimeout(r, DURACION_GRABACION_MS));
  clearInterval(cuenta);
  grabando = false;
  estado.textContent = "Reconociendo…";

  let prediccion = null;
  if (bufferFrames.length >= 3) {
    prediccion = await predecir(prepararEntrada(bufferFrames));
  }
  estado.textContent = "Listo.";
  botonAprender.disabled = false;
  botonComunicar.disabled = false;
  return prediccion;
}

// --- Modo Aprender ---
async function practicar() {
  resultadoAprender.textContent = "";
  const prediccion = await grabarSigno();
  const objetivo = parseInt(selector.value, 10);

  if (!prediccion) {
    resultadoAprender.textContent = "No se detectaron manos";
    resultadoAprender.style.color = "#9aa0a6";
    return;
  }
  const porcentaje = Math.round(prediccion.confianza * 100);
  if (prediccion.confianza < UMBRAL) {
    resultadoAprender.textContent = `No lo tengo claro (${porcentaje}%)`;
    resultadoAprender.style.color = "#9aa0a6";
  } else if (prediccion.indice === objetivo) {
    resultadoAprender.textContent = `Correcto: ${vocab[objetivo].es} (${porcentaje}%)`;
    resultadoAprender.style.color = "#38b774";
  } else {
    resultadoAprender.textContent = `Has hecho ${vocab[prediccion.indice].es}; el objetivo era ${vocab[objetivo].es}`;
    resultadoAprender.style.color = "#e0a13a";
  }
}

function cargarReferencia() {
  referencia.src = `referencias/${selector.value}.mp4`;
  referencia.play().catch(() => {});
}

// --- Modo Comunicar ---
function renderMensaje() {
  mensaje.textContent = fraseComunicar.map(nombreSigno).join(" ");
}

async function signarComunicar() {
  const prediccion = await grabarSigno();
  if (prediccion && prediccion.confianza >= UMBRAL) {
    fraseComunicar.push(prediccion.indice);
    renderMensaje();
  } else {
    estado.textContent = idioma === "es" ? "No lo tengo claro, repite el signo." : "Not sure, sign again.";
  }
}

// --- Cambio de modo ---
function activarModo(modo) {
  const aprender = modo === "aprender";
  tabAprender.classList.toggle("activa", aprender);
  tabComunicar.classList.toggle("activa", !aprender);
  panelAprender.classList.toggle("oculto", !aprender);
  panelComunicar.classList.toggle("oculto", aprender);
}

tabAprender.addEventListener("click", () => activarModo("aprender"));
tabComunicar.addEventListener("click", () => activarModo("comunicar"));
botonAprender.addEventListener("click", practicar);
botonComunicar.addEventListener("click", signarComunicar);
botonBorrar.addEventListener("click", () => { fraseComunicar = []; renderMensaje(); });
selector.addEventListener("change", cargarReferencia);
selectorIdioma.addEventListener("change", () => { idioma = selectorIdioma.value; renderMensaje(); });

// --- Arranque ---
async function iniciar() {
  estado.textContent = "Cargando el modelo…";
  vocab = await cargarModelo();

  vocab.forEach((concepto, indice) => {
    const opcion = document.createElement("option");
    opcion.value = indice;
    opcion.textContent = concepto.es;   // en el modo aprender, siempre en español
    selector.appendChild(opcion);
  });
  cargarReferencia();

  estado.textContent = "Pidiendo acceso a la cámara…";
  await camara.start();
  estado.textContent = "Listo.";
  botonAprender.disabled = false;
  botonComunicar.disabled = false;
}

iniciar().catch((error) => {
  estado.textContent = "Algo falló al iniciar. Revisa la consola.";
  console.error(error);
});
