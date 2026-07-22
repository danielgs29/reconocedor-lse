"""
Evaluacion completa del modelo de signos que usa la aplicacion.

Genera, sobre el conjunto de prueba (grabaciones que el modelo nunca vio al entrenar), todo lo
necesario para defender el proyecto con rigor:

  1. El acierto honesto, con cuantas grabaciones se mide, y el acierto "entre las tres mejores".
  2. La matriz de confusion, que muestra con que signos se confunde cada signo.
  3. Las metricas por signo (precision, cobertura y su combinacion), para ver que la media
     global esconde signos muy buenos y otros flojos.
  4. La calibracion de la confianza: si el modelo dice 80 por ciento, deberia acertar el 80
     por ciento. Se compara antes y despues del ajuste por temperatura.
  5. El equilibrio del umbral: cuanto responde y cuanto acierta segun el nivel de exigencia.

Guarda las figuras y un informe en la carpeta del diario, fuera del repositorio.
El acierto oficial es siempre el del conjunto de prueba.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from tensorflow import keras

import caracteristicas

RUTA_MODELO = "models/transformer_pre_asl.keras"
RUTA_CALIBRACION = "calibracion.json"
SALIDA = Path("evaluacion")

ACENTO = "#0c9c93"


def softmax(z, temperatura=1.0):
    z = z / temperatura
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def cargar_nombres():
    """Lista de nombres de signo, indexada por el numero interno del modelo."""
    vocab = json.loads(Path("vocabulario.json").read_text())
    num_signos = max(v["indice_modelo"] for v in vocab) + 1
    nombres = [""] * num_signos
    for v in vocab:
        nombres[v["indice_modelo"]] = v["nombre_grupo"]
    return nombres


def cargar_grupo(grupo):
    X = np.load(f"data/processed/X_{grupo}.npy")
    y = np.load(f"data/processed/y_{grupo}.npy")
    return caracteristicas.a_entrada_modelo(X), y


def error_calibracion(prob, y, num_cajas=10):
    """Cuanto se aleja de media la confianza declarada del acierto real. Cero es perfecto."""
    confianza = prob.max(axis=1)
    predicho = prob.argmax(axis=1)
    acierto = (predicho == y).astype(float)
    error = 0.0
    for i in range(num_cajas):
        bajo, alto = i / num_cajas, (i + 1) / num_cajas
        en_caja = (confianza > bajo) & (confianza <= alto)
        if en_caja.sum() > 0:
            error += en_caja.mean() * abs(acierto[en_caja].mean() - confianza[en_caja].mean())
    return error


def figura_matriz(cm, ruta):
    plt.figure(figsize=(11, 9))
    plt.imshow(cm, cmap="viridis")
    plt.colorbar(label="numero de grabaciones")
    plt.xlabel("Signo predicho por el modelo")
    plt.ylabel("Signo real")
    plt.title("Matriz de confusion (validacion + prueba)")
    plt.tight_layout()
    plt.savefig(ruta, dpi=110)
    plt.close()


def figura_por_signo(nombres, f1, apoyo, ruta):
    """Barras de la puntuacion F1 de cada signo, de peor a mejor."""
    orden = np.argsort(f1)
    etiquetas = [f"{nombres[i]} ({apoyo[i]})" for i in orden]
    plt.figure(figsize=(9, 14))
    colores = [("#c22f2f" if f1[i] < 0.6 else ACENTO) for i in orden]
    plt.barh(range(len(orden)), f1[orden], color=colores)
    plt.yticks(range(len(orden)), etiquetas, fontsize=7)
    plt.xlabel("Puntuacion F1 (0 a 1)")
    plt.title("Acierto por signo, de peor a mejor\n(entre parentesis, grabaciones de prueba)")
    plt.xlim(0, 1)
    plt.tight_layout()
    plt.savefig(ruta, dpi=110)
    plt.close()


def figura_calibracion(prob_sin, prob_con, y, ruta, num_cajas=10):
    """Diagrama de fiabilidad: confianza declarada frente a acierto real, antes y despues."""
    plt.figure(figsize=(7, 7))
    plt.plot([0, 1], [0, 1], "--", color="#888", label="ideal")
    for prob, etiqueta, color in [(prob_sin, "sin ajuste", "#c22f2f"), (prob_con, "con temperatura", ACENTO)]:
        conf = prob.max(axis=1)
        acierto = (prob.argmax(axis=1) == y).astype(float)
        xs, ys = [], []
        for i in range(num_cajas):
            bajo, alto = i / num_cajas, (i + 1) / num_cajas
            en_caja = (conf > bajo) & (conf <= alto)
            # Solo tramos con suficientes casos; con uno o dos, el punto es puro ruido.
            if en_caja.sum() >= 3:
                xs.append(conf[en_caja].mean())
                ys.append(acierto[en_caja].mean())
        plt.plot(xs, ys, "o-", color=color, label=etiqueta)
    plt.xlabel("Confianza que declara el modelo")
    plt.ylabel("Acierto real")
    plt.title("Calibracion de la confianza")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ruta, dpi=110)
    plt.close()


def figura_umbral(prob, y, ruta):
    """Como cambian cobertura y acierto segun el umbral de exigencia."""
    conf = prob.max(axis=1)
    acierto = prob.argmax(axis=1) == y
    umbrales = np.linspace(0, 0.95, 40)
    cobertura, precision = [], []
    for u in umbrales:
        responde = conf >= u
        cobertura.append(responde.mean())
        precision.append(acierto[responde].mean() if responde.sum() > 0 else np.nan)
    plt.figure(figsize=(8, 6))
    plt.plot(umbrales, cobertura, "o-", color="#a86a10", label="responde (cobertura)")
    plt.plot(umbrales, precision, "o-", color=ACENTO, label="acierta en lo que responde")
    plt.xlabel("Umbral de confianza")
    plt.ylabel("Proporcion")
    plt.title("Equilibrio entre responder y acertar")
    plt.ylim(0, 1.02)
    plt.legend()
    plt.tight_layout()
    plt.savefig(ruta, dpi=110)
    plt.close()


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    nombres = cargar_nombres()
    num_signos = len(nombres)
    temperatura = json.loads(Path(RUTA_CALIBRACION).read_text())["temperatura"]

    modelo = keras.models.load_model(RUTA_MODELO)

    # El acierto oficial se mide solo sobre prueba, que es el numero honesto.
    Xtest, ytest = cargar_grupo("test")
    prob_test = modelo.predict(Xtest, verbose=0)
    n = len(ytest)
    top1 = (prob_test.argmax(axis=1) == ytest).mean()
    top3 = np.mean([ytest[i] in np.argsort(prob_test[i])[-3:] for i in range(n)])

    # El diagnostico (matriz, metricas por signo, calibracion y umbral) se hace sobre validacion
    # y prueba juntas, porque con solo prueba hay muy pocos ejemplos por signo y las cifras
    # salen ruidosas. Es la misma convencion que ya usan calibrar.py y analizar_errores.py.
    Xval, yval = cargar_grupo("val")
    X = np.concatenate([Xval, Xtest])
    y = np.concatenate([yval, ytest])
    prob = modelo.predict(X, verbose=0)
    prob_cal = softmax(np.log(prob + 1e-12), temperatura)
    predicho = prob.argmax(axis=1)
    n_diag = len(y)

    # 3. Metricas por signo
    prec, cob, f1, apoyo = precision_recall_fscore_support(
        y, predicho, labels=range(num_signos), zero_division=0
    )

    # 2. Matriz de confusion
    cm = confusion_matrix(y, predicho, labels=range(num_signos))

    # 4 y 5. Calibracion y umbral
    ece_antes = error_calibracion(prob, y)
    ece_despues = error_calibracion(prob_cal, y)

    # Figuras
    figura_matriz(cm, SALIDA / "matriz-confusion.png")
    figura_por_signo(nombres, f1, apoyo, SALIDA / "acierto-por-signo.png")
    figura_calibracion(prob, prob_cal, y, SALIDA / "calibracion.png")
    figura_umbral(prob_cal, y, SALIDA / "umbral.png")

    # Informe en texto
    lineas = []
    lineas.append("# Evaluacion del modelo de signos\n")
    lineas.append(f"Modelo evaluado: `{RUTA_MODELO}`. Reconoce {num_signos} signos.\n")
    lineas.append("Todas las cifras se miden sobre el conjunto de prueba, grabaciones que el "
                  "modelo no vio al entrenar. Es el numero honesto.\n")
    lineas.append("## Acierto (conjunto de prueba)\n")
    lineas.append(f"- Grabaciones de prueba: {n}")
    lineas.append(f"- Acierto: {top1*100:.1f}%")
    lineas.append(f"- Acierto entre las tres mejores opciones: {top3*100:.1f}%\n")
    lineas.append(f"El resto del diagnostico (calibracion, metricas por signo, matriz de "
                  f"confusion y umbral) se calcula sobre validacion mas prueba juntas, "
                  f"{n_diag} grabaciones, porque con solo prueba hay muy pocos ejemplos por "
                  f"signo y las cifras salen ruidosas.\n")
    lineas.append("## Calibracion de la confianza\n")
    lineas.append(f"- Error de calibracion sin ajuste: {ece_antes:.3f}")
    lineas.append(f"- Error de calibracion con temperatura {temperatura}: {ece_despues:.3f}")
    lineas.append("- Mas cerca de cero es mejor. Ver `calibracion.png`.\n")
    lineas.append("## Signos que peor se reconocen\n")
    orden = np.argsort(f1)
    lineas.append("| Signo | Precision | Cobertura | F1 | Ejemplos |")
    lineas.append("|---|---|---|---|---|")
    for i in orden[:10]:
        lineas.append(f"| {nombres[i]} | {prec[i]*100:.0f}% | {cob[i]*100:.0f}% | {f1[i]:.2f} | {apoyo[i]} |")
    lineas.append("\n## Pares de signos que mas se confunden\n")
    pares = []
    for real in range(num_signos):
        for pred in range(num_signos):
            if real != pred and cm[real, pred] > 0:
                pares.append((int(cm[real, pred]), nombres[real], nombres[pred]))
    pares.sort(reverse=True)
    lineas.append("| Veces | Signo real | Confundido con |")
    lineas.append("|---|---|---|")
    for veces, real, pred in pares[:12]:
        lineas.append(f"| {veces} | {real} | {pred} |")
    lineas.append("\n## Metricas de todos los signos\n")
    lineas.append("| Signo | Precision | Cobertura | F1 | Ejemplos |")
    lineas.append("|---|---|---|---|---|")
    for i in np.argsort([-f1[j] for j in range(num_signos)]):
        lineas.append(f"| {nombres[i]} | {prec[i]*100:.0f}% | {cob[i]*100:.0f}% | {f1[i]:.2f} | {apoyo[i]} |")
    lineas.append("\n## Figuras\n")
    lineas.append("- `matriz-confusion.png`: que predijo el modelo para cada signo real.")
    lineas.append("- `acierto-por-signo.png`: puntuacion F1 de cada signo, de peor a mejor.")
    lineas.append("- `calibracion.png`: confianza declarada frente a acierto real.")
    lineas.append("- `umbral.png`: cuanto responde y cuanto acierta segun la exigencia.")
    (SALIDA / "informe-evaluacion.md").write_text("\n".join(lineas), encoding="utf-8")

    # Resumen por consola
    print(f"Grabaciones de prueba: {n}")
    print(f"Acierto: {top1*100:.1f}%   |   entre las tres mejores: {top3*100:.1f}%")
    print(f"Error de calibracion: {ece_antes:.3f} sin ajuste -> {ece_despues:.3f} con temperatura {temperatura}")
    print(f"F1 medio entre signos: {f1.mean():.2f}")
    print()
    print(f"Informe y figuras guardados en: {SALIDA}")


if __name__ == "__main__":
    main()
