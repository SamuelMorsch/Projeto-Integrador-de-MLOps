## Ciclo `C010_20261128T152939Z`
- **Gatilho:** `schedule` (run 46160065049)
- **data_version:** `v010_bdc553b068` | lotes: 10 | linhas: 10200
- **Features eleitas (10):** `num__chamados_suporte_3m`, `cat__tipo_contrato_mensal`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__tempo_contrato_meses`, `num__atraso_pagamentos_6m`, `num__uso_por_servico`, `num__uso_dados_gb`
- **CV (F1 macro):** A = 0.7210 | B = 0.7223 -> vencedor do ciclo: **modelo_A**
- **Teste:** vencedor = 0.7302 | vigente anterior = 0.7363
- **Decisão:** **MANTIDO**, melhora de -0.0061 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C007_20261127T121405Z_random_forest`
- **Drift:** PSI máx. = 0.275 (`chamados_suporte_3m`) | atributos em alerta: 1 | ALERTA
