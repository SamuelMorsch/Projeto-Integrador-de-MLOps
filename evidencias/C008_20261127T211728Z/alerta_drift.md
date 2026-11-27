### Alerta de drift de dados

O lote incorporado no ciclo `C008_20261127T211728Z` (`v008_e9edeb160c`) mudou em relação ao histórico.

- PSI máximo: **0.353** em `mensalidade`
- Atributos em alerta (PSI >= limite): mensalidade
- Taxa de churn: histórico 27.6% -> lote novo 46.5%

Relatório completo: `evidencias/C008_20261127T211728Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
