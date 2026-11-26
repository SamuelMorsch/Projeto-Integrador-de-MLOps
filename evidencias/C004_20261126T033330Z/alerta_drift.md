### Alerta de drift de dados

O lote incorporado no ciclo `C004_20261126T033330Z` (`v004_58bb9be60f`) mudou em relação ao histórico.

- PSI máximo: **0.377** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 20.5% -> lote novo 31.1%

Relatório completo: `evidencias/C004_20261126T033330Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
