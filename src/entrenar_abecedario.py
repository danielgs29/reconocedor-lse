"""
Entrena el reconocedor del abecedario y lo exporta al navegador.

Recibe los puntos de la mano ya normalizados y aprende a distinguir las letras. Como es una
sola mano estatica, el modelo es pequeno y sencillo: unas pocas capas. Al final lo guarda y
lo convierte a .tflite con tamano fijo, para LiteRT.js.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

SEMILLA = 42
CARPETA_DATOS = Path("data/processed")


def main():
    keras.utils.set_random_seed(SEMILLA)
    X = np.load(CARPETA_DATOS / "X_abc.npy")
    y = np.load(CARPETA_DATOS / "y_abc.npy")
    num_letras = int(y.max()) + 1
    num_rasgos = X.shape[1]

    # Mezcla y separacion en entrenamiento y prueba.
    orden = np.random.default_rng(SEMILLA).permutation(len(X))
    X, y = X[orden], y[orden]
    corte = int(0.85 * len(X))
    X_train, y_train = X[:corte], y[:corte]
    X_test, y_test = X[corte:], y[corte:]
    print(f"{len(X)} ejemplos, {num_letras} letras, {num_rasgos} rasgos por mano")

    modelo = keras.Sequential([
        keras.Input(shape=(num_rasgos,)),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(64, activation="relu"),
        layers.Dense(num_letras, activation="softmax"),
    ])
    modelo.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    parada = keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=15, restore_best_weights=True)
    modelo.fit(X_train, y_train, validation_split=0.15, epochs=100, batch_size=64, callbacks=[parada], verbose=2)

    _, acierto = modelo.evaluate(X_test, y_test, verbose=0)
    print(f"Acierto en la prueba: {acierto*100:.1f}%")

    Path("models").mkdir(exist_ok=True)
    modelo.save("models/abecedario.keras")

    # Exportar a .tflite con tamano fijo de una mano.
    entrada = tf.keras.Input(batch_shape=(1, num_rasgos))
    fijo = tf.keras.Model(entrada, modelo(entrada))
    tflite = tf.lite.TFLiteConverter.from_keras_model(fijo).convert()
    Path("web/abecedario.tflite").write_bytes(tflite)
    print(f"Exportado a web/abecedario.tflite ({len(tflite)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
