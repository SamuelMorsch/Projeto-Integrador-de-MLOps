## Ciclo `C003_20261125T191557Z`
- **Gatilho:** `schedule` (run 45683299000)
- **data_version:** `v003_d73cde0298` | lotes: 3 | linhas: 4600
- **Features eleitas (10):** `num__chamados_por_ano`, `num__tempo_contrato_meses`, `cat__tipo_contrato_mensal`, `cat__tipo_contrato_bianual`, `num__satisfacao`, `num__gasto_por_servico`, `num__chamados_suporte_3m`, `num__mensalidade`, `num__idade`, `num__atraso_pagamentos_6m`
- **CV (F1 macro):** A = 0.6666 | B = 0.6679 -> vencedor do ciclo: **modelo_A**
- **Teste:** vencedor = 0.6757 | vigente anterior = 0.6913
- **Decisão:** **MANTIDO**, melhora de -0.0155 < limiar 0.005; vigente preservado
- **Modelo vigente agora:** `C002_20261125T083010Z_random_forest`
- **Drift:** PSI máx. = 0.041 (`mensalidade`) | atributos em alerta: 0 | sem alerta
