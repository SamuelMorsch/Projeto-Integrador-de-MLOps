### Alerta de drift de dados

O lote incorporado no ciclo `C009_20261128T032133Z` (`v009_0492196107`) mudou em relação ao histórico.

- PSI máximo: **0.334** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 29.3% -> lote novo 49.5%

Relatório completo: `evidencias/C009_20261128T032133Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
