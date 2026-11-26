### Alerta de drift de dados

O lote incorporado no ciclo `C005_20261126T165209Z` (`v005_1b63121e73`) mudou em relação ao histórico.

- PSI máximo: **0.413** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 22.0% -> lote novo 36.1%

Relatório completo: `evidencias/C005_20261126T165209Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
