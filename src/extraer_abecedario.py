"""
Extrae los puntos de la mano de las imagenes del abecedario de LSE.

Cada imagen es una mano haciendo una letra sobre fondo blanco. Se pasa por MediaPipe, se
sacan los 21 puntos de la mano y se normalizan respecto a la muneca, para que la posicion y
el tamano de la mano en la imagen no importen.

Como una persona puede signar con la mano derecha o la izquierda, de cada mano guardamos
tambien su version reflejada, con la misma letra. Asi el reconocedor funciona con las dos.

Resultado: data/processed/X_abc.npy y y_abc.npy, y la lista de letras en web/abecedario.json.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

CARPETA = Path("data/raw/abecedario/fondo_blanco")
CARPETA_SALIDA = Path("data/processed")
NUCLEOS = 8

LETRAS = sorted([d.name for d in CARPETA.iterdir() if d.is_dir()])
LETRA_INDICE = {letra: i for i, letra in enumerate(LETRAS)}

_manos = None


def _iniciar_worker():
    global _manos
    import mediapipe as mp
    _manos = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)


def normalizar_mano(puntos):
    """Centra la mano en la muneca y la escala por el tamano de la palma."""
    centro = puntos[0].copy()          # muneca
    puntos = puntos - centro
    escala = np.linalg.norm(puntos[9, :2])   # muneca -> base del dedo corazon
    return puntos / max(escala, 1e-6)


def _procesar(tarea):
    ruta, letra = tarea
    imagen = cv2.imread(ruta)
    if imagen is None:
        return None
    imagen = cv2.flip(imagen, 1)   # mismo volteo que en la aplicacion
    resultado = _manos.process(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))
    if not resultado.multi_hand_landmarks:
        return None
    puntos = np.array([[p.x, p.y, p.z] for p in resultado.multi_hand_landmarks[0].landmark], dtype=np.float32)
    normal = normalizar_mano(puntos)
    reflejada = normal.copy()
    reflejada[:, 0] *= -1          # version para la otra mano
    return LETRA_INDICE[letra], normal.flatten(), reflejada.flatten()


def main():
    tareas = []
    for letra in LETRAS:
        for imagen in (CARPETA / letra).glob("*.JPG"):
            tareas.append((str(imagen), letra))
    print(f"Imagenes a procesar: {len(tareas)} de {len(LETRAS)} letras", flush=True)

    X, y = [], []
    hechos = 0
    with ProcessPoolExecutor(max_workers=NUCLEOS, initializer=_iniciar_worker) as ejecutor:
        for resultado in ejecutor.map(_procesar, tareas, chunksize=16):
            hechos += 1
            if resultado is not None:
                indice, normal, reflejada = resultado
                X.append(normal); y.append(indice)
                X.append(reflejada); y.append(indice)
            if hechos % 500 == 0:
                print(f"  {hechos}/{len(tareas)}", flush=True)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    np.save(CARPETA_SALIDA / "X_abc.npy", X)
    np.save(CARPETA_SALIDA / "y_abc.npy", y)
    Path("web/abecedario.json").write_text(json.dumps(LETRAS, ensure_ascii=False))
    print(f"Guardado: {X.shape[0]} ejemplos (con reflejadas), {len(LETRAS)} letras: {LETRAS}", flush=True)


if __name__ == "__main__":
    main()
