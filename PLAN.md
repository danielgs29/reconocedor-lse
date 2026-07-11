# Plan de 25 días. Reconocedor de Lengua de Signos Española

Proyecto final del máster de IA. Daniel Gómez.

## Resumen

El proyecto es una aplicación web que reconoce signos de la Lengua de Signos Española, a
la que llamaremos LSE, a partir de la imagen de una cámara. Funciona en el navegador del
móvil o del ordenador y no necesita instalación.

La aplicación tiene dos funciones que se apoyan en un mismo modelo de reconocimiento:

1. Modo aprendizaje. La aplicación muestra una palabra, la persona la signa frente a la
   cámara y la aplicación le dice si lo ha hecho bien y lleva la cuenta de su progreso.
2. Modo comunicación. La aplicación reconoce los signos de forma continua y los va
   convirtiendo en texto. El vocabulario se centra en el ámbito sanitario, que es donde la
   barrera de comunicación con una persona sorda es más crítica.

La idea central es que un único modelo alimenta las dos funciones. El trabajo de
inteligencia artificial es el mismo para las dos; lo único que cambia es qué se hace
después con el resultado. Por eso hacer las dos funciones no duplica el esfuerzo del
modelo, solo el de la interfaz.

### Por qué este proyecto se sostiene

- Impacta en la demostración. Se puede enseñar funcionando en directo con la cámara.
- Tiene trabajo serio detrás. Hay que entrenar un modelo que entiende secuencias de
  movimiento, validarlo con rigor y desplegarlo.
- Es original. Casi toda la tecnología de reconocimiento de signos existente está hecha
  para la lengua de signos americana, no para la española.
- Tiene un motivo claro. Para una parte del colectivo sordo, el español escrito es una
  segunda lengua con la que no siempre se maneja con soltura, y su lengua natural es la
  LSE.
- Encaja con el máster. Toca aprendizaje profundo, es decir, redes neuronales que aprenden
  de los datos, y prácticas de MLOps como el seguimiento de experimentos, el despliegue y
  la evaluación.

## Datos

Un modelo aprende a partir de ejemplos, así que lo primero es tener datos. Usaremos tres
fuentes.

| Fuente | Qué es | Para qué la usamos | Cómo se obtiene |
|---|---|---|---|
| SWL-LSE | 300 signos del ámbito sanitario, 8.000 ejemplos grabados, con los puntos clave del cuerpo ya extraídos, hechos por 124 personas distintas | Fuente principal de entrenamiento | Descarga directa y gratuita desde Zenodo, con licencia de uso abierto |
| Sign4all | 24 signos de la vida cotidiana, cerca de 7.756 vídeos | Refuerzo opcional | Público |
| Grabaciones propias | Daniel signando frente a la cámara | Demostración en directo y prueba de que el modelo funciona con una persona nueva | Se graban durante el proyecto |

Aquí conviene explicar un término. Un punto clave, o keypoint, es la posición de una parte
del cuerpo en la imagen, por ejemplo la punta de un dedo o una muñeca. En lugar de trabajar
con la imagen completa, trabajamos con la lista de posiciones de las manos y el cuerpo en
cada instante. SWL-LSE ya trae esos puntos calculados, lo que nos ahorra mucho trabajo.

Una advertencia importante sobre los datos. Si repartimos 8.000 ejemplos entre 300 signos,
salen unos 27 ejemplos por signo, que es poco para que un modelo aprenda bien tantas
clases distintas. La solución es empezar con un vocabulario más pequeño, de unos 40 a 60
signos, eligiendo los que tienen más ejemplos. Dejamos como mejora futura ampliarlo a los
300. Además usaremos aumento de datos, una técnica que genera variaciones de los ejemplos
que ya tenemos para que el modelo vea más casos.

## Cómo funciona por dentro

El recorrido de la información, desde la cámara hasta el resultado, es el siguiente.

1. La cámara del navegador capta la imagen.
2. Una herramienta llamada MediaPipe localiza en cada fotograma los puntos clave de las
   manos y el cuerpo. MediaPipe es una librería de Google que hace este trabajo y que
   funciona incluso dentro del navegador.
3. Se van guardando los puntos de los últimos fotogramas para formar la secuencia de
   movimiento de un signo.
4. El modelo recibe esa secuencia y decide qué signo es, junto con un número de confianza
   que indica cómo de seguro está.
5. Según el modo elegido, ese resultado se usa para corregir al usuario o para mostrar el
   texto.

El modelo se ejecuta dentro del propio navegador gracias a TensorFlow.js, que es la versión
de la librería TensorFlow preparada para funcionar en páginas web. Esto tiene una
consecuencia buena: no hace falta ningún servidor, así que no hay coste ni espera por la
red.

Un punto de método que marca la calidad del proyecto es cómo se separan los datos para
evaluar el modelo. Lo explicamos más abajo en la fase correspondiente.

## Coste del proyecto: 0 euros

El proyecto no necesita ninguna cuenta de pago. Cada necesidad se cubre con una herramienta
gratuita.

| Necesidad | Herramienta gratuita |
|---|---|
| Entrenar el modelo | Google Colab o Kaggle, que ofrecen tarjetas gráficas gratis |
| Guardar el registro de experimentos | MLflow en local, o DagsHub que lo ofrece alojado y gratis |
| Alojar la aplicación web | GitHub Pages, Netlify, Vercel, Cloudflare Pages o Hugging Face Spaces |
| Ejecutar el modelo | En el navegador, sin servidor que pagar |
| Automatizar pruebas y despliegue | GitHub Actions, gratis en repositorios públicos |
| Datos | SWL-LSE desde Zenodo, descarga gratuita |

El motivo de que salga gratis es que el modelo se ejecuta en el navegador del usuario, lo
que elimina de raíz el gasto de servidor.

## Calendario de 25 días

El plan se divide en cinco semanas. Cada semana termina con un resultado concreto.

### Semana 1. Días 1 a 5. Preparar la base y los datos

- Día 1. Crear el proyecto, preparar el entorno de trabajo con la herramienta uv, ordenar
  las carpetas y descargar los datos de SWL-LSE.
- Día 2. Explorar los datos. Ver cuántos ejemplos hay por signo y por persona, y elegir el
  vocabulario de trabajo con los signos mejor representados.
- Día 3. Construir el proceso que prepara los datos. Esto incluye normalizar los puntos
  clave, es decir, ponerlos todos en una misma escala, y fijar una duración común para las
  secuencias. También se define aquí la separación de los datos por persona, que se explica
  en la Semana 2.
- Día 4. Entrenar un primer modelo sencillo de principio a fin. Aunque sea básico, sirve
  para tener una referencia de partida y comprobar que todo el proceso funciona. A esa
  referencia inicial se le llama baseline.
- Día 5. Aplicar el aumento de datos y empezar a registrar los experimentos con MLflow, que
  es una herramienta que guarda qué se probó y qué resultados dio, para poder comparar.
- Resultado de la semana: el proceso de datos funciona y hay una primera medida de
  referencia honesta.

### Semana 2. Días 6 a 10. El modelo serio

- Días 6 y 7. Construir un modelo mejor. Empezamos con una red que entiende secuencias, y
  probamos también un Transformer, que es un tipo de red muy eficaz para datos en orden
  temporal. Se ajustan sus parámetros y se comparan resultados con MLflow.
- Día 8. Comparar los modelos probados y analizar los errores. Se estudia qué signos se
  confunden entre sí con una matriz de confusión, que es una tabla que muestra en qué se
  equivoca el modelo.
- Día 9. Mejorar el modelo. Se reduce el sobreajuste, que ocurre cuando el modelo memoriza
  los ejemplos en vez de aprender de verdad, y se calibra la confianza para que el modo
  comunicación pueda decir no lo sé cuando no está seguro.
- Día 10. Fijar la primera versión del modelo y evaluarla a fondo con varias medidas de
  acierto.
- Resultado de la semana: un modelo sólido, evaluado con honestidad y con sus errores
  analizados.

Aquí explicamos el punto de método más importante del proyecto. Para evaluar el modelo hay
que separar los datos en tres grupos: uno para entrenar, uno para ajustar y uno para la
prueba final. La forma correcta de hacer esta separación es por persona, de modo que
ninguna persona aparezca en más de un grupo. Si no se hace así, el modelo puede memorizar
la forma de signar de cada persona y dar una nota alta que no refleja la realidad, porque
en el uso real se enfrentará a personas que nunca ha visto. Separar por persona da una nota
más baja pero honesta, y es justo lo que demuestra rigor ante un tribunal.

### Semana 3. Días 11 a 15. Llevar el modelo al navegador

- Día 11. Convertir el modelo al formato de TensorFlow.js y comprobar que da los mismos
  resultados que antes de convertirlo.
- Día 12. Montar la estructura de la aplicación web y conseguir que MediaPipe capte los
  puntos clave de la cámara en tiempo real.
- Día 13. Unir las piezas para que la aplicación reconozca signos en directo.
- Día 14. Resolver cuándo empieza y cuándo termina un signo dentro del movimiento continuo.
  Si esto resulta difícil, el plan alternativo es usar un botón que la persona pulsa para
  indicar que va a signar.
- Día 15. Convertir la web en una aplicación instalable en el móvil y probarla en el
  teléfono. Una aplicación web instalable de este tipo se conoce como PWA.
- Resultado de la semana: una aplicación web que reconoce signos en directo en el móvil.

### Semana 4. Días 16 a 20. Las dos funciones

- Días 16 y 17. Construir el modo aprendizaje, con el recorrido completo de una lección:
  mostrar la palabra, recoger el signo, dar la corrección y llevar la puntuación.
- Días 18 y 19. Construir el modo comunicación, con el reconocimiento continuo que va
  formando texto, centrado en el vocabulario sanitario.
- Día 20. Grabar las muestras propias para la demostración y comprobar que el modelo
  funciona con una persona nueva. Pulir las dos funciones. Este es el punto de decisión: si
  el tiempo aprieta, aquí se decide recortar una función para dejar la otra bien terminada.
  Es preferible una función redonda que dos a medias.
- Resultado de la semana: las dos funciones en marcha.

### Semana 5. Días 21 a 25. Despliegue, memoria y presentación

- Día 21. Publicar la aplicación en un alojamiento gratuito y montar la automatización
  básica de pruebas y despliegue con GitHub Actions.
- Día 22. Evaluación final y documentación de las medidas, los objetivos de calidad y las
  limitaciones.
- Días 23 y 24. Redactar la memoria: el problema, los datos, el método con la separación
  por persona, los resultados honestos, las limitaciones, la ética y el trabajo futuro.
- Día 25. Preparar la presentación y ensayar la demostración en directo, cuidando la luz y
  el fondo. Se prepara también un vídeo grabado por si la cámara falla en la sala.
- Resultado final: proyecto publicado, memoria escrita y presentación ensayada.

## Riesgos y planes alternativos

| Riesgo | Qué hacemos si ocurre |
|---|---|
| Pocos ejemplos por signo | Reducir el vocabulario a 40 o 60 signos y usar aumento de datos |
| Detectar el inicio y el fin del signo en directo resulta difícil | Usar un botón para pulsar antes de signar |
| La conversión del modelo al navegador falla | Servir el modelo desde Hugging Face Spaces, que es gratuito |
| Las dos funciones quedan a medias | Aplicar el punto de decisión del Día 20 y priorizar una |
| La demostración en directo falla en la sala | Tener preparado un vídeo grabado de respaldo |
| El modelo no funciona bien con Daniel | Grabar sus muestras pronto y reentrenar si hace falta |

## Regla principal

El orden manda. Primero un modelo sólido al final de la Semana 2, luego la aplicación web
en la Semana 3, y por último las dos funciones en la Semana 4. Si falta tiempo, lo primero
que se recorta es la segunda función, nunca la calidad del modelo.

## Cita obligatoria de los datos

La licencia de SWL-LSE exige dar crédito. En la memoria se incluirá la referencia al
conjunto de datos SWL-LSE publicado en Zenodo, con el identificador
10.5281/zenodo.13691887, y a Sign4all si finalmente se usa.
