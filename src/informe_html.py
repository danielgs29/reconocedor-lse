"""
Genera un informe visual de la evaluacion en una sola pagina HTML autonoma.

Reune las cifras principales, la comparacion de modelos registrada en MLflow y las cuatro
figuras (incrustadas en el propio archivo), con la identidad visual de la aplicacion. El
resultado, evaluacion/informe.html, se abre en el navegador y sirve para presentar o para
exportar a PDF. Regenera las cifras al vuelo, asi que siempre esta al dia.
"""

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

import base64
import json
from pathlib import Path

import mlflow
import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from tensorflow import keras

from evaluar import cargar_grupo, cargar_nombres, error_calibracion, softmax

EVAL = Path("evaluacion")
RUTA_MODELO = "models/transformer_pre_asl.keras"


def img(nombre):
    datos = base64.b64encode((EVAL / nombre).read_bytes()).decode()
    return f"data:image/png;base64,{datos}"


def filas_mlflow():
    mlflow.set_tracking_uri("file:./mlruns")
    exp = mlflow.get_experiment_by_name("comparacion-modelos-lse")
    if exp is None:
        return []
    runs = mlflow.search_runs(experiment_ids=[exp.experiment_id], order_by=["metrics.acierto_prueba DESC"])
    filas = []
    for _, r in runs.iterrows():
        filas.append({
            "modelo": r["tags.archivo"],
            "pre": r["params.preentrenamiento"],
            "acierto": r["metrics.acierto_prueba"] * 100,
            "params": int(r["params.num_parametros"]),
            "desplegado": r["tags.desplegado"] == "si",
        })
    return filas


def main():
    temperatura = json.loads(Path("calibracion.json").read_text())["temperatura"]
    nombres = cargar_nombres()
    num_signos = len(nombres)
    modelo = keras.models.load_model(RUTA_MODELO)

    Xtest, ytest = cargar_grupo("test")
    prob_test = modelo.predict(Xtest, verbose=0)
    n = len(ytest)
    top1 = (prob_test.argmax(axis=1) == ytest).mean() * 100
    top3 = np.mean([ytest[i] in np.argsort(prob_test[i])[-3:] for i in range(n)]) * 100

    Xval, yval = cargar_grupo("val")
    X = np.concatenate([Xval, Xtest]); y = np.concatenate([yval, ytest])
    prob = modelo.predict(X, verbose=0)
    prob_cal = softmax(np.log(prob + 1e-12), temperatura)
    predicho = prob.argmax(axis=1)
    ece_antes = error_calibracion(prob, y)
    ece_despues = error_calibracion(prob_cal, y)
    prec, cob, f1, apoyo = precision_recall_fscore_support(
        y, predicho, labels=range(num_signos), zero_division=0
    )
    f1_medio = f1.mean()

    peores = [i for i in np.argsort(f1) if apoyo[i] > 0][:8]
    filas_peores = "".join(
        f"<tr><td>{nombres[i]}</td><td class='num'>{prec[i]*100:.0f}%</td>"
        f"<td class='num'>{cob[i]*100:.0f}%</td><td class='num'>{f1[i]:.2f}</td>"
        f"<td class='num'>{apoyo[i]}</td></tr>"
        for i in peores
    )

    filas_cmp = "".join(
        f"<tr class='{'destacada' if f['desplegado'] else ''}'>"
        f"<td>{f['modelo']}{' &middot; desplegado' if f['desplegado'] else ''}</td>"
        f"<td>{f['pre']}</td><td class='num'>{f['acierto']:.1f}%</td>"
        f"<td class='num'>{f['params']:,}</td></tr>"
        for f in filas_mlflow()
    )

    figuras = [
        ("matriz-confusion.png", "Matriz de confusion",
         "Que predijo el modelo para cada signo real. La diagonal son los aciertos; fuera de ella, las confusiones."),
        ("acierto-por-signo.png", "Acierto por signo",
         "Puntuacion F1 de cada signo, de peor a mejor. En rojo, los que quedan por debajo de 0,6."),
        ("calibracion.png", "Calibracion de la confianza",
         "La confianza que declara el modelo frente al acierto real. Cuanto mas cerca de la diagonal, mas sincera."),
        ("umbral.png", "Equilibrio del umbral",
         "Al subir la exigencia, el modelo acierta mas en lo que responde pero responde menos veces."),
    ]
    bloques_fig = "".join(
        f"<figure><img src='{img(f)}' alt='{t}'><figcaption><b>{t}.</b> {d}</figcaption></figure>"
        for f, t, d in figuras
    )

    html = PLANTILLA.format(
        top1=f"{top1:.1f}", top3=f"{top3:.1f}", f1=f"{f1_medio:.2f}",
        ece_antes=f"{ece_antes:.3f}", ece_despues=f"{ece_despues:.3f}",
        n=n, n_diag=len(y), num_signos=num_signos,
        filas_cmp=filas_cmp, filas_peores=filas_peores, figuras=bloques_fig,
    )
    (EVAL / "informe.html").write_text(html, encoding="utf-8")
    print(f"Informe generado en: {EVAL / 'informe.html'}")
    print(f"Acierto {top1:.1f}% | top-3 {top3:.1f}% | F1 {f1_medio:.2f} | calibracion {ece_antes:.3f}->{ece_despues:.3f}")


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signia - Evaluacion del modelo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0b0f0e; --surface:#121a19; --surface-2:#0d1413; --text:#e9efee; --muted:#8fa09d;
    --border:#263230; --accent:#1cc3b8; --accent-ink:#04211e; --bad:#ff7a7a;
    --font:"Space Grotesk",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg:#eef1f0; --surface:#fff; --surface-2:#e7ecea; --text:#14201e; --muted:#5a6a68;
      --border:#d3dcda; --accent:#0c9c93; --accent-ink:#fff; --bad:#c22f2f; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:var(--font);
    line-height:1.55; padding:2.5rem 1.25rem 4rem; }}
  .marco {{ max-width:960px; margin:0 auto; }}
  header {{ border-bottom:1px solid var(--border); padding-bottom:1.2rem; margin-bottom:2rem; }}
  .logo {{ font-weight:700; text-transform:uppercase; letter-spacing:-0.01em; font-size:1.3rem; margin:0; }}
  .logo span {{ color:var(--accent); }}
  h1 {{ font-size:1.9rem; letter-spacing:-0.02em; margin:0.6rem 0 0.3rem; text-wrap:balance; }}
  .sub {{ color:var(--muted); margin:0; font-size:0.95rem; }}
  h2 {{ font-size:1.15rem; margin:2.4rem 0 1rem; padding-top:1.4rem; border-top:1px solid var(--border); }}
  .tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:0.8rem; margin-top:1.5rem; }}
  .tile {{ background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:1.1rem; }}
  .tile .v {{ font-size:2rem; font-weight:700; color:var(--accent); font-variant-numeric:tabular-nums; }}
  .tile .k {{ font-family:var(--mono); font-size:0.66rem; text-transform:uppercase; letter-spacing:0.09em; color:var(--muted); margin-top:0.3rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.9rem; margin-top:0.5rem; }}
  th, td {{ text-align:left; padding:0.55rem 0.7rem; border-bottom:1px solid var(--border); }}
  th {{ font-family:var(--mono); font-size:0.66rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); font-weight:600; }}
  td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr.destacada td {{ background:color-mix(in srgb, var(--accent) 12%, transparent); font-weight:600; }}
  .figuras {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:1.2rem; }}
  figure {{ margin:0; background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:0.9rem; }}
  figure img {{ width:100%; border-radius:8px; display:block; background:#fff; }}
  figcaption {{ color:var(--muted); font-size:0.82rem; margin-top:0.7rem; }}
  figcaption b {{ color:var(--text); }}
  .nota {{ color:var(--muted); font-size:0.82rem; }}
  ul {{ padding-left:1.1rem; }} li {{ margin:0.3rem 0; }}
</style>
</head>
<body>
<div class="marco">
  <header>
    <p class="logo">Sign<span>ia</span><span>_</span></p>
    <h1>Evaluacion del modelo de signos</h1>
    <p class="sub">Reconocedor de {num_signos} signos de la Lengua de Signos Espanola. Cifras medidas sobre el conjunto de prueba, grabaciones que el modelo no vio al entrenar.</p>
  </header>

  <div class="tiles">
    <div class="tile"><div class="v">{top1}%</div><div class="k">Acierto en prueba</div></div>
    <div class="tile"><div class="v">{top3}%</div><div class="k">Entre las tres mejores</div></div>
    <div class="tile"><div class="v">{f1}</div><div class="k">F1 medio por signo</div></div>
    <div class="tile"><div class="v">{ece_despues}</div><div class="k">Error de calibracion</div></div>
  </div>
  <p class="nota">Sobre {n} grabaciones de prueba. El diagnostico por signo y la calibracion se calculan sobre validacion mas prueba ({n_diag} grabaciones) para tener suficientes ejemplos. La calibracion mejora de {ece_antes} a {ece_despues} con el ajuste por temperatura.</p>

  <h2>Comparacion de modelos (registrada en MLflow)</h2>
  <p class="nota">Todos medidos sobre el mismo conjunto de prueba. El preentrenamiento con signos americanos es lo que da el salto; agrandar el modelo no ayuda, lo que indica que el techo lo marcan los datos, no la capacidad.</p>
  <table>
    <thead><tr><th>Modelo</th><th>Preentrenamiento</th><th class="num">Acierto</th><th class="num">Parametros</th></tr></thead>
    <tbody>{filas_cmp}</tbody>
  </table>

  <h2>Figuras</h2>
  <div class="figuras">{figuras}</div>

  <h2>Signos que peor se reconocen</h2>
  <p class="nota">Precision: de las veces que dijo este signo, cuantas acerto. Cobertura: de las veces que era este signo, cuantas cazo. F1 combina ambas.</p>
  <table>
    <thead><tr><th>Signo</th><th class="num">Precision</th><th class="num">Cobertura</th><th class="num">F1</th><th class="num">Ejemplos</th></tr></thead>
    <tbody>{filas_peores}</tbody>
  </table>

  <h2>Limites</h2>
  <ul>
    <li>Vocabulario cerrado: {num_signos} signos del ambito de la salud. Fuera de esa lista no reconoce.</li>
    <li>Conjunto de prueba pequeno: pocos ejemplos por signo, asi que las cifras de un signo concreto tienen incertidumbre.</li>
    <li>Confunde signos que se hacen parecido, como "cuidar" con "curar".</li>
    <li>Sensible a la iluminacion, el encuadre y la camara. Funciona mejor de frente.</li>
  </ul>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
