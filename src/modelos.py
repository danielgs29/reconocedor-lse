"""
Definiciones de los modelos que probamos.

Contiene dos modelos que reciben una secuencia de fotogramas, donde cada fotograma es un
vector de numeros, y devuelven una probabilidad por cada signo:

  - GRU: una red que recorre los fotogramas en orden acumulando memoria.
  - Transformer: una red que mira todos los fotogramas a la vez y aprende a que fotogramas
    prestar atencion.

En los dos casos, los fotogramas de relleno, que son todo ceros, se ignoran.
"""

import keras
from keras import layers, ops


def compilar(modelo, pasos_por_epoca, epocas, lr_pico=1e-3):
    """
    Prepara el modelo para entrenar con un buen ritmo de aprendizaje.

    Usa calentamiento seguido de descenso suave, el optimizador AdamW y recorte de gradiente.
    Esto estabiliza el entrenamiento, sobre todo en modelos grandes, que con un ritmo fijo
    tienden a no converger.
    """
    total = max(1, pasos_por_epoca * epocas)
    calentamiento = max(1, int(0.05 * total))
    ritmo = keras.optimizers.schedules.CosineDecay(
        initial_learning_rate=0.0,
        decay_steps=max(1, total - calentamiento),
        warmup_target=lr_pico,
        warmup_steps=calentamiento,
    )
    optimizador = keras.optimizers.AdamW(learning_rate=ritmo, weight_decay=1e-4, clipnorm=1.0)
    modelo.compile(optimizer=optimizador, loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return modelo


def construir_gru(num_pasos, num_rasgos, num_signos):
    """Modelo de secuencia GRU, sin compilar."""
    return keras.Sequential([
        keras.Input(shape=(num_pasos, num_rasgos)),
        layers.Masking(mask_value=0.0),
        layers.GRU(64),
        layers.Dropout(0.3),
        layers.Dense(num_signos, activation="softmax"),
    ])


def construir_transformer(num_pasos, num_rasgos, num_signos, dimension=64, cabezas=4, oculta=128, bloques=2, dropout=0.3):
    """Modelo Transformer con atencion, que ignora los fotogramas de relleno."""
    entradas = keras.Input(shape=(num_pasos, num_rasgos))

    # Marca de fotogramas validos: True donde el fotograma no es todo ceros.
    validos = ops.any(ops.not_equal(entradas, 0.0), axis=-1)          # (lote, pasos)
    mascara_atencion = ops.expand_dims(validos, axis=1)               # (lote, 1, pasos)

    # Llevamos cada fotograma a un tamano comun y le sumamos su posicion en la secuencia,
    # para que el modelo sepa el orden de los fotogramas.
    x = layers.Dense(dimension)(entradas)
    posiciones = ops.arange(0, num_pasos)
    x = x + layers.Embedding(num_pasos, dimension)(posiciones)

    # Bloques de atencion.
    for _ in range(bloques):
        atencion = layers.MultiHeadAttention(num_heads=cabezas, key_dim=dimension // cabezas)(
            x, x, attention_mask=mascara_atencion
        )
        x = layers.LayerNormalization()(x + atencion)
        salto = layers.Dense(oculta, activation="relu")(x)
        salto = layers.Dense(dimension)(salto)
        x = layers.LayerNormalization()(x + salto)

    # Resumimos la secuencia promediando solo los fotogramas validos.
    peso = ops.expand_dims(ops.cast(validos, x.dtype), axis=-1)       # (lote, pasos, 1)
    x = ops.sum(x * peso, axis=1) / ops.maximum(ops.sum(peso, axis=1), 1.0)

    x = layers.Dropout(dropout)(x)
    salidas = layers.Dense(num_signos, activation="softmax")(x)

    return keras.Model(entradas, salidas)
