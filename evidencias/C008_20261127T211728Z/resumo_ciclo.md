## Ciclo `C008_20261127T211728Z`
- **Gatilho:** `schedule` (run 46069189500)
- **data_version:** `v008_e9edeb160c` | lotes: 8 | linhas: 8600
- **Features eleitas (10):** `num__chamados_suporte_3m`, `cat__tipo_contrato_mensal`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__tempo_contrato_meses`, `num__idade`, `num__atraso_pagamentos_6m`, `cat__plano_premium`
- **CV (F1 macro):** A = 0.7139 | B = 0.7139 -> vencedor do ciclo: **modelo_A**
- **Teste:** vencedor = 0.7130 | vigente anterior = 0.7271
- **Decisão:** **MANTIDO**, melhora de -0.0141 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C007_20261127T121405Z_random_forest`
- **Drift:** PSI máx. = 0.353 (`mensalidade`) | atributos em alerta: 1 | ALERTA
