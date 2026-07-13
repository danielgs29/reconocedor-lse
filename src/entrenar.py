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

import aumento
import caracteristicas
import modelos

SEMILLA = 42
CARPETA_DATOS = Path("data/processed")
CARPETA_MODELOS = Path("models")
EXPERIMENTO = "reconocedor-lse"


def cargar(grupo):
    """Carga las secuencias y respuestas de un grupo, sin preparar todavia."""
    X = np.load(CARPETA_DATOS / f"X_{grupo}.npy")  # (n, 56, 61, 3)
    y = np.load(CARPETA_DATOS / f"y_{grupo}.npy")
    return X, y


def crear_modelo(tipo, num_pasos, num_rasgos, num_signos, dimension=64, bloques=2):
    """Crea el modelo elegido: gru o transformer."""
    if tipo == "gru":
        return modelos.construir_gru(num_pasos, num_rasgos, num_signos)
    if tipo == "transformer":
        return modelos.construir_transformer(num_pasos, num_rasgos, num_signos, dimension=dimension, bloques=bloques)
    raise ValueError(f"Modelo desconocido: {tipo}")


def transferir_pesos(modelo, ruta_preentrenado):
    """
    Copia al modelo lo aprendido por un modelo preentrenado, capa por capa. Se copian todas
    las capas cuyo tamano coincide, y se deja sin tocar la capa final, que cambia de tamano
    al pasar de 300 signos a los conceptos de nuestro vocabulario.
    """
    preentrenado = keras.models.load_model(ruta_preentrenado)
    copiadas = 0
    for capa_nueva, capa_previa in zip(modelo.layers, preentrenado.layers):
        pesos_nuevos = capa_nueva.get_weights()
        pesos_previos = capa_previa.get_weights()
        if pesos_previos and len(pesos_nuevos) == len(pesos_previos) and all(
            a.shape == b.shape for a, b in zip(pesos_nuevos, pesos_previos)
        ):
            capa_nueva.set_weights(pesos_previos)
            copiadas += 1
    print(f"Capas transferidas desde el modelo preentrenado: {copiadas}")


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--nombre", required=True, help="nombre de la ejecucion")
    analizador.add_argument("--modelo", default="gru", choices=["gru", "transformer"], help="tipo de modelo")
    analizador.add_argument("--aumento", type=int, default=0, help="copias variadas por grabacion")
    analizador.add_argument("--preentrenado", default=None, help="ruta a un modelo preentrenado del que partir")
    analizador.add_argument("--dimension", type=int, default=64, help="tamano interno del transformer")
    analizador.add_argument("--bloques", type=int, default=2, help="numero de bloques de atencion")
    args = analizador.parse_args()

    keras.utils.set_random_seed(SEMILLA)
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    X_train, y_train = cargar("train")
    if args.aumento > 0:
        X_train, y_train = aumento.ampliar_entrenamiento(X_train, y_train, args.aumento, semilla=SEMILLA)
    X_val, y_val = cargar("val")
    X_test, y_test = cargar("test")

    # Preparamos la entrada del modelo (anade movimiento y aplana) despues del aumento.
    X_train = caracteristicas.a_entrada_modelo(X_train)
    X_val = caracteristicas.a_entrada_modelo(X_val)
    X_test = caracteristicas.a_entrada_modelo(X_test)
    print(f"Entrenamiento: {X_train.shape[0]} grabaciones (aumento: {args.aumento} copias)")
    print(f"Numeros por fotograma: {X_train.shape[2]}")

    mlflow.set_experiment(EXPERIMENTO)
    with mlflow.start_run(run_name=args.nombre):
        mlflow.log_params({
            "modelo": args.modelo,
            "copias_aumento": args.aumento,
            "tamano_lote": 32,
            "dropout": 0.3,
            "preentrenado": bool(args.preentrenado),
            "dimension": args.dimension,
            "bloques": args.bloques,
        })

        num_signos = int(y_train.max()) + 1
        modelo = crear_modelo(args.modelo, X_train.shape[1], X_train.shape[2], num_signos, args.dimension, args.bloques)
        if args.preentrenado:
            transferir_pesos(modelo, args.preentrenado)
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
