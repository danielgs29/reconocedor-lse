# Plan de 25 días — Reconocedor de LSE (Lengua de Signos Española)

**Proyecto final del máster de IA · Daniel Gómez**

## Resumen ejecutivo

Web app que reconoce signos de **Lengua de Signos Española** en tiempo real desde el
navegador del móvil, con **dos funciones sobre un mismo modelo**:

1. **Modo aprendizaje** ("Duolingo de LSE"): muestra una palabra, la signas, la app te
   corrige y lleva tu progreso.
2. **Modo comunicación** (accesibilidad): reconocimiento continuo signo → texto, con
   vocabulario del ámbito **sanitario** (comunicación persona sorda ↔ personal médico).

**Principio rector:** un solo modelo temporal alimenta las dos funciones. El ML es
compartido; las dos funciones solo cambian la interfaz. El modelo tiene que estar sólido
antes de tocar la segunda función.

### Por qué es defendible
- **Wow:** demo en vivo con la webcam, funciona en el móvil.
- **Trabajo serio:** modelo temporal sobre secuencias de keypoints, validación
  signer-independent, evals honestas, despliegue.
- **Original:** en español (casi toda la tecnología es de ASL americana).
- **Para qué:** el español escrito es una barrera para parte del colectivo sordo;
  el vocabulario sanitario es donde la barrera es crítica.
- **Encaje con el máster:** DL (modelo temporal), MLOps (pipeline, MLflow, despliegue,
  CI), evals y producto.

---

## Datos

| Dataset | Qué es | Uso | Acceso |
|---|---|---|---|
| **SWL-LSE** (Zenodo, DOI 10.5281/zenodo.13691887) | 300 signos sanitarios, 8.000 muestras, **keypoints MediaPipe ya extraídos**, 124 signantes | **Base principal** | CC-BY 4.0, descarga directa |
| **Sign4all** (Nature Sci. Data) | 24 signos cotidianos, ~7.756 vídeos RGB | Refuerzo opcional | Público |
| **Grabaciones propias** | Tú signando, vía webcam | Demo en vivo + test de generalización | Las generas tú |

**Nota técnica importante:** 8.000 muestras / 300 clases ≈ **27 por clase** (poco).
→ Mitigación: trabajar con un **vocabulario acotado** de los ~40-60 signos mejor
representados para un modelo robusto, y dejar "escalar a 300" como línea futura.
Data augmentation de keypoints para engordar las clases.

---

## Arquitectura técnica

```
Webcam (navegador)
   │
   ▼
MediaPipe Tasks JS  ──► keypoints (pose + manos) por frame
   │
   ▼
Buffer de secuencia (ventana deslizante) en el navegador
   │
   ▼
Modelo temporal (TensorFlow.js, en el navegador)  ──► predicción de signo + confianza
   │
   ├──► Modo aprendizaje:  ¿coincide con el signo objetivo? → feedback ✅/❌ + progreso
   └──► Modo comunicación: stream de texto (con umbral de confianza)
```

- **Modelo:** baseline LSTM/GRU → **Transformer temporal** (el que dé mejor eval).
- **Inferencia en el navegador** con TensorFlow.js (sin latencia de red **y sin coste de
  servidor** — la app son archivos estáticos).
  Plan B: servir el modelo como API en un espacio gratuito (Hugging Face Spaces).
- **Validación signer-independent** (train/val/test partidos por signante — ningún
  signante en dos splits). Es *el* punto de rigor, análogo al group-by-patient.

---

## Coste: 0 € (sin cuenta AWS)

| Necesidad | Herramienta gratuita |
|---|---|
| Entrenar el modelo | Google Colab / Kaggle Notebooks (GPU gratis) |
| Trackear experimentos | MLflow local, o DagsHub (hosted gratis) |
| Alojar la web app | GitHub Pages / Netlify / Vercel / Cloudflare Pages / HF Spaces |
| Inferencia | En el navegador (TF.js) → sin servidor que pagar |
| CI/CD | GitHub Actions (gratis en repos públicos) |
| Datos | SWL-LSE (Zenodo, descarga directa gratuita) |

La arquitectura client-side (modelo en el navegador) elimina el coste de servidor de raíz.

## Calendario (25 días)

### Semana 1 · Días 1-5 — Fundamentos y datos
- **D1:** Repo, entorno (uv/conda), estructura de carpetas, git. Descargar SWL-LSE.
  Leer paper y anotaciones.
- **D2:** EDA: muestras por signo y por signante, distribución. **Decidir el vocabulario
  de trabajo** (subset mejor representado). Entender formato pickle de keypoints.
- **D3:** Pipeline de datos: parseo, normalización de keypoints (centrar/escalar),
  longitud fija de secuencia (padding/truncado). **Split signer-independent.**
- **D4:** Baseline rápido (LSTM pequeño) end-to-end. Cerrar el circuito con un número
  base honesto, aunque sea malo.
- **D5:** Data augmentation de keypoints (jitter, rotación, escala, time-warp).
  Montar **MLflow** para trackear experimentos.
- **Entregable:** pipeline de datos + baseline con métrica signer-independent.

### Semana 2 · Días 6-10 — El modelo serio
- **D6-7:** Arquitectura buena (Transformer temporal / GRU bidireccional). Iterar
  hiperparámetros con MLflow.
- **D8:** Comparativa de arquitecturas + **análisis de errores** (matriz de confusión,
  qué signos se confunden).
- **D9:** Mejora: regularización, augmentation dirigida a signos difíciles,
  **calibración de confianza** (umbral "no sé" para el modo comunicación).
- **D10:** Congelar **modelo v1**. Eval suite: accuracy top-1/top-5, per-signer,
  per-class, matriz de confusión.
- **Entregable:** modelo sólido con evals honestas y análisis de errores.

### Semana 3 · Días 11-15 — Del modelo al navegador
- **D11:** Exportar a **TensorFlow.js**. Validar que las predicciones coinciden con Python.
- **D12:** Esqueleto web app: MediaPipe Tasks JS captura landmarks en vivo, visualización
  en canvas.
- **D13:** Conectar: buffer de keypoints → inferencia TF.js → **predicción en vivo**.
- **D14:** Segmentación temporal en vivo (cuándo empieza/acaba un signo: detección de
  reposo/movimiento, ventana deslizante, suavizado). **Plan B:** botón "pulsar para
  signar" si la segmentación continua da guerra.
- **D15:** PWA instalable en móvil, responsive, probar en tu teléfono.
- **Entregable:** web app que reconoce signos en vivo en el móvil.

### Semana 4 · Días 16-20 — Las dos funciones
- **D16-17:** **Modo aprendizaje**: flujo de lección (palabra → signas → feedback →
  puntuación/racha), UI, progreso local.
- **D18-19:** **Modo comunicación**: reconocimiento continuo → stream de texto, enfoque
  sanitario, umbral de confianza.
- **D20:** Grabar tu mini-set propio para la demo (test de generalización a signante
  nuevo). Pulir UX de ambos modos. **← PUNTO DE CORTE:** si vas justo, aquí se decide
  qué modo se recorta (dejar uno redondo > dos a medias).
- **Entregable:** las dos funciones operativas.

### Semana 5 · Días 21-25 — MLOps, memoria y presentación
- **D21:** Despliegue **gratuito**: web app estática + modelo TF.js en GitHub Pages /
  Netlify / Vercel / Cloudflare Pages / Hugging Face Spaces. CI básico (lint/test/build)
  con GitHub Actions (gratis en repos públicos).
- **D22:** Eval final + observabilidad: métricas documentadas, SLOs, limitaciones.
  Opcional: registrar modelo en MLflow registry (local o DagsHub gratis).
- **D23-24:** **Memoria**: problema, datos, metodología (validación signer-independent),
  resultados honestos, limitaciones, ética, trabajo futuro.
- **D25:** Presentación + **ensayo de la demo en vivo** (iluminación, fondo; **plan B con
  vídeo grabado** por si la webcam falla en la sala).
- **Entregable:** proyecto desplegado + memoria + presentación ensayada.

---

## Riesgos y planes B

| Riesgo | Mitigación / Plan B |
|---|---|
| Pocas muestras por clase (27) | Vocabulario acotado (40-60 signos) + augmentation |
| Segmentación temporal en vivo difícil | Botón "pulsar para signar" en vez de continuo |
| Conversión a TF.js falla | Servir modelo como API en Hugging Face Spaces (gratis) |
| Las dos funciones a medias | Punto de corte D20: priorizar una redonda |
| Demo en vivo falla en la sala | Vídeo grabado de respaldo |
| Modelo no generaliza a ti | Grabar tus muestras pronto (D20) y reentrenar si hace falta |

## Regla de oro
Primero el modelo sólido (fin semana 2), luego la web app (semana 3), luego las dos
funciones (semana 4). El segundo modo es lo primero que se recorta si el tiempo aprieta.
Nunca al revés.

## Cita obligatoria (SWL-LSE, licencia CC-BY)
Incluir en la memoria la atribución del dataset SWL-LSE (Zenodo, DOI
10.5281/zenodo.13691887) y de Sign4all si se usa.
