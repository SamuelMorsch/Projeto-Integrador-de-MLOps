## Ciclo `C009_20261128T032133Z`
- **Gatilho:** `schedule` (run 46102403470)
- **data_version:** `v009_0492196107` | lotes: 9 | linhas: 9400
- **Features eleitas (10):** `num__chamados_suporte_3m`, `cat__tipo_contrato_mensal`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__tempo_contrato_meses`, `num__idade`, `num__atraso_pagamentos_6m`, `cat__plano_premium`
- **CV (F1 macro):** A = 0.7165 | B = 0.7194 -> vencedor do ciclo: **modelo_B**
- **Teste:** vencedor = 0.7196 | vigente anterior = 0.7275
- **Decisão:** **MANTIDO**, melhora de -0.0079 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C007_20261127T121405Z_random_forest`
- **Drift:** PSI máx. = 0.334 (`mensalidade`) | atributos em alerta: 1 | ALERTA
