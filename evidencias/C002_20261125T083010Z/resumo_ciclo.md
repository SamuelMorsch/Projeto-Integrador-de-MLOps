## Ciclo `C002_20261125T083010Z`
- **Gatilho:** `schedule` (run 45576699201)
- **data_version:** `v002_e6352cb52b` | lotes: 2 | linhas: 3800
- **Features eleitas (11):** `num__tempo_contrato_meses`, `cat__tipo_contrato_mensal`, `num__idade`, `cat__tipo_contrato_bianual`, `num__chamados_por_ano`, `num__gasto_por_servico`, `num__mensalidade`, `num__chamados_suporte_3m`, `num__atraso_pagamentos_6m`, `num__satisfacao`, `cat__tipo_contrato_anual`
- **CV (F1 macro):** A = 0.6656 | B = 0.6690 -> vencedor do ciclo: **modelo_B**
- **Teste:** vencedor = 0.6862 | vigente anterior = 0.6777
- **Decisão:** **PROMOVIDO**, melhora de 0.0085 >= limiar 0.005
- **Modelo vigente agora:** `C002_20261125T083010Z_random_forest`
- **Drift:** PSI máx. = 0.030 (`mensalidade`) | atributos em alerta: 0 | sem alerta
