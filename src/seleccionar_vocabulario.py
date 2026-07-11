"""
Selecciona el vocabulario de trabajo del proyecto y lo guarda en un archivo fijo.

De los 300 signos del conjunto de datos, se eligen los que tienen al menos un numero
minimo de ejemplos, para que el modelo pueda aprenderlos bien. El resultado se guarda en
vocabulario.json.

Cada signo elegido recibe un numero interno correlativo, del 0 en adelante, que es el que
usara el modelo. Esto es necesario porque los signos vienen numerados del 0 al 299 con
huecos una vez descartamos algunos, y el modelo necesita numeros seguidos.
"""

import json
from collections import Counter
from pathlib import Path

MINIMO_EJEMPLOS = 40

CARPETA_ANNS = Path("data/raw/annotations/ANNOTATIONS")
RUTA_NOMBRES = Path("data/raw/videos_ref_annotations.csv")
RUTA_SALIDA = Path("vocabulario.json")


def leer_etiquetas(nombre_archivo):
    """Devuelve una lista de (identificador, numero_de_signo) de un archivo de etiquetas."""
    pares = []
    for linea in (CARPETA_ANNS / nombre_archivo).read_text().strip().splitlines():
        identificador, numero_signo = linea.split(",")
        pares.append((identificador, int(numero_signo)))
    return pares


def leer_nombres():
    """Devuelve un diccionario que traduce el numero de signo a su nombre."""
    nombres = {}
    lineas = RUTA_NOMBRES.read_text().strip().splitlines()[1:]  # se salta la cabecera
    for linea in lineas:
        _, numero_signo, nombre = linea.split(",", 2)
        nombres[int(numero_signo)] = nombre
    return nombres


def main():
    todas = leer_etiquetas("train_labels.csv") + leer_etiquetas("val_labels.csv") + leer_etiquetas("test_labels.csv")
    ejemplos_por_signo = Counter(numero for _, numero in todas)
    nombres = leer_nombres()

    # Signos que superan el minimo, ordenados de mas a menos ejemplos.
    elegidos = [signo for signo, cuenta in ejemplos_por_signo.most_common() if cuenta >= MINIMO_EJEMPLOS]

    vocabulario = []
    for indice_modelo, numero_signo in enumerate(elegidos):
        vocabulario.append({
            "indice_modelo": indice_modelo,
            "numero_signo_original": numero_signo,
            "nombre": nombres.get(numero_signo, "desconocido"),
            "ejemplos": ejemplos_por_signo[numero_signo],
        })

    RUTA_SALIDA.write_text(json.dumps(vocabulario, ensure_ascii=False, indent=2))

    print(f"Vocabulario guardado en {RUTA_SALIDA}")
    print(f"Signos seleccionados: {len(vocabulario)} (con al menos {MINIMO_EJEMPLOS} ejemplos)")
    print(f"Ejemplos en total en el vocabulario: {sum(v['ejemplos'] for v in vocabulario)}")


if __name__ == "__main__":
    main()
