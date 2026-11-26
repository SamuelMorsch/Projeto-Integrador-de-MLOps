## Ciclo `C004_20261126T033330Z`
- **Gatilho:** `schedule` (run 45749596261)
- **data_version:** `v004_58bb9be60f` | lotes: 4 | linhas: 5400
- **Features eleitas (11):** `num__tempo_contrato_meses`, `cat__tipo_contrato_mensal`, `num__chamados_suporte_3m`, `num__satisfacao`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__mensalidade`, `cat__tipo_contrato_bianual`, `num__atraso_pagamentos_6m`, `num__idade`, `cat__tipo_contrato_anual`
- **CV (F1 macro):** A = 0.6707 | B = 0.6742 -> vencedor do ciclo: **modelo_B**
- **Teste:** vencedor = 0.7135 | vigente anterior = 0.7046
- **Decisão:** **PROMOVIDO**, melhora de 0.0089 >= limiar 0.005
- **Modelo vigente agora:** `C004_20261126T033330Z_random_forest`
- **Drift:** PSI máx. = 0.377 (`mensalidade`) | atributos em alerta: 1 | ALERTA
