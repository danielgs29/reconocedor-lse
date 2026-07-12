"""
Aumento de datos para las secuencias de puntos.

A partir de una grabacion se generan variaciones que no cambian el signo pero si los
numeros: pequenos giros, cambios de tamano y ruido leve. Esto ayuda a que el modelo vea mas
variedad y memorice menos, que es el problema de sobreajuste que detectamos.

Regla que se respeta siempre: los puntos que no se detectaron, que estan a cero, deben
seguir a cero despues de las variaciones. De lo contrario se estropearia la marca de
fotograma de relleno que usa el modelo.
"""

import numpy as np

# El giro y el escalado se hacen respecto al origen. Como los puntos ausentes valen (0, 0),
# girarlos o escalarlos los deja igual, en (0, 0). Por eso estas dos operaciones son seguras.
# El ruido si podria mover un cero, asi que se aplica solo a los puntos presentes.


def _puntos_presentes(secuencia):
    """Devuelve una mascara con True donde el punto existe, es decir no es (0, 0)."""
    return np.any(secuencia != 0, axis=-1)  # forma (fotogramas, puntos)


def girar(secuencia, angulo):
    """Gira todas las coordenadas un angulo dado, en radianes, respecto al centro."""
    coseno, seno = np.cos(angulo), np.sin(angulo)
    rotacion = np.array([[coseno, -seno], [seno, coseno]], dtype=np.float32)
    return (secuencia @ rotacion.T).astype(np.float32)


def escalar(secuencia, factor):
    """Multiplica todas las coordenadas por un factor."""
    return (secuencia * factor).astype(np.float32)


def anadir_ruido(secuencia, desviacion, generador):
    """Anade un ruido leve solo a los puntos presentes."""
    mascara = _puntos_presentes(secuencia)[..., None]  # forma (fotogramas, puntos, 1)
    ruido = generador.normal(0, desviacion, secuencia.shape).astype(np.float32)
    return (secuencia + ruido * mascara).astype(np.float32)


def variar(secuencia, generador):
    """Aplica una combinacion aleatoria de variaciones a una grabacion."""
    angulo = generador.uniform(-0.26, 0.26)  # unos 15 grados a cada lado
    factor = generador.uniform(0.9, 1.1)
    secuencia = girar(secuencia, angulo)
    secuencia = escalar(secuencia, factor)
    secuencia = anadir_ruido(secuencia, 0.01, generador)
    return secuencia


def ampliar_entrenamiento(X, y, copias, semilla=0):
    """
    Devuelve el conjunto de entrenamiento ampliado.

    Junta las grabaciones originales con un numero de copias variadas de cada una. Por
    ejemplo, con copias=3 el conjunto pasa a ser cuatro veces mayor: el original mas tres
    versiones variadas.
    """
    generador = np.random.default_rng(semilla)
    lista_X = [X]
    lista_y = [y]
    for _ in range(copias):
        variadas = np.stack([variar(secuencia, generador) for secuencia in X])
        lista_X.append(variadas)
        lista_y.append(y)
    return np.concatenate(lista_X), np.concatenate(lista_y)
