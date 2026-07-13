"""
Extrae los puntos de los videos de la lengua de signos argentina (LSA64).

Pasa cada video por MediaPipe Holistic, con el mismo volteo en espejo que se uso con los
datos españoles, y lo convierte a nuestro formato de 61 puntos. Luego normaliza y ajusta a
56 fotogramas.

Para que sea rapido, reparte los videos entre varios nucleos del procesador a la vez.

Los nombres de archivo tienen la forma signo_persona_repeticion. Se separa por persona: las
personas 1 a 8 para entrenar y 9 a 10 para validar.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from convertir_keypoints import INDICES_POSE
from preparar_datos import ajustar_duracion, normalizar

CARPETA_VIDEOS = Path("data/raw/lsa64/all")
CARPETA_SALIDA = Path("data/processed")
NUCLEOS = 8

_holistic = None


def _iniciar_worker():
    """Cada proceso crea su propia instancia de MediaPipe una sola vez."""
    global _holistic
    import mediapipe as mp
    _holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False, model_complexity=1,
        min_detection_confidence=0.5, min_tracking_confidence=0.5,
    )


def _procesar(ruta_str):
    """Procesa un video y devuelve (grupo, clase, secuencia lista) o None."""
    ruta = Path(ruta_str)
    signo, persona, _ = ruta.stem.split("_")
    clase = int(signo) - 1
    grupo = "val" if int(persona) >= 9 else "train"

    captura = cv2.VideoCapture(ruta_str)
    frames = []
    while True:
        ok, imagen = captura.read()
        if not ok:
            break
        imagen = cv2.flip(imagen, 1)
        resultados = _holistic.process(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))
        frame = np.zeros((61, 3), dtype=np.float32)
        if resultados.pose_landmarks:
            for posicion, indice in enumerate(INDICES_POSE):
                lm = resultados.pose_landmarks.landmark[indice]
                frame[posicion] = [lm.x, lm.y, lm.z]
            if resultados.left_hand_landmarks:
                for i in range(21):
                    lm = resultados.left_hand_landmarks.landmark[i]
                    frame[19 + i] = [lm.x, lm.y, lm.z]
            if resultados.right_hand_landmarks:
                for i in range(21):
                    lm = resultados.right_hand_landmarks.landmark[i]
                    frame[40 + i] = [lm.x, lm.y, lm.z]
        frames.append(frame)
    captura.release()

    secuencia = np.array(frames, dtype=np.float32)
    if secuencia.shape[0] < 3:
        return None
    return grupo, clase, ajustar_duracion(normalizar(secuencia)).astype(np.float32)


def main():
    videos = [str(p) for p in sorted(CARPETA_VIDEOS.glob("*.mp4"))]
    print(f"Videos a procesar: {len(videos)} con {NUCLEOS} núcleos", flush=True)

    datos = {"train": ([], []), "val": ([], [])}
    hechos = 0
    with ProcessPoolExecutor(max_workers=NUCLEOS, initializer=_iniciar_worker) as ejecutor:
        for resultado in ejecutor.map(_procesar, videos, chunksize=8):
            hechos += 1
            if resultado is not None:
                grupo, clase, secuencia = resultado
                datos[grupo][0].append(secuencia)
                datos[grupo][1].append(clase)
            if hechos % 400 == 0:
                print(f"  {hechos}/{len(videos)} procesados", flush=True)

    for grupo, (X, y) in datos.items():
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64)
        np.save(CARPETA_SALIDA / f"X_lsa_{grupo}.npy", X)
        np.save(CARPETA_SALIDA / f"y_lsa_{grupo}.npy", y)
        print(f"{grupo}: {X.shape[0]} grabaciones, {len(set(y.tolist()))} signos", flush=True)


if __name__ == "__main__":
    main()
