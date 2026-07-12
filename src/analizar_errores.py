"""
Analiza en que signos se equivoca el modelo.

Calcula la matriz de confusion, que muestra que predijo el modelo para cada signo real,
identifica los pares de signos que mas se confunden entre si, y senala los signos que peor
reconoce.

Para tener suficientes ejemplos, el analisis se hace juntando los grupos de validacion y
prueba. Es un diagnostico para saber donde falla el modelo; la nota oficial sigue siendo la
del grupo de prueba.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
from tensorflow import keras

NUM_SIGNOS = 53
RUTA_MODELO = "models/transformer_aumento3.keras"
RUTA_GRAFICO = "/Users/daniel/Documents/GitHub/master/diario-proyecto-lse/matriz-confusion.png"


def cargar_nombres():
    vocab = json.loads(Path("vocabulario.json").read_text())
    nombres = [""] * NUM_SIGNOS
    for v in vocab:
        nombres[v["indice_modelo"]] = v["nombre"]
    return nombres


def cargar_grupo(grupo):
    X = np.load(f"data/processed/X_{grupo}.npy")
    y = np.load(f"data/processed/y_{grupo}.npy")
    return X.reshape(X.shape[0], 56, 122), y


def main():
    nombres = cargar_nombres()

    Xv, yv = cargar_grupo("val")
    Xt, yt = cargar_grupo("test")
    X = np.concatenate([Xv, Xt])
    y = np.concatenate([yv, yt])
    print(f"Grabaciones analizadas: {len(y)} (validacion + prueba)")

    modelo = keras.models.load_model(RUTA_MODELO)
    predicho = modelo.predict(X, verbose=0).argmax(axis=1)

    aciertos = int((predicho == y).sum())
    print(f"Acierto en este conjunto de diagnostico: {100*aciertos/len(y):.1f}%")
    print()

    cm = confusion_matrix(y, predicho, labels=range(NUM_SIGNOS))
    ejemplos_por_signo = cm.sum(axis=1)
    acierto_por_signo = np.divide(cm.diagonal(), ejemplos_por_signo, where=ejemplos_por_signo > 0)

    # Signos que peor se reconocen (con al menos un ejemplo)
    print("=== 10 signos que peor se reconocen ===")
    orden = np.argsort(acierto_por_signo)
    mostrados = 0
    for i in orden:
        if ejemplos_por_signo[i] == 0:
            continue
        print(f"  {acierto_por_signo[i]*100:4.0f}% de acierto  -  {nombres[i]:18s} ({ejemplos_por_signo[i]} ejemplos)")
        mostrados += 1
        if mostrados == 10:
            break

    # Pares de signos que mas se confunden
    print()
    print("=== Pares de signos que mas se confunden ===")
    pares = []
    for real in range(NUM_SIGNOS):
        for pred in range(NUM_SIGNOS):
            if real != pred and cm[real, pred] > 0:
                pares.append((cm[real, pred], nombres[real], nombres[pred]))
    pares.sort(reverse=True)
    for veces, real, pred in pares[:12]:
        print(f"  {veces} veces: signo real {real!r} confundido con {pred!r}")

    # Grafico de la matriz de confusion
    plt.figure(figsize=(12, 10))
    plt.imshow(cm, cmap="Blues")
    plt.colorbar(label="numero de grabaciones")
    plt.xlabel("Signo predicho por el modelo")
    plt.ylabel("Signo real")
    plt.title("Matriz de confusion (validacion + prueba)")
    plt.tight_layout()
    plt.savefig(RUTA_GRAFICO, dpi=100)
    print()
    print(f"Grafico guardado en: {RUTA_GRAFICO}")


if __name__ == "__main__":
    main()
