### Alerta de drift de dados

O lote incorporado no ciclo `C006_20261127T014450Z` (`v006_0cb9f395e1`) mudou em relação ao histórico.

- PSI máximo: **0.464** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 23.9% -> lote novo 40.4%

Relatório completo: `evidencias/C006_20261127T014450Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
