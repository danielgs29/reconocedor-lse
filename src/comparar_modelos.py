"""
Compara los modelos del proyecto sobre el mismo conjunto de prueba y registra el resultado en
MLflow, que es la herramienta de seguimiento de experimentos que se uso en el master.

El registro de MLflow del desarrollo quedo sin datos (solo sobrevivieron los archivos de
modelo), asi que aqui se vuelve a medir cada modelo guardado con las mismas grabaciones de
prueba y se anota como una ejecucion nueva en MLflow, con sus parametros y su acierto. Asi la
comparacion es reproducible y se puede explorar con la interfaz de MLflow.

Solo se comparan los modelos que reconocen el mismo vocabulario de 64 signos y esperan la
misma entrada. A partir del registro de MLflow se genera tambien una tabla en markdown.

Para abrir la interfaz despues:
    MLFLOW_ALLOW_FILE_STORE=true uv run mlflow ui
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
# Esta version de MLflow bloquea por defecto el almacenamiento en archivos; lo reactivamos
# para seguir usando la carpeta mlruns como en el master.
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

from pathlib import Path

import mlflow
import numpy as np
from tensorflow import keras

import caracteristicas

CARPETA_MODELOS = Path("models")
SALIDA = Path("evaluacion/comparacion-modelos.md")
EXPERIMENTO = "comparacion-modelos-lse"

# Descripcion de cada modelo: que arquitectura usa, si lleva aumento de datos y con que
# preentrenamiento parte. Se registra como parametros en MLflow.
META = {
    "transformer_64conceptos.keras": ("Transformer", "si", "ninguno"),
    "transformer_64_grande.keras": ("Transformer grande", "si", "ninguno"),
    "transformer_pre_asl.keras": ("Transformer", "si", "signos americanos (ASL)"),
    "transformer_pre_lsa64.keras": ("Transformer", "si", "signos argentinos (LSA64)"),
}
DESPLEGADO = "transformer_pre_asl.keras"


def describir(nombre):
    if nombre in META:
        return META[nombre]
    arq = "GRU" if "gru" in nombre else "Transformer"
    aumento = "si" if "aumento" in nombre else "?"
    if "pre_asl" in nombre:
        pre = "signos americanos (ASL)"
    elif "pre_lsa" in nombre:
        pre = "signos argentinos (LSA64)"
    else:
        pre = "ninguno"
    return arq, aumento, pre


def main():
    Xtest = caracteristicas.a_entrada_modelo(np.load("data/processed/X_test.npy"))
    ytest = np.load("data/processed/y_test.npy")
    num_signos = int(ytest.max()) + 1
    entrada_esperada = Xtest.shape[1:]
    print(f"Conjunto de prueba: {len(ytest)} grabaciones, {num_signos} signos.\n")

    mlflow.set_tracking_uri("file:./mlruns")
    exp = mlflow.get_experiment_by_name(EXPERIMENTO)
    if exp is not None:
        # Borramos las ejecuciones previas para no acumular duplicados al reejecutar.
        previas = mlflow.search_runs(experiment_ids=[exp.experiment_id])
        for rid in previas.get("run_id", []):
            mlflow.delete_run(rid)
        exp_id = exp.experiment_id
    else:
        exp_id = mlflow.create_experiment(EXPERIMENTO)

    no_comparables = []
    for ruta in sorted(CARPETA_MODELOS.glob("*.keras")):
        if ruta.name == "abecedario.keras" or ruta.name.startswith("preentrenado_"):
            continue
        try:
            modelo = keras.models.load_model(ruta)
        except Exception as e:
            no_comparables.append((ruta.name, f"no se pudo cargar ({type(e).__name__})"))
            continue
        if modelo.output_shape[-1] != num_signos:
            no_comparables.append((ruta.name, f"otro vocabulario ({modelo.output_shape[-1]} signos)"))
            continue
        if tuple(modelo.input_shape[1:]) != entrada_esperada:
            no_comparables.append((ruta.name, f"otra entrada {tuple(modelo.input_shape[1:])}"))
            continue

        acierto = float((modelo.predict(Xtest, verbose=0).argmax(axis=1) == ytest).mean())
        arq, aumento, pre = describir(ruta.name)
        with mlflow.start_run(experiment_id=exp_id, run_name=ruta.name):
            mlflow.log_param("arquitectura", arq)
            mlflow.log_param("aumento_datos", aumento)
            mlflow.log_param("preentrenamiento", pre)
            mlflow.log_param("num_parametros", int(modelo.count_params()))
            mlflow.set_tag("archivo", ruta.name)
            mlflow.set_tag("desplegado", "si" if ruta.name == DESPLEGADO else "no")
            mlflow.log_metric("acierto_prueba", acierto)
            mlflow.log_metric("grabaciones_prueba", len(ytest))
        print(f"  {acierto*100:5.1f}%  {ruta.name}")

    # Leemos de MLflow lo que acabamos de registrar y construimos la tabla desde ahi.
    runs = mlflow.search_runs(experiment_ids=[exp_id], order_by=["metrics.acierto_prueba DESC"])

    lineas = ["# Comparacion de modelos (registrada en MLflow)\n"]
    lineas.append(f"Experimento MLflow: `{EXPERIMENTO}`. Mismo conjunto de prueba para todos: "
                  f"{len(ytest)} grabaciones, {num_signos} signos. Cada modelo se vuelve a medir; "
                  f"no se usan cifras antiguas.\n")
    lineas.append("Para explorarlo en la interfaz: `MLFLOW_ALLOW_FILE_STORE=true uv run mlflow ui`\n")
    lineas.append("| Modelo | Arquitectura | Aumento | Preentrenamiento | Acierto | Parametros | Desplegado |")
    lineas.append("|---|---|---|---|---|---|---|")
    for _, r in runs.iterrows():
        lineas.append(
            f"| {r['tags.archivo']} | {r['params.arquitectura']} | {r['params.aumento_datos']} "
            f"| {r['params.preentrenamiento']} | {r['metrics.acierto_prueba']*100:.1f}% "
            f"| {int(r['params.num_parametros']):,} | {r['tags.desplegado']} |"
        )
    if no_comparables:
        lineas.append("\n## No comparables (otro vocabulario o entrada distinta)\n")
        lineas.append("Los experimentos de red recurrente (GRU) y sin aumento se hicieron con un "
                      "vocabulario anterior de 53 signos, por lo que no se pueden medir sobre este "
                      "conjunto de prueba. Se listan para dejar constancia.\n")
        for nombre, razon in no_comparables:
            lineas.append(f"- {nombre}: {razon}")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nRegistradas {len(runs)} ejecuciones en MLflow (experimento '{EXPERIMENTO}').")
    print(f"Tabla guardada en: {SALIDA}")
    print("Ver en la interfaz: MLFLOW_ALLOW_FILE_STORE=true uv run mlflow ui")


if __name__ == "__main__":
    main()
