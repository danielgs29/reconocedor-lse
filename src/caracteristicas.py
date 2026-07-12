"""
Prepara la entrada que recibe el modelo, a partir de las grabaciones ya normalizadas.

Esta preparacion se define aqui, en un unico sitio, para que todos los programas la hagan
igual: el entrenamiento, la calibracion y el analisis de errores. Ademas, cuando llevemos
el modelo al navegador habra que replicar exactamente estos mismos pasos en JavaScript.

A partir de una grabacion (fotogramas, 61, 3), con las coordenadas x, y, z de cada punto,
se anade el movimiento de cada punto y se aplana todo en un vector por fotograma.
"""

import numpy as np


def anadir_velocidad(X):
    """
    Anade el movimiento de cada punto: cuanto cambia su posicion respecto al fotograma
    anterior. Duplica las coordenadas, ya que a cada punto se le suman las de su movimiento.

    El movimiento se pone a cero en el primer fotograma y donde el punto falta en el
    fotograma actual o en el anterior, para no inventar saltos.
    """
    presente = np.any(X != 0, axis=-1)  # (n, fotogramas, puntos)
    velocidad = np.zeros_like(X)
    velocidad[:, 1:] = X[:, 1:] - X[:, :-1]
    valido = presente[:, 1:] & presente[:, :-1]
    velocidad[:, 1:][~valido] = 0
    return np.concatenate([X, velocidad], axis=-1)


def aplanar(X):
    """Une todos los valores de los puntos en un solo vector por fotograma."""
    n, fotogramas, puntos, coords = X.shape
    return X.reshape(n, fotogramas, puntos * coords)


def a_entrada_modelo(X):
    """Convierte grabaciones (n, fotogramas, 61, 3) en la entrada del modelo."""
    return aplanar(anadir_velocidad(X))
