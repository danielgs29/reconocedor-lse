# Ficha del modelo

Un resumen honesto de qué hace el modelo, con qué datos se hizo, cómo de bien funciona y,
sobre todo, qué no hace. En el mundo profesional a esto se le llama ficha del modelo o model
card, y sirve para no prometer de más y para que cualquiera entienda sus límites.

## Qué es

Dos reconocedores que funcionan en el navegador a partir de la cámara:

- Un reconocedor de signos de la Lengua de Signos Española, de un vocabulario de 64 signos del
  ámbito de la salud (dolor, fiebre, hospital, cita, y similares).
- Un reconocedor del abecedario dactilológico, es decir, deletrear con la mano, que cubre 19
  letras estáticas.

No traduce la lengua de signos. Reconoce signos sueltos, uno a uno, no frases con gramática.

## Para qué sirve

Es una herramienta de accesibilidad y de aprendizaje. Ayuda a practicar signos y letras, y
permite componer mensajes sencillos signo a signo. No es una herramienta clínica, ni sustituye
a un intérprete de lengua de signos.

## Con qué datos y cómo se hizo

- Los signos vienen del conjunto de datos SWL-LSE, del que se seleccionaron los 64 conceptos
  que tenían al menos 35 grabaciones, uniendo variantes del mismo concepto.
- De cada grabación no se guarda el vídeo, sino los puntos de la mano y el cuerpo que detecta
  MediaPipe. Sobre esa secuencia de puntos trabaja el modelo, una red de atención (transformer).
- El modelo parte de un preentrenamiento con signos americanos (ASL). Ese paso es lo que más
  mejora el resultado, como se ve en la comparación de modelos.

## Cómo de bien funciona

Medido sobre el conjunto de prueba, grabaciones que el modelo no vio al entrenar:

- Acierto en signos: 90,5% (148 grabaciones de prueba).
- Acierto entre las tres opciones más probables: 96,6%.
- Puntuación media por signo (F1): 0,89.
- Abecedario: 98,3% en las 19 letras estáticas.

## Límites y avisos

- Vocabulario cerrado: solo 64 signos, todos del ámbito de la salud. Cualquier signo fuera de
  esa lista no se reconoce.
- Abecedario incompleto: 19 letras. Faltan las que llevan movimiento (por ejemplo J, Ñ, Z, y
  las dobles), porque el reconocedor de letras trabaja con la mano quieta.
- Conjunto de prueba pequeño: hay pocos ejemplos por signo, a veces solo dos. Por eso las
  cifras de un signo concreto tienen bastante incertidumbre, aunque la media global es sólida.
- Techo marcado por los datos: hacer el modelo más grande no mejora el resultado, incluso lo
  empeora. Lo que falta son más datos, no más capacidad.
- Confunde signos que se hacen de forma parecida. El caso más claro es "cuidar" con "curar".
- Sensible a las condiciones: iluminación, encuadre, distancia y calidad de la cámara. Funciona
  mejor de frente y con la persona bien visible.
- Puede generalizar peor a personas o estilos distintos de los que aparecen en los datos de
  entrenamiento.

## Privacidad

Todo el reconocimiento ocurre en el dispositivo. La imagen de la cámara no se envía a ningún
servidor.
