"""
Prepara los datos para entrenar a partir de los puntos ya convertidos.

Para cada uno de los tres grupos oficiales, entrenamiento, validacion y prueba, este
programa:

  1. Se queda solo con las grabaciones de nuestro vocabulario de 53 signos.
  2. Toma las coordenadas x, y, z de cada punto.
  3. Normaliza cada grabacion usando los hombros como referencia, de modo que la posicion y
     el tamano de la persona en la imagen dejen de importar.
  4. Ajusta todas las grabaciones a la misma duracion, 56 fotogramas, rellenando las cortas
     y recortando las largas.

El resultado se guarda como cuatro pares de matrices, una con las secuencias y otra con la
respuesta correcta, para cada grupo.
"""

import json
from pathlib import Path

import numpy as np

DURACION = 56  # numero de fotogramas al que se ajustan todas las grabaciones

# Posiciones del hombro izquierdo y derecho dentro de nuestros 61 puntos.
# Vienen de los puntos 11 y 12 del cuerpo de MediaPipe, que quedaron en estas posiciones.
POS_HOMBRO_IZQ = 5
POS_HOMBRO_DER = 6

CARPETA_KPS = Path("data/processed/keypoints")
CARPETA_ANNS = Path("data/raw/annotations/ANNOTATIONS")
CARPETA_SALIDA = Path("data/processed")


def cargar_vocabulario():
    """Devuelve un diccionario que traduce el numero de signo original al numero interno."""
    vocab = json.loads(Path("vocabulario.json").read_text())
    return {v["numero_signo_original"]: v["indice_modelo"] for v in vocab}


def normalizar(grabacion):
    """
    Normaliza una grabacion (fotogramas, 61, 4) y devuelve (fotogramas, 61, 3).

    Conserva las tres coordenadas x, y, z. Centra los puntos en el punto medio de los
    hombros y los escala por la distancia entre hombros. Los puntos que no se detectaron,
    que vienen a cero, se dejan a cero.
    """
    # Un punto esta presente si alguno de sus cuatro valores no es cero.
    presente = np.any(grabacion != 0, axis=-1)  # forma (fotogramas, 61)

    # Nos quedamos con las coordenadas x, y, z.
    xyz = grabacion[:, :, :3].copy()  # forma (fotogramas, 61, 3)

    # Referencia: usamos los fotogramas donde se ven los dos hombros.
    hombros_ok = presente[:, POS_HOMBRO_IZQ] & presente[:, POS_HOMBRO_DER]
    if not np.any(hombros_ok):
        # Sin hombros no podemos normalizar; devolvemos los puntos tal cual.
        xyz[~presente] = 0
        return xyz.astype(np.float32)

    izq = xyz[hombros_ok, POS_HOMBRO_IZQ, :]
    der = xyz[hombros_ok, POS_HOMBRO_DER, :]
    centro = ((izq + der) / 2).mean(axis=0)  # punto medio de los hombros, en x, y, z
    # La distancia entre hombros se mide en el plano de la imagen, con x e y.
    ancho = np.linalg.norm((izq - der)[:, :2], axis=1).mean()
    ancho = max(ancho, 1e-6)  # evitar dividir por cero

    xyz = (xyz - centro) / ancho

    # Los puntos ausentes vuelven a cero tras la normalizacion.
    xyz[~presente] = 0
    return xyz.astype(np.float32)


def ajustar_duracion(grabacion):
    """Ajusta una grabacion a DURACION fotogramas rellenando o recortando."""
    n = grabacion.shape[0]
    if n >= DURACION:
        return grabacion[:DURACION]
    relleno = np.zeros((DURACION - n, grabacion.shape[1], grabacion.shape[2]), dtype=grabacion.dtype)
    return np.concatenate([grabacion, relleno], axis=0)


def preparar_grupo(nombre_archivo, mapa_vocab):
    """Construye las matrices de secuencias y respuestas de un grupo."""
    secuencias = []
    respuestas = []
    for linea in (CARPETA_ANNS / nombre_archivo).read_text().strip().splitlines():
        identificador, numero_signo = linea.split(",")
        numero_signo = int(numero_signo)
        if numero_signo not in mapa_vocab:
            continue

        grabacion = np.load(CARPETA_KPS / f"{identificador}.npy")
        grabacion = normalizar(grabacion)
        grabacion = ajustar_duracion(grabacion)

        secuencias.append(grabacion)
        respuestas.append(mapa_vocab[numero_signo])

    return np.array(secuencias, dtype=np.float32), np.array(respuestas, dtype=np.int64)


def main():
    mapa_vocab = cargar_vocabulario()
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    for grupo, archivo in [("train", "train_labels.csv"), ("val", "val_labels.csv"), ("test", "test_labels.csv")]:
        X, y = preparar_grupo(archivo, mapa_vocab)
        np.save(CARPETA_SALIDA / f"X_{grupo}.npy", X)
        np.save(CARPETA_SALIDA / f"y_{grupo}.npy", y)
        print(f"{grupo}: secuencias {X.shape}, respuestas {y.shape}")


if __name__ == "__main__":
    main()
