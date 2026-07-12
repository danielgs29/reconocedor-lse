"""
Selecciona el vocabulario de trabajo del proyecto y lo guarda en un archivo fijo.

De los 300 signos del conjunto de datos se eligen los que tienen al menos un numero minimo
de ejemplos. Ademas, las variantes del mismo signo se juntan en un solo concepto. Por
ejemplo, PIS, PIS2, PIS3 y PIS4 son formas distintas de signar lo mismo, asi que se tratan
como un unico signo llamado PIS. Esto reduce las confusiones y da mas ejemplos por concepto.

Cada concepto recibe un numero interno correlativo, del 0 en adelante, que es el que usara
el modelo. Varias variantes pueden compartir el mismo numero interno.
"""

import json
import re
from collections import Counter, OrderedDict
from pathlib import Path

MINIMO_EJEMPLOS = 40

CARPETA_ANNS = Path("data/raw/annotations/ANNOTATIONS")
RUTA_NOMBRES = Path("data/raw/videos_ref_annotations.csv")
RUTA_SALIDA = Path("vocabulario.json")


def leer_etiquetas(nombre_archivo):
    pares = []
    for linea in (CARPETA_ANNS / nombre_archivo).read_text().strip().splitlines():
        identificador, numero_signo = linea.split(",")
        pares.append((identificador, int(numero_signo)))
    return pares


def leer_nombres():
    nombres = {}
    for linea in RUTA_NOMBRES.read_text().strip().splitlines()[1:]:
        _, numero_signo, nombre = linea.split(",", 2)
        nombres[int(numero_signo)] = nombre
    return nombres


def concepto_base(nombre):
    """Reduce el nombre de un signo a su concepto: quita la anotacion y los numeros finales."""
    base = nombre.split("(")[0]      # quita lo que va desde el primer parentesis
    base = re.sub(r"\d+$", "", base)  # quita numeros al final, CANSADO2 -> CANSADO
    return base.strip()


def main():
    todas = leer_etiquetas("train_labels.csv") + leer_etiquetas("val_labels.csv") + leer_etiquetas("test_labels.csv")
    ejemplos_por_signo = Counter(numero for _, numero in todas)
    nombres = leer_nombres()

    # Signos que superan el minimo de ejemplos, de mas a menos.
    elegidos = [signo for signo, cuenta in ejemplos_por_signo.most_common() if cuenta >= MINIMO_EJEMPLOS]

    # Agrupar los elegidos por concepto base.
    grupos = OrderedDict()
    for signo in elegidos:
        base = concepto_base(nombres[signo])
        grupos.setdefault(base, []).append(signo)

    # Ordenar los conceptos por numero total de ejemplos, de mas a menos.
    conceptos = sorted(grupos.items(), key=lambda kv: -sum(ejemplos_por_signo[s] for s in kv[1]))

    vocabulario = []
    for indice, (base, signos) in enumerate(conceptos):
        for signo in signos:
            vocabulario.append({
                "indice_modelo": indice,
                "nombre_grupo": base,
                "numero_signo_original": signo,
                "nombre_original": nombres[signo],
                "ejemplos": ejemplos_por_signo[signo],
            })

    RUTA_SALIDA.write_text(json.dumps(vocabulario, ensure_ascii=False, indent=2))

    total_ejemplos = sum(v["ejemplos"] for v in vocabulario)
    print(f"Vocabulario guardado en {RUTA_SALIDA}")
    print(f"Signos originales seleccionados: {len(vocabulario)}")
    print(f"Conceptos tras juntar variantes: {len(conceptos)}")
    print(f"Ejemplos en total: {total_ejemplos}")


if __name__ == "__main__":
    main()
