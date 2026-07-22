# Memoria del proyecto. Signia, reconocedor de Lengua de Signos Española

Proyecto final del máster de Inteligencia Artificial.

Aplicación en vivo: https://danielgs29.github.io/reconocedor-lse/

---

## 1. Resumen

Signia es una aplicación web que reconoce signos de la Lengua de Signos Española, la LSE, a
partir de la imagen de una cámara, y funciona entera en el navegador. Reconoce 64 signos del
ámbito de la salud y el abecedario dactilológico de 19 letras, y muestra el significado en
español, inglés o francés. El modelo de signos acierta un 90,5% sobre datos que no vio al
entrenar, y el de abecedario un 98,3%. Todo el reconocimiento ocurre en el dispositivo, así que
la imagen de la cámara no sale de él. La aplicación está publicada con despliegue automático, y
el desarrollo siguió prácticas de seguimiento de experimentos y evaluación con rigor.

---

## 2. Introducción y problema

Las personas sordas que se comunican en lengua de signos encuentran barreras cuando la otra
persona no signa. Este proyecto no pretende sustituir a un intérprete ni traducir la lengua de
signos entera, que es un problema abierto y muy difícil. Se centra en una pieza concreta y
alcanzable: reconocer signos aislados de un vocabulario acotado, y hacerlo de forma accesible,
en el navegador, sin coste ni instalación.

Se eligió el ámbito de la salud porque es un contexto donde la comunicación clara importa mucho
y donde un vocabulario reducido ya resulta útil: dolor, fiebre, hospital, cita, y similares. La
aplicación sirve a dos públicos: personas que aprenden LSE y quieren practicar, y personas
sordas que quieren componer mensajes sencillos para alguien que no signa.

---

## 3. Objetivos

- Reconocer un vocabulario de signos de LSE a partir de la cámara, con acierto suficiente para
  ser útil.
- Añadir el abecedario dactilológico para poder deletrear más allá del vocabulario cerrado.
- Que funcione entero en el navegador, sin servidor, para que sea accesible y respete la
  privacidad.
- Mostrar el significado en varios idiomas, pensando en la comunicación entre países.
- Evaluar el modelo con rigor y dejar constancia honesta de sus límites.
- Publicar la aplicación con un proceso de despliegue automático.

---

## 4. Datos

Se utiliza el conjunto SWL-LSE, publicado en Zenodo con licencia de uso abierto. En lugar de
vídeos, el conjunto proporciona los puntos de las manos y el cuerpo que detecta la librería
MediaPipe. Cada fotograma se describe con 61 puntos: 19 del cuerpo y 21 de cada mano. Trabajar
con puntos, y no con imágenes, hace el problema más manejable y protege la privacidad, porque no
se guarda la cara ni la apariencia de nadie.

De todo el conjunto se seleccionaron los conceptos con al menos 35 grabaciones, uniendo las
variantes de un mismo concepto, lo que dio un vocabulario de 64 signos. Se probó a ampliarlo,
pero con menos ejemplos por signo el modelo empeoraba, así que 64 fue el punto de equilibrio
entre tamaño de vocabulario y calidad.

Para el abecedario se grabó y procesó material propio de las 19 letras que se hacen con la mano
estática.

---

## 5. Método

### 5.1 Extracción de puntos con MediaPipe

MediaPipe es una librería que, dada una imagen, localiza las articulaciones de las manos y el
cuerpo. De cada fotograma se obtiene esa lista de puntos, cada uno con tres coordenadas: dos de
posición en el plano y una de profundidad. La imagen se voltea horizontalmente para que
coincida con la orientación de los datos de entrenamiento.

### 5.2 Preparación y características

Los puntos en crudo dependen de dónde esté la persona y de su tamaño en la imagen. Para que al
modelo le dé igual, se normalizan tomando los hombros como referencia. Cada signo se lleva a una
longitud fija de 56 fotogramas, recortando o rellenando, porque el modelo necesita entradas del
mismo tamaño. Además de la posición, se añade la velocidad, es decir, cuánto se mueve cada punto
de un fotograma al siguiente, que ayuda a distinguir signos parecidos en postura pero distintos
en movimiento. Todo se aplana a 366 valores por fotograma.

### 5.3 Arquitectura del modelo

El modelo es un transformer, una red basada en el mecanismo de atención, que pesa qué
fotogramas de la secuencia importan más para decidir el signo. Es una red compacta, de unos
94.000 parámetros. Se comparó con una red recurrente, un tipo de red pensada para secuencias, y
el transformer dio mejores resultados, así que fue la elección.

### 5.4 Entrenamiento

Para aprovechar mejor los pocos datos se usaron tres técnicas:

- Aumento de datos. Se crean variantes de cada grabación rotándola, escalándola y añadiendo un
  poco de ruido, con cuidado de no alterar los puntos que faltan. Así el modelo ve más
  variedad y generaliza mejor.
- Preentrenamiento y transferencia. El modelo parte de haber aprendido antes con un conjunto
  grande de signos americanos. Sobre esa base se ajusta a los signos españoles. Este paso es el
  que más mejora el resultado.
- Buenas prácticas de optimización. Se usó el optimizador AdamW con un calentamiento inicial del
  ritmo de aprendizaje seguido de un descenso suave, y un recorte de gradiente para estabilizar
  el entrenamiento.

### 5.5 Calibración de la confianza y umbral

Un modelo suele ser demasiado confiado: dice estar 95% seguro cuando en realidad acierta menos.
Para corregirlo se aplica un ajuste por temperatura, un único número que hace la confianza más
sincera. Además se fija un umbral por debajo del cual la aplicación prefiere decir "no lo tengo
claro" antes que arriesgar una respuesta dudosa. Los valores se calcularon con el conjunto de
validación y se guardaron para que la aplicación los use.

### 5.6 Reconocedor de abecedario

Una letra dactilológica es sobre todo una postura de la mano quieta, no un movimiento. Por eso
se usa un modelo pequeño y aparte que mira un solo fotograma: toma los 21 puntos de una mano,
los normaliza respecto a la muñeca y a su tamaño, y decide la letra. Los ejemplos se duplican en
espejo, porque una letra es la misma con la mano derecha o la izquierda. Cubre 19 letras
estáticas; faltan las que llevan movimiento, como la J o la Z.

---

## 6. Resultados y evaluación

Todas las cifras se miden sobre el conjunto de prueba, grabaciones que el modelo no vio al
entrenar, que es el número honesto.

- Acierto en signos: 90,5% sobre 148 grabaciones. Entre las tres opciones más probables, 96,6%.
- Acierto en abecedario: 98,3%.
- Puntuación media por signo, que combina precisión y cobertura: 0,90.
- Calibración: el error de calibración baja de 0,058 a 0,025 con el ajuste por temperatura, lo
  que indica que la confianza declarada se acerca al acierto real.

El diagnóstico por signo se calculó sobre validación y prueba juntas, porque con solo prueba hay
muy pocos ejemplos por signo. La matriz de confusión reveló que el modelo confunde signos que se
hacen de forma parecida; el caso más claro es cuidar con curar. Los signos con menos ejemplos
son los que peor se reconocen, lo que es esperable.

Comparación de modelos, todos medidos sobre el mismo conjunto de prueba y registrada en MLflow:

| Modelo | Preentrenamiento | Acierto |
|---|---|---|
| Transformer preentrenado con signos americanos (desplegado) | ASL | 90,5% |
| Transformer sin preentrenar | ninguno | 83,1% |
| Transformer preentrenado con signos argentinos | LSA64 | 82,4% |
| Transformer más grande, sin preentrenar | ninguno | 81,1% |

La lectura es doble: el preentrenamiento con signos americanos es lo que da el salto, y
agrandar el modelo lo empeora. Ambas cosas apuntan a que el techo lo marcan los datos
disponibles, no la capacidad del modelo.

---

## 7. La aplicación

La aplicación funciona entera en el navegador. En cada fotograma, MediaPipe extrae los puntos,
que se dibujan sobre la imagen, y el modelo, convertido a un formato ligero con LiteRT.js, hace
el reconocimiento. Si el navegador tiene tarjeta gráfica compatible se usa; si no, se recurre al
procesador.

Tiene dos modos, y dentro de cada uno se puede trabajar con signos o con el abecedario:

- Aprender. La persona elige un signo o una letra, ve cómo se hace e intenta imitarlo. La
  aplicación le dice si lo ha hecho bien.
- Comunicar. La persona signa y la aplicación escribe lo reconocido, en español, inglés o
  francés. Con el abecedario se deletrea letra a letra.

El modelo solo devuelve un número de signo; es la interfaz la que elige en qué idioma mostrarlo,
gracias a una lista de vocabulario con los nombres en los tres idiomas. Añadir un idioma no
requiere tocar el modelo.

Para que el uso se sienta fiable, el abecedario confirma una letra solo cuando se mantiene
estable un instante, con un anillo que se rellena, evitando el parpadeo y las letras coladas. Y
los errores de arranque, como la falta de cámara o el permiso denegado, se explican con
mensajes claros.

---

## 8. Seguimiento de experimentos y despliegue

El desarrollo usó MLflow para registrar los experimentos de entrenamiento. La comparación final
de modelos se registró de nuevo en MLflow midiendo cada modelo sobre el mismo conjunto de
prueba, de modo que sea reproducible.

La aplicación se publica en GitHub Pages mediante un flujo de integración y despliegue continuo
con GitHub Actions. Cada cambio subido a la rama principal pasa por unas comprobaciones
automáticas, que revisan el código y la presencia de los archivos necesarios, y solo si las
supera se publica la carpeta de la web. Como la aplicación no necesita servidor y Pages sirve
por conexión segura, la cámara funciona sin problemas.

---

## 9. Límites y trabajo futuro

- Vocabulario cerrado de 64 signos del ámbito de la salud. Fuera de esa lista no reconoce.
- Abecedario de 19 letras; faltan las que llevan movimiento.
- Conjunto de prueba pequeño, con pocos ejemplos por signo, lo que da incertidumbre a las cifras
  de un signo concreto, aunque la media global es sólida.
- Techo marcado por los datos: más capacidad no mejora, faltan más grabaciones.
- Sensible a la iluminación, el encuadre y la cámara; funciona mejor de frente.
- No es un traductor de LSE: reconoce signos aislados, no frases con gramática.

Como trabajo futuro: ampliar el vocabulario con más datos, cubrir las letras con movimiento,
detectar automáticamente el inicio y el fin del signo, y explorar el camino inverso de texto a
signo.

---

## 10. Conclusiones

El proyecto cumple sus objetivos: reconoce signos de LSE y el abecedario en el navegador, con un
acierto útil, en varios idiomas, respetando la privacidad, publicado con despliegue automático y
evaluado con honestidad. Más allá del resultado, deja claro el porqué de cada decisión: por qué
un transformer, por qué el preentrenamiento, por qué el techo es de datos, y qué no hace la
herramienta. Ese entendimiento, y no solo el número de acierto, es lo que sostiene el proyecto.

---

## 11. Referencias y créditos

- SWL-LSE, conjunto de datos de Lengua de Signos Española. Publicado en Zenodo,
  https://zenodo.org/records/13691887 (DOI 10.5281/zenodo.13691887). Se utiliza con fin
  educativo y se reconoce a sus autores, conforme a su licencia de atribución.
- MediaPipe, librería de detección de puntos de manos y cuerpo.
- LiteRT.js, motor de ejecución de modelos en el navegador, evolución de TensorFlow.js.
- MLflow, seguimiento de experimentos. GitHub Actions y GitHub Pages, automatización y
  alojamiento.
- Conjuntos usados para el preentrenamiento: signos americanos y signos argentinos (LSA64).
