"""
Prepara los datos para el preentrenamiento: los 300 signos completos.

A diferencia de preparar_datos.py, que se queda solo con el vocabulario de trabajo, aqui
usamos las 8000 grabaciones y sus 300 signos. La idea es que el modelo aprenda primero, con
muchos mas datos, como es el movimiento de la Lengua de Signos Española en general. Luego,
en otro paso, se afinara con nuestros 86 conceptos.

La respuesta de cada grabacion es su numero de signo original, del 0 al 299.
"""

from pathlib import Path

import numpy as np

from preparar_datos import CARPETA_ANNS, CARPETA_KPS, CARPETA_SALIDA, ajustar_duracion, normalizar


def preparar_grupo(nombre_archivo):
    secuencias = []
    respuestas = []
    for linea in (CARPETA_ANNS / nombre_archivo).read_text().strip().splitlines():
        identificador, numero_signo = linea.split(",")
        grabacion = np.load(CARPETA_KPS / f"{identificador}.npy")
        grabacion = ajustar_duracion(normalizar(grabacion))
        secuencias.append(grabacion)
        respuestas.append(int(numero_signo))
    return np.array(secuencias, dtype=np.float32), np.array(respuestas, dtype=np.int64)


def main():
    # Para preentrenar usamos el grupo de entrenamiento y el de validacion oficiales.
    for grupo, archivo in [("pre_train", "train_labels.csv"), ("pre_val", "val_labels.csv")]:
        X, y = preparar_grupo(archivo)
        np.save(CARPETA_SALIDA / f"X_{grupo}.npy", X)
        np.save(CARPETA_SALIDA / f"y_{grupo}.npy", y)
        print(f"{grupo}: {X.shape[0]} grabaciones, {len(set(y.tolist()))} signos distintos")


if __name__ == "__main__":
    main()
