# Reconocedor de Lengua de Signos Española

Proyecto final del máster de IA. Es una aplicación web que reconoce signos de la Lengua de
Signos Española, abreviada como LSE, a partir de la imagen de una cámara. Funciona en el
navegador del móvil o del ordenador y no necesita instalación.

La aplicación tiene dos funciones que se apoyan en un mismo modelo de reconocimiento.

- Modo aprendizaje. La aplicación muestra una palabra, la persona la signa frente a la
  cámara y la aplicación le dice si lo ha hecho bien.
- Modo comunicación. La aplicación reconoce los signos de forma continua y los va
  convirtiendo en texto, con un vocabulario centrado en el ámbito sanitario.

## Documentación

- PLAN.md contiene el plan de 25 días, con el calendario, los riesgos y los planes
  alternativos.
- ARQUITECTURA.md explica cómo está montado el proyecto y por qué se ha decidido así, con
  diagramas.

## Herramientas y coste

El proyecto no tiene ningún coste. El modelo se entrena en Google Colab o Kaggle, que
ofrecen tarjetas gráficas gratuitas, y se ejecuta dentro del navegador con TensorFlow.js,
que es la versión de la librería TensorFlow preparada para páginas web. Esto último
significa que no hace falta ningún servidor. El seguimiento de experimentos se lleva con
MLflow, la automatización con GitHub Actions y los datos provienen de SWL-LSE, publicado en
Zenodo con licencia de uso abierto.

## Datos

Los datos no se incluyen en el repositorio, porque SWL-LSE ocupa alrededor de 3,5
gigabytes. Se descargan desde Zenodo, en la dirección https://zenodo.org/records/13691887,
y se colocan en la carpeta data, que git no sube por estar excluida.
