"""
Extrae los puntos del conjunto grande de lengua de signos americana (Google ISLR).

Lee directamente de dentro del zip, sin descomprimirlo, un subconjunto grande y equilibrado
de las 94.000 grabaciones. Cada grabacion es un parquet con los puntos de MediaPipe. Se
extraen nuestros 61 puntos, se aplica el mismo volteo en espejo que en los datos españoles,
se normaliza y se ajusta a 56 fotogramas.

El objetivo es tener muchos datos de otra lengua de signos para preentrenar el modelo. Se
reparte el trabajo entre varios nucleos.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import io
import json
import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from convertir_keypoints import INDICES_POSE
from preparar_datos import ajustar_duracion, normalizar

RUTA_ZIP = "data/raw/asl-signs.zip"
CARPETA_SALIDA = Path("data/processed")
MAX_POR_SIGNO = 100000  # sin tope real: usar todas las grabaciones disponibles
NUCLEOS = 8

_zip = None
_pose_pos = {li: p for p, li in enumerate(INDICES_POSE)}


def _iniciar_worker():
    global _zip
    _zip = zipfile.ZipFile(RUTA_ZIP)


def _secuencia(ruta):
    """Lee un parquet del zip y devuelve la secuencia (fotogramas, 61, 3) ya normalizada."""
    df = pd.read_parquet(io.BytesIO(_zip.read(ruta)), columns=["frame", "type", "landmark_index", "x", "y", "z"])

    # Volteo en espejo: invertir x e intercambiar mano izquierda y derecha.
    df["x"] = 1.0 - df["x"]
    df.loc[df["type"] == "left_hand", "type"] = "_tmp"
    df.loc[df["type"] == "right_hand", "type"] = "left_hand"
    df.loc[df["type"] == "_tmp", "type"] = "right_hand"

    frames = sorted(df["frame"].unique())
    posicion_frame = {f: i for i, f in enumerate(frames)}
    seq = np.zeros((len(frames), 61, 3), dtype=np.float32)

    pose = df[(df["type"] == "pose") & (df["landmark_index"].isin(_pose_pos))]
    for f, li, x, y, z in zip(pose["frame"], pose["landmark_index"], pose["x"], pose["y"], pose["z"]):
        seq[posicion_frame[f], _pose_pos[li]] = (x, y, z)

    for tipo, base in [("left_hand", 19), ("right_hand", 40)]:
        mano = df[df["type"] == tipo]
        for f, li, x, y, z in zip(mano["frame"], mano["landmark_index"], mano["x"], mano["y"], mano["z"]):
            if li < 21:
                seq[posicion_frame[f], base + int(li)] = (x, y, z)

    seq = np.nan_to_num(seq)
    if seq.shape[0] < 3:
        return None
    return ajustar_duracion(normalizar(seq)).astype(np.float32)


def _procesar(tarea):
    ruta, clase, grupo = tarea
    seq = _secuencia(ruta)
    if seq is None:
        return None
    return grupo, clase, seq


def main():
    z = zipfile.ZipFile(RUTA_ZIP)
    train = pd.read_csv(io.BytesIO(z.read("train.csv")))
    smap = json.loads(z.read("sign_to_prediction_index_map.json"))

    # Personas para validar: las dos ultimas, para que sean distintas de las de entrenar.
    personas = sorted(train["participant_id"].unique())
    personas_val = set(personas[-2:])

    # Subconjunto equilibrado: hasta MAX_POR_SIGNO por signo.
    tareas = []
    cuenta = defaultdict(int)
    for fila in train.itertuples(index=False):
        if cuenta[fila.sign] >= MAX_POR_SIGNO:
            continue
        cuenta[fila.sign] += 1
        clase = smap[fila.sign]
        grupo = "val" if fila.participant_id in personas_val else "train"
        tareas.append((fila.path, clase, grupo))

    print(f"Grabaciones a procesar: {len(tareas)} (de {len(train)}), {len(smap)} signos", flush=True)

    datos = {"train": ([], []), "val": ([], [])}
    hechos = 0
    with ProcessPoolExecutor(max_workers=NUCLEOS, initializer=_iniciar_worker) as ejecutor:
        for resultado in ejecutor.map(_procesar, tareas, chunksize=16):
            hechos += 1
            if resultado is not None:
                grupo, clase, seq = resultado
                datos[grupo][0].append(seq)
                datos[grupo][1].append(clase)
            if hechos % 2000 == 0:
                print(f"  {hechos}/{len(tareas)} procesados", flush=True)

    for grupo, (X, y) in datos.items():
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64)
        np.save(CARPETA_SALIDA / f"X_asl_{grupo}.npy", X)
        np.save(CARPETA_SALIDA / f"y_asl_{grupo}.npy", y)
        print(f"{grupo}: {X.shape[0]} grabaciones, {len(set(y.tolist()))} signos", flush=True)


if __name__ == "__main__":
    main()
