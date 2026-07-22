# Evaluacion del modelo de signos

Modelo evaluado: `models/transformer_pre_asl.keras`. Reconoce 64 signos.

Todas las cifras se miden sobre el conjunto de prueba, grabaciones que el modelo no vio al entrenar. Es el numero honesto.

## Acierto (conjunto de prueba)

- Grabaciones de prueba: 148
- Acierto: 90.5%
- Acierto entre las tres mejores opciones: 96.6%

El resto del diagnostico (calibracion, metricas por signo, matriz de confusion y umbral) se calcula sobre validacion mas prueba juntas, 420 grabaciones, porque con solo prueba hay muy pocos ejemplos por signo y las cifras salen ruidosas.

## Calibracion de la confianza

- Error de calibracion sin ajuste: 0.058
- Error de calibracion con temperatura 1.7: 0.025
- Mas cerca de cero es mejor. Ver `calibracion.png`.

## Signos que peor se reconocen

| Signo | Precision | Cobertura | F1 | Ejemplos |
|---|---|---|---|---|
| CUIDAR | 100% | 40% | 0.57 | 5 |
| VER^PROBAR | 75% | 50% | 0.60 | 6 |
| PROBAR | 56% | 83% | 0.67 | 6 |
| CURAR | 70% | 64% | 0.67 | 11 |
| NACER | 80% | 67% | 0.73 | 6 |
| CENTRO^VIVIR | 100% | 60% | 0.75 | 5 |
| AUXILIAR | 100% | 60% | 0.75 | 5 |
| APETECER | 100% | 60% | 0.75 | 5 |
| HERIDA | 100% | 67% | 0.80 | 6 |
| AGOTAMIENTO | 67% | 100% | 0.80 | 6 |

## Pares de signos que mas se confunden

| Veces | Signo real | Confundido con |
|---|---|---|
| 2 | VER^PROBAR | PROBAR |
| 2 | CURAR | ALCOHOL |
| 2 | CUIDAR | CURAR |
| 2 | AUXILIAR | PROBAR |
| 2 | APETECER | PULMON |
| 1 | VIRUS | OPERAR |
| 1 | VER^PROBAR | AGOTAMIENTO |
| 1 | PROBAR | FARMACIA |
| 1 | PIS | PIEL^CUERPO |
| 1 | OPERAR | OIR^MITAD |
| 1 | OPERAR | HOSPITAL |
| 1 | OPERAR | FIEBRE |

## Metricas de todos los signos

| Signo | Precision | Cobertura | F1 | Ejemplos |
|---|---|---|---|---|
| GRIPE | 100% | 100% | 1.00 | 6 |
| DOLOR-DE-CABEZA | 100% | 100% | 1.00 | 6 |
| URGENTE | 100% | 100% | 1.00 | 6 |
| DROGA | 100% | 100% | 1.00 | 6 |
| CORAZON | 100% | 100% | 1.00 | 6 |
| DIARREA | 100% | 100% | 1.00 | 6 |
| ENFERMO^CASA | 100% | 100% | 1.00 | 6 |
| GARGANTA | 100% | 100% | 1.00 | 6 |
| DORMIR | 100% | 100% | 1.00 | 6 |
| GANA | 100% | 100% | 1.00 | 6 |
| EMBARAZO | 100% | 100% | 1.00 | 5 |
| ANSIEDAD | 100% | 100% | 1.00 | 5 |
| CANSADO | 100% | 100% | 1.00 | 5 |
| ESTRES | 100% | 100% | 1.00 | 6 |
| COMER | 100% | 100% | 1.00 | 5 |
| SUFRIR | 100% | 100% | 1.00 | 6 |
| ADELGAZAR | 100% | 100% | 1.00 | 6 |
| COMER^SIN | 100% | 100% | 1.00 | 5 |
| MAREO | 100% | 100% | 1.00 | 12 |
| ALERGIA | 100% | 100% | 1.00 | 6 |
| AFECTAR | 100% | 100% | 1.00 | 10 |
| ALTA | 100% | 100% | 1.00 | 6 |
| FUMAR | 100% | 100% | 1.00 | 5 |
| AZUCAR | 100% | 89% | 0.94 | 18 |
| PIS | 91% | 95% | 0.93 | 21 |
| PIEL^CUERPO | 86% | 100% | 0.92 | 6 |
| FIEBRE | 86% | 100% | 0.92 | 6 |
| DOLOR | 86% | 100% | 0.92 | 6 |
| ARTERIA | 86% | 100% | 0.92 | 6 |
| DEBIL | 86% | 100% | 0.92 | 6 |
| ANALISIS-DE-SANGRE | 86% | 100% | 0.92 | 6 |
| HOSPITAL | 86% | 100% | 0.92 | 6 |
| CACA | 85% | 100% | 0.92 | 11 |
| APENDICE | 100% | 83% | 0.91 | 6 |
| MENTE^CEREBRO | 100% | 83% | 0.91 | 6 |
| EVITAR | 100% | 83% | 0.91 | 6 |
| VIRUS | 100% | 83% | 0.91 | 6 |
| RELAJAR | 83% | 100% | 0.91 | 5 |
| ENFERMO | 100% | 80% | 0.89 | 5 |
| DEPRESION | 100% | 80% | 0.89 | 5 |
| GORDO | 100% | 80% | 0.89 | 5 |
| DIABETES | 100% | 80% | 0.89 | 5 |
| INSOMNIO | 75% | 100% | 0.86 | 6 |
| ALCOHOL | 75% | 100% | 0.86 | 6 |
| OIR^MITAD | 75% | 100% | 0.86 | 6 |
| ACONSEJAR | 75% | 100% | 0.86 | 6 |
| FARMACIA | 83% | 83% | 0.83 | 6 |
| CONTROL | 83% | 83% | 0.83 | 6 |
| CITA | 71% | 100% | 0.83 | 5 |
| HAMBRE | 83% | 83% | 0.83 | 6 |
| PULMON | 71% | 100% | 0.83 | 5 |
| CONTRA | 83% | 83% | 0.83 | 6 |
| OPERAR | 90% | 75% | 0.82 | 12 |
| AGOTAMIENTO | 67% | 100% | 0.80 | 6 |
| HERIDA | 100% | 67% | 0.80 | 6 |
| CANCER | 100% | 67% | 0.80 | 6 |
| CENTRO^VIVIR | 100% | 60% | 0.75 | 5 |
| AUXILIAR | 100% | 60% | 0.75 | 5 |
| APETECER | 100% | 60% | 0.75 | 5 |
| NACER | 80% | 67% | 0.73 | 6 |
| PROBAR | 56% | 83% | 0.67 | 6 |
| CURAR | 70% | 64% | 0.67 | 11 |
| VER^PROBAR | 75% | 50% | 0.60 | 6 |
| CUIDAR | 100% | 40% | 0.57 | 5 |

## Figuras

- `matriz-confusion.png`: que predijo el modelo para cada signo real.
- `acierto-por-signo.png`: puntuacion F1 de cada signo, de peor a mejor.
- `calibracion.png`: confianza declarada frente a acierto real.
- `umbral.png`: cuanto responde y cuanto acierta segun la exigencia.