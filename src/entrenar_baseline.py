"""
Entrena el primer modelo de referencia, el baseline.

Es un modelo sencillo a proposito. Su objetivo no es ser el mejor, sino dar una nota de
partida con la que comparar los modelos que vengan despues, y comprobar que todo el proceso
funciona de principio a fin.

El modelo lee cada grabacion como una secuencia de 56 fotogramas. En cada fotograma hay 61
puntos con 2 coordenadas, o sea 122 numeros. Una red del tipo GRU recorre la secuencia y al
final decide cual de los 53 signos es.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # reduce los mensajes de aviso de TensorFlow

from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

CARPETA_DATOS = Path("data/processed")
CARPETA_MODELOS = Path("models")
NUM_SIGNOS = 53
SEMILLA = 42


def cargar(grupo):
    """Carga las secuencias y las respuestas de un grupo, aplanando cada fotograma."""
    X = np.load(CARPETA_DATOS / f"X_{grupo}.npy")  # forma (n, 56, 61, 2)
    y = np.load(CARPETA_DATOS / f"y_{grupo}.npy")
    # Unimos los 61 puntos y sus 2 coordenadas en un solo vector de 122 por fotograma.
    n, fotogramas, puntos, coords = X.shape
    X = X.reshape(n, fotogramas, puntos * coords)
    return X, y


def construir_modelo(num_pasos, num_rasgos):
    """Define el modelo sencillo de referencia."""
    modelo = keras.Sequential([
        keras.Input(shape=(num_pasos, num_rasgos)),
        # Ignora los fotogramas de relleno, que son todo ceros.
        layers.Masking(mask_value=0.0),
        # Red para secuencias que resume el movimiento.
        layers.GRU(64),
        # Evita que el modelo memorice en exceso.
        layers.Dropout(0.3),
        # Capa final: una probabilidad por cada uno de los 53 signos.
        layers.Dense(NUM_SIGNOS, activation="softmax"),
    ])
    modelo.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return modelo


def main():
    keras.utils.set_random_seed(SEMILLA)
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    X_train, y_train = cargar("train")
    X_val, y_val = cargar("val")
    X_test, y_test = cargar("test")
    print(f"Entrenamiento: {X_train.shape[0]} grabaciones")
    print(f"Validacion: {X_val.shape[0]} grabaciones")
    print(f"Prueba: {X_test.shape[0]} grabaciones")
    print()

    modelo = construir_modelo(X_train.shape[1], X_train.shape[2])

    # Paramos si la validacion deja de mejorar, y recuperamos el mejor momento.
    parada = keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=15, restore_best_weights=True
    )

    modelo.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=32,
        callbacks=[parada],
        verbose=2,
    )

    print()
    perdida_test, acierto_test = modelo.evaluate(X_test, y_test, verbose=0)
    acierto_azar = 100 / NUM_SIGNOS
    print("=== Resultado del modelo de referencia ===")
    print(f"Acierto en la prueba: {acierto_test*100:.1f}%")
    print(f"(Acertar al azar daria alrededor de {acierto_azar:.1f}%)")

    modelo.save(CARPETA_MODELOS / "baseline.keras")
    print(f"Modelo guardado en {CARPETA_MODELOS / 'baseline.keras'}")


if __name__ == "__main__":
    main()
