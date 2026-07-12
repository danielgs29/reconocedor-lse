"""
Entrena un modelo y registra el experimento en MLflow.

Permite entrenar con o sin aumento de datos, para poder comparar. Cada ejecucion queda
anotada en MLflow con sus ajustes y sus resultados.

Uso:
    uv run python src/entrenar.py --nombre baseline --aumento 0
    uv run python src/entrenar.py --nombre gru_aumento3 --aumento 3
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import argparse
from pathlib import Path

import mlflow
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

import aumento

NUM_SIGNOS = 53
SEMILLA = 42
CARPETA_DATOS = Path("data/processed")
CARPETA_MODELOS = Path("models")
EXPERIMENTO = "reconocedor-lse"


def cargar(grupo):
    """Carga las secuencias y respuestas de un grupo, sin aplanar todavia."""
    X = np.load(CARPETA_DATOS / f"X_{grupo}.npy")  # (n, 56, 61, 2)
    y = np.load(CARPETA_DATOS / f"y_{grupo}.npy")
    return X, y


def aplanar(X):
    """Une los 61 puntos y sus 2 coordenadas en 122 numeros por fotograma."""
    n, fotogramas, puntos, coords = X.shape
    return X.reshape(n, fotogramas, puntos * coords)


def construir_modelo(num_pasos, num_rasgos):
    """Modelo de secuencia GRU, el mismo del baseline."""
    modelo = keras.Sequential([
        keras.Input(shape=(num_pasos, num_rasgos)),
        layers.Masking(mask_value=0.0),
        layers.GRU(64),
        layers.Dropout(0.3),
        layers.Dense(NUM_SIGNOS, activation="softmax"),
    ])
    modelo.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return modelo


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--nombre", required=True, help="nombre de la ejecucion")
    analizador.add_argument("--aumento", type=int, default=0, help="copias variadas por grabacion")
    args = analizador.parse_args()

    keras.utils.set_random_seed(SEMILLA)
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    X_train, y_train = cargar("train")
    if args.aumento > 0:
        X_train, y_train = aumento.ampliar_entrenamiento(X_train, y_train, args.aumento, semilla=SEMILLA)
    X_val, y_val = cargar("val")
    X_test, y_test = cargar("test")

    X_train, X_val, X_test = aplanar(X_train), aplanar(X_val), aplanar(X_test)
    print(f"Entrenamiento: {X_train.shape[0]} grabaciones (aumento: {args.aumento} copias)")

    mlflow.set_experiment(EXPERIMENTO)
    with mlflow.start_run(run_name=args.nombre):
        mlflow.log_params({
            "modelo": "gru64",
            "copias_aumento": args.aumento,
            "tamano_lote": 32,
            "dropout": 0.3,
        })

        modelo = construir_modelo(X_train.shape[1], X_train.shape[2])
        parada = keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=15, restore_best_weights=True)

        historia = modelo.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100, batch_size=32, callbacks=[parada], verbose=2,
        )

        mejor_val = max(historia.history["val_accuracy"])
        _, acierto_test = modelo.evaluate(X_test, y_test, verbose=0)

        mlflow.log_metric("mejor_val_accuracy", mejor_val)
        mlflow.log_metric("test_accuracy", acierto_test)

        ruta_modelo = CARPETA_MODELOS / f"{args.nombre}.keras"
        modelo.save(ruta_modelo)
        mlflow.log_artifact(str(ruta_modelo))

        print(f"=== {args.nombre} ===")
        print(f"Mejor acierto en validacion: {mejor_val*100:.1f}%")
        print(f"Acierto en la prueba: {acierto_test*100:.1f}%")


if __name__ == "__main__":
    main()
