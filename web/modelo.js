// Carga el modelo con LiteRT.js y ejecuta el reconocimiento en el navegador.
// Usamos la creacion de tensores y la ejecucion del propio motor, sin utilidades externas,
// para evitar conflictos entre versiones de paquetes distintos.

import { loadLiteRt, loadAndCompile, Tensor } from "https://cdn.jsdelivr.net/npm/@litertjs/core/+esm";

// Valores de la calibracion, calculados en Python y guardados en calibracion.json.
const TEMPERATURA = 1.7;
export const UMBRAL = 0.5;

let modelo = null;
let nombres = [];

// Carga el motor, el modelo y la lista de nombres de los signos.
export async function cargarModelo() {
  await loadLiteRt("https://cdn.jsdelivr.net/npm/@litertjs/core/wasm/");

  try {
    // Primero intentamos con la tarjeta grafica, que es mas rapida.
    modelo = await loadAndCompile("modelo.tflite", { accelerator: "webgpu" });
  } catch (error) {
    // Si no hay tarjeta grafica disponible, usamos el procesador.
    console.warn("WebGPU no disponible, se usa el procesador.", error);
    modelo = await loadAndCompile("modelo.tflite", { accelerator: "wasm" });
  }

  nombres = await (await fetch("vocabulario.json")).json();
  return nombres;
}

// Recibe la entrada preparada y devuelve el signo mas probable y su confianza.
export async function predecir(entrada) {
  const tensor = Tensor.fromTypedArray(entrada, [1, 56, 366]);
  const salidas = await modelo.run([tensor]);
  const probabilidades = await salidas[0].data();

  tensor.delete();
  salidas[0].delete();

  // Aplicamos la temperatura de la calibracion para que la confianza sea sincera.
  const escalados = Array.from(probabilidades).map((p) => Math.log(p + 1e-12) / TEMPERATURA);
  const maximo = Math.max(...escalados);
  const exponenciales = escalados.map((v) => Math.exp(v - maximo));
  const suma = exponenciales.reduce((a, b) => a + b, 0);
  const calibradas = exponenciales.map((v) => v / suma);

  let mejor = 0;
  for (let i = 1; i < calibradas.length; i++) {
    if (calibradas[i] > calibradas[mejor]) mejor = i;
  }
  return { indice: mejor, nombre: nombres[mejor], confianza: calibradas[mejor] };
}
