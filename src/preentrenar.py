"""
Preentrena el modelo con los 300 signos de la LSE.

Entrena un Transformer para reconocer los 300 signos completos, usando las 8000 grabaciones.
El objetivo no es este modelo en si, sino que aprenda buenas representaciones del movimiento
de la lengua de signos, que luego se reaprovecharan al afinar con nuestros 86 conceptos.

El modelo se guarda en models/preentrenado_300.keras.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import argparse
from pathlib import Path

import numpy as np
from tensorflow import keras

import caracteristicas
import modelos

SEMILLA = 42
CARPETA_DATOS = Path("data/processed")
CARPETA_MODELOS = Path("models")


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--entrada", default="pre", help="prefijo de los datos, por ejemplo pre o lsa")
    analizador.add_argument("--salida", default="preentrenado_300.keras", help="nombre del modelo resultante")
    args = analizador.parse_args()

    keras.utils.set_random_seed(SEMILLA)
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    X_train = np.load(CARPETA_DATOS / f"X_{args.entrada}_train.npy")
    y_train = np.load(CARPETA_DATOS / f"y_{args.entrada}_train.npy")
    X_val = np.load(CARPETA_DATOS / f"X_{args.entrada}_val.npy")
    y_val = np.load(CARPETA_DATOS / f"y_{args.entrada}_val.npy")

    X_train = caracteristicas.a_entrada_modelo(X_train)
    X_val = caracteristicas.a_entrada_modelo(X_val)

    num_signos = int(max(y_train.max(), y_val.max())) + 1
    print(f"Preentrenando con {X_train.shape[0]} grabaciones y {num_signos} signos")

    modelo = modelos.construir_transformer(X_train.shape[1], X_train.shape[2], num_signos)
    parada = keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=12, restore_best_weights=True)

    modelo.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100, batch_size=32, callbacks=[parada], verbose=2,
    )

    ruta = CARPETA_MODELOS / args.salida
    modelo.save(ruta)
    print(f"Modelo preentrenado guardado en {ruta}")


if __name__ == "__main__":
    main()
