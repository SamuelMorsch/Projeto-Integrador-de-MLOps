## Ciclo `C006_20261127T014450Z`
- **Gatilho:** `schedule` (run 45924229162)
- **data_version:** `v006_0cb9f395e1` | lotes: 6 | linhas: 7000
- **Features eleitas (10):** `cat__tipo_contrato_mensal`, `num__chamados_suporte_3m`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__tempo_contrato_meses`, `num__idade`, `num__atraso_pagamentos_6m`, `cat__plano_premium`
- **CV (F1 macro):** A = 0.6940 | B = 0.6947 -> vencedor do ciclo: **modelo_A**
- **Teste:** vencedor = 0.7125 | vigente anterior = 0.7101
- **Decisão:** **MANTIDO**, melhora de 0.0024 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C004_20261126T033330Z_random_forest`
- **Drift:** PSI máx. = 0.464 (`mensalidade`) | atributos em alerta: 1 | ALERTA
