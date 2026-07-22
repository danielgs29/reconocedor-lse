# Comparacion de modelos (registrada en MLflow)

Experimento MLflow: `comparacion-modelos-lse`. Mismo conjunto de prueba para todos: 148 grabaciones, 64 signos. Cada modelo se vuelve a medir; no se usan cifras antiguas.

Para explorarlo en la interfaz: `MLFLOW_ALLOW_FILE_STORE=true uv run mlflow ui`

| Modelo | Arquitectura | Aumento | Preentrenamiento | Acierto | Parametros | Desplegado |
|---|---|---|---|---|---|---|
| transformer_pre_asl.keras | Transformer | si | signos americanos (ASL) | 90.5% | 94,592 | si |
| transformer_64conceptos.keras | Transformer | si | ninguno | 83.1% | 94,592 | no |
| transformer_pre_lsa64.keras | Transformer | si | signos argentinos (LSA64) | 82.4% | 94,592 | no |
| transformer_64_grande.keras | Transformer grande | si | ninguno | 81.1% | 453,568 | no |

## No comparables (otro vocabulario o entrada distinta)

Los experimentos de red recurrente (GRU) y sin aumento se hicieron con un vocabulario anterior de 53 signos, por lo que no se pueden medir sobre este conjunto de prueba. Se listan para dejar constancia.

- baseline.keras: otro vocabulario (53 signos)
- baseline_gru.keras: otro vocabulario (53 signos)
- gru_aumento3.keras: otro vocabulario (53 signos)
- transformer_236_arq128.keras: otro vocabulario (236 signos)
- transformer_236_arq128_v2.keras: otro vocabulario (236 signos)
- transformer_236_mejorado.keras: otro vocabulario (236 signos)
- transformer_300_pre_asl.keras: otro vocabulario (236 signos)
- transformer_300_pre_asl_94k.keras: otro vocabulario (236 signos)
- transformer_300_pre_asl_grande.keras: otro vocabulario (236 signos)
- transformer_45conceptos.keras: otro vocabulario (45 signos)
- transformer_86_preentrenado.keras: otro vocabulario (86 signos)
- transformer_86conceptos.keras: otro vocabulario (86 signos)
- transformer_aumento3.keras: otro vocabulario (53 signos)
- transformer_z_movimiento.keras: otro vocabulario (45 signos)