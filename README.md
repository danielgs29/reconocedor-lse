# Reconocedor de Lengua de Signos Española (LSE)

Proyecto final del máster de IA. Web app que reconoce signos de LSE en tiempo real desde
el navegador, con dos funciones sobre un mismo modelo:

- **Modo aprendizaje** — muestra una palabra, la signas y la app te corrige.
- **Modo comunicación** — reconocimiento continuo signo → texto (vocabulario sanitario).

## Documentación

- [PLAN.md](PLAN.md) — plan de 25 días con calendario, riesgos y planes B.
- [ARQUITECTURA.md](ARQUITECTURA.md) — decisiones arquitectónicas (ADR) y diagramas.

## Stack (coste 0 €)

Modelo temporal sobre keypoints de MediaPipe · TensorFlow / PyTorch · TensorFlow.js
(inferencia en el navegador) · MLflow · GitHub Actions · datos: SWL-LSE (Zenodo, CC-BY 4.0).

## Datos

Los datos **no** se incluyen en el repositorio (SWL-LSE pesa ~3,5 GB). Descargar desde
Zenodo: https://zenodo.org/records/13691887 y colocar en `data/` (ignorado por git).
