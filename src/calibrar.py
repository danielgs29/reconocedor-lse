"""
Calibra la confianza del modelo y elige un umbral para decir "no lo tengo claro".

Hace dos cosas:

  1. Escalado por temperatura. Los modelos suelen ser demasiado confiados. Buscamos un unico
     numero, la temperatura, que ajusta la confianza para que sea sincera: que un 90 por
     ciento de confianza signifique acertar de verdad el 90 por ciento de las veces.

  2. Umbral de confianza. Analizamos que pasa si el modelo solo responde cuando su confianza
     supera cierto nivel. A mas exigencia, mas acierto en lo que responde pero responde menos
     veces. Elegimos un punto de equilibrio.

La temperatura se ajusta con el grupo de validacion. El analisis del umbral se muestra sobre
validacion y prueba juntas, para tener mas datos. Los valores elegidos se guardan en
calibracion.json para que la aplicacion los use.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from pathlib import Path

import numpy as np
from tensorflow import keras

import caracteristicas

RUTA_MODELO = "models/transformer_pre_asl.keras"
RUTA_SALIDA = "calibracion.json"


def softmax(z, temperatura=1.0):
    z = z / temperatura
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def cargar_grupo(grupo):
    X = np.load(f"data/processed/X_{grupo}.npy")
    y = np.load(f"data/processed/y_{grupo}.npy")
    return caracteristicas.a_entrada_modelo(X), y


def error_calibracion(probabilidades, y, num_cajas=10):
    """
    Calcula el error de calibracion. Agrupa las predicciones por su confianza en varias
    cajas y mide cuanto se aleja la confianza media de cada caja de su acierto real. Cuanto
    mas cerca de cero, mejor calibrado.
    """
    confianza = probabilidades.max(axis=1)
    predicho = probabilidades.argmax(axis=1)
    acierto = (predicho == y).astype(float)

    error = 0.0
    for i in range(num_cajas):
        bajo, alto = i / num_cajas, (i + 1) / num_cajas
        en_caja = (confianza > bajo) & (confianza <= alto)
        if en_caja.sum() > 0:
            peso = en_caja.mean()
            error += peso * abs(acierto[en_caja].mean() - confianza[en_caja].mean())
    return error


def main():
    modelo = keras.models.load_model(RUTA_MODELO)

    Xval, yval = cargar_grupo("val")
    Xtest, ytest = cargar_grupo("test")

    # El modelo ya aplica softmax; recuperamos algo equivalente a las puntuaciones previas
    # tomando el logaritmo de las probabilidades, que es lo que necesita el escalado.
    prob_val = modelo.predict(Xval, verbose=0)
    prob_test = modelo.predict(Xtest, verbose=0)
    logit_val = np.log(prob_val + 1e-12)
    logit_test = np.log(prob_test + 1e-12)

    # 1. Buscar la mejor temperatura probando un rango de valores y quedandonos con la que
    #    hace la confianza mas sincera en validacion.
    mejor_temp, mejor_error = 1.0, error_calibracion(prob_val, yval)
    for temp in np.linspace(0.5, 5.0, 46):
        error = error_calibracion(softmax(logit_val, temp), yval)
        if error < mejor_error:
            mejor_temp, mejor_error = temp, error

    error_antes = error_calibracion(prob_val, yval)
    error_despues = error_calibracion(softmax(logit_val, mejor_temp), yval)
    print("=== Calibracion (sobre validacion) ===")
    print(f"Temperatura elegida: {mejor_temp:.2f}")
    print(f"Error de calibracion antes: {error_antes:.3f}")
    print(f"Error de calibracion despues: {error_despues:.3f}")
    print("(mas cerca de cero es mejor)")

    # 2. Analizar el umbral sobre validacion y prueba juntas, con la confianza ya calibrada.
    logit = np.concatenate([logit_val, logit_test])
    y = np.concatenate([yval, ytest])
    prob_cal = softmax(logit, mejor_temp)
    confianza = prob_cal.max(axis=1)
    predicho = prob_cal.argmax(axis=1)
    acierto = predicho == y

    print()
    print("=== Equilibrio entre exigencia y cobertura ===")
    print("umbral | responde | acierta en lo que responde")
    recomendado = 0.5
    for umbral in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        responde = confianza >= umbral
        cobertura = responde.mean()
        if responde.sum() > 0:
            acierto_resp = acierto[responde].mean()
        else:
            acierto_resp = float("nan")
        print(f"  {umbral:.1f}  |  {cobertura*100:4.0f}%  |  {acierto_resp*100:4.0f}%")

    # Recomendamos el umbral mas bajo que consigue al menos un 90% de acierto en lo respondido.
    for umbral in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        responde = confianza >= umbral
        if responde.sum() > 0 and acierto[responde].mean() >= 0.90:
            recomendado = float(umbral)
            break

    Path(RUTA_SALIDA).write_text(json.dumps({
        "temperatura": round(float(mejor_temp), 3),
        "umbral_confianza": recomendado,
    }, indent=2))
    print()
    print(f"Umbral recomendado: {recomendado}")
    print(f"Guardado en {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
