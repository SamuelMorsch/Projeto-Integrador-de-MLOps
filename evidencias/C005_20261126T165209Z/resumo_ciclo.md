## Ciclo `C005_20261126T165209Z`
- **Gatilho:** `schedule` (run 45862565222)
- **data_version:** `v005_1b63121e73` | lotes: 5 | linhas: 6200
- **Features eleitas (10):** `cat__tipo_contrato_mensal`, `num__chamados_suporte_3m`, `num__tempo_contrato_meses`, `num__mensalidade`, `num__satisfacao`, `num__chamados_por_ano`, `num__gasto_por_servico`, `cat__tipo_contrato_bianual`, `num__atraso_pagamentos_6m`, `cat__tipo_contrato_anual`
- **CV (F1 macro):** A = 0.6798 | B = 0.6773 -> vencedor do ciclo: **modelo_A**
- **Teste:** vencedor = 0.7080 | vigente anterior = 0.7114
- **Decisão:** **MANTIDO**, melhora de -0.0034 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C004_20261126T033330Z_random_forest`
- **Drift:** PSI máx. = 0.413 (`mensalidade`) | atributos em alerta: 1 | ALERTA
