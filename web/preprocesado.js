// Replica en el navegador la misma preparacion de datos que se hizo en Python.
// Es la pieza mas delicada: si aqui los numeros no salen igual que en el entrenamiento,
// el modelo fallaria aunque acierte en las pruebas. Sigue paso a paso lo que hacen
// preparar_datos.py y caracteristicas.py.

// Los 19 puntos del cuerpo que usamos, de los 33 de MediaPipe (formato SIGNAMED).
export const INDICES_POSE = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24];

const NUM_PUNTOS = 61;        // 19 del cuerpo + 21 de cada mano
const DURACION = 56;          // fotogramas a los que se ajusta cada grabacion
const POS_HOMBRO_IZQ = 5;     // el hombro izquierdo cae en esta posicion de los 61 puntos
const POS_HOMBRO_DER = 6;

function frameVacio() {
  const frame = [];
  for (let i = 0; i < NUM_PUNTOS; i++) frame.push([0, 0, 0]);
  return frame;
}

function presente(punto) {
  return punto[0] !== 0 || punto[1] !== 0 || punto[2] !== 0;
}

// Convierte un resultado de MediaPipe en un fotograma de 61 puntos con x, y, z.
// Si no hay cuerpo, el fotograma entero queda a cero, igual que en Python.
export function extraerFrame(resultados) {
  const frame = frameVacio();
  const pose = resultados.poseLandmarks;
  if (!pose) return frame;

  INDICES_POSE.forEach((indice, posicion) => {
    const p = pose[indice];
    frame[posicion] = [p.x, p.y, p.z];
  });

  const izquierda = resultados.leftHandLandmarks;
  if (izquierda) for (let i = 0; i < 21; i++) frame[19 + i] = [izquierda[i].x, izquierda[i].y, izquierda[i].z];

  const derecha = resultados.rightHandLandmarks;
  if (derecha) for (let i = 0; i < 21; i++) frame[40 + i] = [derecha[i].x, derecha[i].y, derecha[i].z];

  return frame;
}

// Normaliza usando los hombros como referencia: los centra y los escala por la distancia
// entre hombros. Los puntos ausentes se quedan a cero.
function normalizar(frames) {
  let cx = 0, cy = 0, cz = 0, ancho = 0, cuenta = 0;
  for (const frame of frames) {
    const izq = frame[POS_HOMBRO_IZQ];
    const der = frame[POS_HOMBRO_DER];
    if (presente(izq) && presente(der)) {
      cx += (izq[0] + der[0]) / 2;
      cy += (izq[1] + der[1]) / 2;
      cz += (izq[2] + der[2]) / 2;
      ancho += Math.hypot(izq[0] - der[0], izq[1] - der[1]);
      cuenta += 1;
    }
  }
  if (cuenta === 0) return frames;  // sin hombros no podemos normalizar

  cx /= cuenta; cy /= cuenta; cz /= cuenta;
  ancho = Math.max(ancho / cuenta, 1e-6);

  return frames.map((frame) =>
    frame.map((p) => (presente(p) ? [(p[0] - cx) / ancho, (p[1] - cy) / ancho, (p[2] - cz) / ancho] : [0, 0, 0]))
  );
}

// Ajusta la grabacion a 56 fotogramas: recorta si sobra, rellena con vacios si falta.
function ajustarDuracion(frames) {
  if (frames.length >= DURACION) return frames.slice(0, DURACION);
  const salida = frames.slice();
  while (salida.length < DURACION) salida.push(frameVacio());
  return salida;
}

// Anade el movimiento de cada punto y aplana todo en un vector de 366 numeros por fotograma.
function construirEntrada(frames) {
  const entrada = new Float32Array(DURACION * NUM_PUNTOS * 6);
  for (let t = 0; t < DURACION; t++) {
    for (let j = 0; j < NUM_PUNTOS; j++) {
      const p = frames[t][j];
      let vx = 0, vy = 0, vz = 0;
      if (t > 0) {
        const anterior = frames[t - 1][j];
        if (presente(p) && presente(anterior)) {
          vx = p[0] - anterior[0];
          vy = p[1] - anterior[1];
          vz = p[2] - anterior[2];
        }
      }
      const base = t * NUM_PUNTOS * 6 + j * 6;
      entrada[base] = p[0]; entrada[base + 1] = p[1]; entrada[base + 2] = p[2];
      entrada[base + 3] = vx; entrada[base + 4] = vy; entrada[base + 5] = vz;
    }
  }
  return entrada;
}

// Recibe la lista de fotogramas grabados y devuelve la entrada lista para el modelo.
export function prepararEntrada(frames) {
  return construirEntrada(ajustarDuracion(normalizar(frames)));
}
