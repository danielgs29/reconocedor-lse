# Signia. Reconocedor de Lengua de Signos Española

Proyecto final del máster de IA. Es una aplicación web que reconoce signos de la Lengua de
Signos Española, abreviada como LSE, a partir de la imagen de una cámara. Funciona en el
navegador del móvil o del ordenador, no necesita instalación y todo el reconocimiento ocurre
en el propio dispositivo, así que la imagen de la cámara no sale de él.

**Aplicación en vivo: https://danielgs29.github.io/reconocedor-lse/**

## Qué hace

La aplicación tiene dos modos, y dentro de cada uno se puede trabajar con signos completos o
con el abecedario dactilológico, que es deletrear palabras con la mano letra a letra.

- Modo aprender. La persona elige un signo o una letra, ve cómo se hace e intenta imitarlo
  frente a la cámara. La aplicación le dice si lo ha hecho bien.
- Modo comunicar. La persona signa y la aplicación va escribiendo lo que reconoce. El
  significado se puede mostrar en español, inglés o francés. Con el abecedario se puede
  deletrear letra a letra.

El reconocedor de signos cubre 64 signos del ámbito de la salud. El del abecedario cubre 19
letras estáticas, las que se hacen con la mano quieta.

## Cómo funciona por dentro

De cada fotograma de la cámara, la librería MediaPipe extrae la posición de las manos y el
cuerpo, es decir, unos puntos, no la imagen. Sobre la secuencia de puntos de un signo trabaja
el modelo, una red de atención llamada transformer. El modelo se entrena aparte y luego se
convierte a un formato ligero, con LiteRT.js, que es lo que permite ejecutarlo dentro del
navegador sin servidor. El abecedario usa un modelo pequeño que clasifica la forma de la mano
en cada momento.

Hay una explicación más detallada del montaje en ARQUITECTURA.md, y el diario de desarrollo,
día a día, está fuera del repositorio.

## Resultados

Medido sobre el conjunto de prueba, grabaciones que el modelo no vio al entrenar:

- Signos: 90,5% de acierto. Entre las tres opciones más probables, 96,6%.
- Abecedario: 98,3% en las 19 letras estáticas.

La evaluación completa, con la matriz de confusión, el acierto por signo, la calibración de la
confianza y la comparación entre modelos, está en la carpeta `evaluacion`, incluido un informe
visual en `evaluacion/informe.html`.

## Cómo verla en local

Desde esta carpeta:

```
python3 src/servidor.py
```

Y abrir la dirección que indique, permitiendo el acceso a la cámara. El servidor no usa caché,
así que los cambios se ven al recargar.

## Despliegue

La aplicación se publica sola en GitHub Pages. Cada vez que se sube un cambio a la rama
principal, GitHub Actions comprueba el código y publica la carpeta `web`. El flujo está en
`.github/workflows/deploy.yml`.

## Herramientas y coste

El proyecto no tiene ningún coste. El modelo se entrena con tarjetas gráficas gratuitas, y se
ejecuta dentro del navegador con LiteRT.js, la evolución de TensorFlow.js para páginas web, de
modo que no hace falta servidor. El seguimiento de los experimentos de entrenamiento se lleva
con MLflow, la automatización con GitHub Actions, y los datos provienen de SWL-LSE.

## Datos y créditos

Los datos no se incluyen en el repositorio, porque SWL-LSE ocupa alrededor de 3,5 gigabytes.
Se descargan desde Zenodo, en https://zenodo.org/records/13691887, y se colocan en la carpeta
`data`, que git no sube por estar excluida.

El conjunto SWL-LSE se publica con licencia de uso abierto que exige dar crédito. Este proyecto
lo utiliza con ese fin educativo y reconoce a sus autores. La referencia completa se incluye en
la memoria del proyecto.
