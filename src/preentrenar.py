"""
Preentrena el modelo con un conjunto de datos grande.

Para no agotar la memoria con conjuntos enormes, no carga todos los datos de golpe. Los deja
en disco y los va tomando por lotes, calculando el movimiento de cada lote sobre la marcha.
Asi funciona igual con 30.000 que con 94.000 grabaciones.

Uso:
    uv run python src/preentrenar.py --entrada asl --salida preentrenado_asl.keras
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import argparse
import math
from pathlib import Path

import numpy as np
from tensorflow import keras

import caracteristicas
import modelos

SEMILLA = 42
CARPETA_DATOS = Path("data/processed")
CARPETA_MODELOS = Path("models")


class Lotes(keras.utils.PyDataset):
    """Entrega los datos por lotes, tomandolos del disco y anadiendo el movimiento al vuelo."""

    def __init__(self, X, y, tamano_lote=32, **kwargs):
        super().__init__(**kwargs)
        self.X = X
        self.y = y
        self.tamano_lote = tamano_lote

    def __len__(self):
        return math.ceil(self.X.shape[0] / self.tamano_lote)

    def __getitem__(self, indice):
        inicio = indice * self.tamano_lote
        fin = inicio + self.tamano_lote
        lote = caracteristicas.a_entrada_modelo(np.asarray(self.X[inicio:fin]))
        return lote, self.y[inicio:fin]


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--entrada", default="pre", help="prefijo de los datos, por ejemplo pre o asl")
    analizador.add_argument("--salida", default="preentrenado_300.keras", help="nombre del modelo resultante")
    analizador.add_argument("--dimension", type=int, default=64, help="tamano interno del transformer")
    analizador.add_argument("--bloques", type=int, default=2, help="numero de bloques de atencion")
    args = analizador.parse_args()

    keras.utils.set_random_seed(SEMILLA)
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    # mmap_mode deja los datos en disco; solo se cargan a memoria los lotes que se usan.
    X_train = np.load(CARPETA_DATOS / f"X_{args.entrada}_train.npy", mmap_mode="r")
    y_train = np.load(CARPETA_DATOS / f"y_{args.entrada}_train.npy")
    X_val = np.load(CARPETA_DATOS / f"X_{args.entrada}_val.npy", mmap_mode="r")
    y_val = np.load(CARPETA_DATOS / f"y_{args.entrada}_val.npy")

    num_signos = int(max(y_train.max(), y_val.max())) + 1
    num_pasos = X_train.shape[1]
    num_rasgos = X_train.shape[2] * X_train.shape[3] * 2  # posicion + movimiento
    print(f"Preentrenando con {X_train.shape[0]} grabaciones y {num_signos} signos", flush=True)

    EPOCAS = 150
    entrenamiento = Lotes(X_train, y_train)
    validacion = Lotes(X_val, y_val)

    modelo = modelos.construir_transformer(num_pasos, num_rasgos, num_signos, dimension=args.dimension, bloques=args.bloques)
    modelos.compilar(modelo, pasos_por_epoca=len(entrenamiento), epocas=EPOCAS, lr_pico=1e-3)
    parada = keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=25, restore_best_weights=True)

    modelo.fit(entrenamiento, validation_data=validacion, epochs=EPOCAS, callbacks=[parada], verbose=2)

    ruta = CARPETA_MODELOS / args.salida
    modelo.save(ruta)
    print(f"Modelo preentrenado guardado en {ruta}", flush=True)


if __name__ == "__main__":
    main()
