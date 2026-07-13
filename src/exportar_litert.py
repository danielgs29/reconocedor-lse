"""
Exporta el modelo definitivo al formato que usa el navegador, .tflite.

Convierte el modelo de Keras a un archivo .tflite, que es el que ejecuta LiteRT.js en el
navegador. La conversion va incluida en TensorFlow, sin instalar nada mas. Al final se
comprueba que el modelo convertido da las mismas predicciones que el original.

El resultado se guarda en web/modelo.tflite.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path

import numpy as np
import tensorflow as tf

import caracteristicas

RUTA_MODELO = "models/transformer_64conceptos.keras"
RUTA_SALIDA = Path("web/modelo.tflite")


def convertir(modelo):
    """
    Convierte el modelo a .tflite con un tamano de entrada fijo de una grabacion.

    Fijar el tamano es necesario porque LiteRT en el navegador no admite tamanos dinamicos.
    Para ello envolvemos el modelo en una funcion con una forma de entrada concreta.
    """
    # Reconstruimos el modelo con el tamano de entrada fijo a una grabacion, reutilizando
    # las mismas capas y pesos ya entrenados.
    _, pasos, rasgos = modelo.input_shape
    entrada = tf.keras.Input(batch_shape=(1, pasos, rasgos))
    modelo_fijo = tf.keras.Model(entrada, modelo(entrada))

    try:
        conversor = tf.lite.TFLiteConverter.from_keras_model(modelo_fijo)
        return conversor.convert(), "operaciones nativas de LiteRT, tamaño fijo"
    except Exception:
        conversor = tf.lite.TFLiteConverter.from_keras_model(modelo_fijo)
        conversor.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
            tf.lite.OpsSet.SELECT_TF_OPS,
        ]
        return conversor.convert(), "operaciones nativas + extra de TensorFlow, tamaño fijo"


def comprobar(ruta_tflite):
    """Comprueba que el modelo convertido coincide con el original en el grupo de prueba."""
    X = caracteristicas.a_entrada_modelo(np.load("data/processed/X_test.npy")).astype(np.float32)
    original = tf.keras.models.load_model(RUTA_MODELO).predict(X, verbose=0).argmax(axis=1)

    interprete = tf.lite.Interpreter(model_path=str(ruta_tflite))
    interprete.allocate_tensors()
    entrada = interprete.get_input_details()[0]["index"]
    salida = interprete.get_output_details()[0]["index"]

    convertido = []
    for i in range(len(X)):
        interprete.set_tensor(entrada, X[i:i + 1])
        interprete.invoke()
        convertido.append(interprete.get_tensor(salida).argmax())
    return float((original == np.array(convertido)).mean())


def main():
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    modelo = tf.keras.models.load_model(RUTA_MODELO)

    tflite, modo = convertir(modelo)
    RUTA_SALIDA.write_bytes(tflite)
    print(f"Modelo convertido ({modo}), {len(tflite) / 1024:.0f} KB, guardado en {RUTA_SALIDA}")

    coincidencia = comprobar(RUTA_SALIDA)
    print(f"Coincidencia con el modelo original: {coincidencia * 100:.1f}%")
    if coincidencia < 0.99:
        print("AVISO: hay diferencias entre el original y el convertido.")


if __name__ == "__main__":
    main()
