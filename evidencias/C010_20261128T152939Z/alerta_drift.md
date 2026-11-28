### Alerta de drift de dados

O lote incorporado no ciclo `C010_20261128T152939Z` (`v010_bdc553b068`) mudou em relação ao histórico.

- PSI máximo: **0.275** em `chamados_suporte_3m`
- Atributos em alerta (PSI >= limite): chamados_suporte_3m
- Taxa de churn: histórico 31.0% -> lote novo 51.6%

Relatório completo: `evidencias/C010_20261128T152939Z/drift_report.csv`. O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.
