## Ciclo `C001_20261124T234632Z`
- **Gatilho:** `workflow_dispatch` (run 45512629978)
- **data_version:** `v001_8c382cd5af` | lotes: 1 | linhas: 3000
- **Features eleitas (10):** `num__tempo_contrato_meses`, `cat__tipo_contrato_mensal`, `num__mensalidade`, `num__chamados_suporte_3m`, `num__chamados_por_ano`, `cat__tipo_contrato_bianual`, `num__atraso_pagamentos_6m`, `num__gasto_por_servico`, `num__tem_atraso`, `num__satisfacao`
- **CV (F1 macro):** A = 0.6717 | B = 0.6792 -> vencedor do ciclo: **modelo_B**
- **Teste:** vencedor = 0.6804
- **Decisão:** **PROMOVIDO**, não havia modelo vigente (primeiro ciclo)
- **Modelo vigente agora:** `C001_20261124T234632Z_random_forest`
- **Drift:** não avaliado (ciclo inicial: usa apenas os dados já presentes em data/raw)
