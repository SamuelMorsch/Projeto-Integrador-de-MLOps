### Alerta de drift de dados

O lote incorporado no ciclo `C007_20261127T121405Z` (`v007_4f092bbb0e`) mudou em relação ao histórico.

- PSI máximo: **0.370** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 25.7% -> lote novo 43.4%

Relatório completo: `evidencias/C007_20261127T121405Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
