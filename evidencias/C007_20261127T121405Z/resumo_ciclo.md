## Ciclo `C007_20261127T121405Z`
- **Gatilho:** `schedule` (run 45996815154)
- **data_version:** `v007_4f092bbb0e` | lotes: 7 | linhas: 7800
- **Features eleitas (11):** `num__chamados_suporte_3m`, `cat__tipo_contrato_mensal`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__tempo_contrato_meses`, `num__satisfacao`, `num__idade`, `num__atraso_pagamentos_6m`, `cat__plano_premium`
- **CV (F1 macro):** A = 0.6953 | B = 0.7017 -> vencedor do ciclo: **modelo_B**
- **Teste:** vencedor = 0.7258 | vigente anterior = 0.7099
- **Decisão:** **PROMOVIDO**, melhora de 0.0160 >= limiar 0.005
- **Modelo vigente agora:** `C007_20261127T121405Z_random_forest`
- **Drift:** PSI máx. = 0.370 (`mensalidade`) | atributos em alerta: 1 | ALERTA
