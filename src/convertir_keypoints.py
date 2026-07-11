"""
Convierte las grabaciones de SWL-LSE del formato original de MediaPipe a listas de
numeros simples.

Cada grabacion original es un archivo .pkl que guarda objetos internos de MediaPipe, lo
que obliga a tener instalada una version concreta de esa libreria para poder abrirlo. Este
programa los abre una sola vez y los reescribe como archivos .npy, que son simples matrices
de numeros. A partir de ahi ya no hace falta MediaPipe para trabajar con los datos.

Cada grabacion pasa a ser una matriz de forma (numero_de_fotogramas, 61, 4):
  - 61 puntos por fotograma: 19 del cuerpo, 21 de la mano izquierda y 21 de la derecha.
  - 4 valores por punto: las coordenadas x, y, z y la visibilidad.

Se sigue el mismo criterio que los autores del conjunto de datos, llamado SIGNAMED, para
que los resultados sean comparables con los suyos. Cuando en un fotograma falta el cuerpo o
una mano, esos valores quedan a cero.
"""

import pickle
from pathlib import Path

import numpy as np

# Indices de los 19 puntos del cuerpo que usan los autores, de los 33 que da MediaPipe.
# Corresponden a cabeza, hombros, brazos y torso alto.
INDICES_POSE = [0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

PUNTOS_POR_MANO = 21
NUM_PUNTOS = len(INDICES_POSE) + PUNTOS_POR_MANO * 2  # 61
NUM_VALORES = 4  # x, y, z, visibilidad


def _copiar_puntos(destino, base, landmarks, indices):
    """Copia las coordenadas de una lista de puntos de MediaPipe en la matriz destino."""
    for posicion, origen in enumerate(indices):
        punto = landmarks.landmark[origen]
        destino[base + posicion] = (punto.x, punto.y, punto.z, punto.visibility)


def fotograma_a_matriz(pose, mano_izquierda, mano_derecha):
    """Convierte los puntos de un fotograma en una matriz (61, 4)."""
    matriz = np.zeros((NUM_PUNTOS, NUM_VALORES), dtype=np.float32)

    # Los autores solo usan las manos cuando tambien se ha detectado el cuerpo.
    # Si no hay cuerpo, el fotograma entero queda a cero.
    if not pose:
        return matriz

    _copiar_puntos(matriz, 0, pose, INDICES_POSE)

    base_izquierda = len(INDICES_POSE)
    if mano_izquierda:
        _copiar_puntos(matriz, base_izquierda, mano_izquierda, range(PUNTOS_POR_MANO))

    base_derecha = base_izquierda + PUNTOS_POR_MANO
    if mano_derecha:
        _copiar_puntos(matriz, base_derecha, mano_derecha, range(PUNTOS_POR_MANO))

    return matriz


def convertir_grabacion(ruta_pkl):
    """Lee un archivo .pkl y devuelve una matriz (numero_de_fotogramas, 61, 4)."""
    with open(ruta_pkl, "rb") as archivo:
        fotogramas = pickle.load(archivo)

    matrices = []
    for fotograma in fotogramas:
        datos = fotograma["holistic_legacy"]
        matrices.append(
            fotograma_a_matriz(
                datos["pose_landmarks"],
                datos["left_hand_landmarks"],
                datos["right_hand_landmarks"],
            )
        )

    return np.array(matrices, dtype=np.float32)


def main():
    carpeta_entrada = Path("data/raw/mediapipe/MEDIAPIPE")
    carpeta_salida = Path("data/processed/keypoints")
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    archivos = sorted(carpeta_entrada.glob("*.pkl"))
    print(f"Encontradas {len(archivos)} grabaciones para convertir.")

    convertidas = 0
    for numero, ruta in enumerate(archivos, start=1):
        destino = carpeta_salida / f"{ruta.stem}.npy"
        if destino.exists():
            continue

        matriz = convertir_grabacion(ruta)
        np.save(destino, matriz)
        convertidas += 1

        if numero % 500 == 0:
            print(f"  {numero}/{len(archivos)} procesadas")

    print(f"Conversion terminada. {convertidas} grabaciones nuevas guardadas en {carpeta_salida}.")


if __name__ == "__main__":
    main()
