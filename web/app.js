// Aplicacion completa: abre la camara, saca los puntos con MediaPipe, y al pulsar el boton
// graba un signo durante unos segundos y lo reconoce con el modelo.

import { extraerFrame, prepararEntrada } from "./preprocesado.js";
import { cargarModelo, predecir, UMBRAL } from "./modelo.js";

const video = document.getElementById("video");
const lienzo = document.getElementById("lienzo");
const contexto = lienzo.getContext("2d");
const estado = document.getElementById("estado");
const boton = document.getElementById("grabar");
const resultado = document.getElementById("resultado");
const selector = document.getElementById("selector");
const referencia = document.getElementById("referencia");

const DURACION_GRABACION_MS = 2500;

// Lienzo oculto donde volteamos la imagen en espejo antes de analizarla, para que los
// puntos coincidan con el entrenamiento, que tambien volteaba la imagen.
const espejo = document.createElement("canvas");
const contextoEspejo = espejo.getContext("2d");

let grabando = false;
let bufferFrames = [];
let ultimoResultado = null;

const holistic = new Holistic({
  locateFile: (archivo) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${archivo}`,
});
holistic.setOptions({
  modelComplexity: 1,
  smoothLandmarks: true,
  refineFaceLandmarks: false,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5,
});

holistic.onResults((resultados) => {
  ultimoResultado = resultados;

  if (lienzo.width !== resultados.image.width) {
    lienzo.width = resultados.image.width;
    lienzo.height = resultados.image.height;
  }

  contexto.clearRect(0, 0, lienzo.width, lienzo.height);
  // La imagen que analiza MediaPipe ya viene volteada, asi que la dibujamos tal cual.
  contexto.drawImage(resultados.image, 0, 0, lienzo.width, lienzo.height);

  if (resultados.poseLandmarks) {
    drawConnectors(contexto, resultados.poseLandmarks, POSE_CONNECTIONS, { color: "#5b8def", lineWidth: 3 });
    drawLandmarks(contexto, resultados.poseLandmarks, { color: "#a8c7ff", lineWidth: 1, radius: 2 });
  }
  for (const mano of [resultados.leftHandLandmarks, resultados.rightHandLandmarks]) {
    if (mano) {
      drawConnectors(contexto, mano, HAND_CONNECTIONS, { color: "#38b774", lineWidth: 3 });
      drawLandmarks(contexto, mano, { color: "#7ee0a8", lineWidth: 1, radius: 2 });
    }
  }

  // Si estamos grabando, guardamos el fotograma.
  if (grabando) {
    bufferFrames.push(extraerFrame(resultados));
  }
});

// Voltea el fotograma del video en un lienzo oculto y se lo pasa a MediaPipe.
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

const camara = new Camera(video, {
  onFrame: enviarFrameVolteado,
  width: 640,
  height: 480,
});

async function grabarSigno() {
  boton.disabled = true;
  resultado.textContent = "";
  bufferFrames = [];
  grabando = true;

  // Cuenta atras sencilla mientras se graba.
  let restante = Math.round(DURACION_GRABACION_MS / 1000);
  estado.textContent = `Grabando… haz el signo (${restante})`;
  const cuenta = setInterval(() => {
    restante -= 1;
    if (restante > 0) estado.textContent = `Grabando… haz el signo (${restante})`;
  }, 1000);

  await new Promise((r) => setTimeout(r, DURACION_GRABACION_MS));
  clearInterval(cuenta);
  grabando = false;

  estado.textContent = "Reconociendo…";
  if (bufferFrames.length < 3) {
    resultado.textContent = "No se detectaron manos";
    estado.textContent = "Inténtalo de nuevo, con las manos bien visibles.";
    boton.disabled = false;
    return;
  }

  const entrada = prepararEntrada(bufferFrames);
  const prediccion = await predecir(entrada);

  const objetivo = parseInt(selector.value, 10);
  const objetivoNombre = selector.options[selector.selectedIndex].textContent;
  const porcentaje = Math.round(prediccion.confianza * 100);

  if (prediccion.confianza < UMBRAL) {
    resultado.textContent = `No lo tengo claro (${porcentaje}%)`;
    resultado.style.color = "#9aa0a6";
  } else if (prediccion.indice === objetivo) {
    resultado.textContent = `Correcto: ${prediccion.nombre} (${porcentaje}%)`;
    resultado.style.color = "#38b774";
  } else {
    resultado.textContent = `Has hecho ${prediccion.nombre}; el objetivo era ${objetivoNombre}`;
    resultado.style.color = "#e0a13a";
  }
  estado.textContent = "Elige otro signo o vuelve a intentarlo.";
  boton.disabled = false;
}

boton.addEventListener("click", grabarSigno);

// Muestra el video de demostracion del signo elegido en el selector.
function cargarReferencia() {
  referencia.src = `referencias/${selector.value}.mp4`;
  referencia.play().catch(() => {});
}

// Arranque: primero el modelo del todo, y solo despues la cámara. Cargar las dos librerías
// a la vez hace que se pisen una variable interna común, así que las separamos.
async function iniciar() {
  estado.textContent = "Cargando el modelo…";
  const nombres = await cargarModelo();

  // Rellena el selector con los 64 signos y muestra el primero.
  nombres.forEach((nombre, indice) => {
    const opcion = document.createElement("option");
    opcion.value = indice;
    opcion.textContent = nombre;
    selector.appendChild(opcion);
  });
  selector.addEventListener("change", cargarReferencia);
  cargarReferencia();

  estado.textContent = "Pidiendo acceso a la cámara…";
  await camara.start();
  estado.textContent = "Listo. Elige un signo, imítalo y pulsa 'Grabar signo'.";
  boton.disabled = false;
}

iniciar().catch((error) => {
  estado.textContent = "Algo falló al iniciar. Revisa la consola.";
  console.error(error);
});
