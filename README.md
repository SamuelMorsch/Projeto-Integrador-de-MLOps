# Projeto N3 - Pipeline MLOps agendado para previsão de churn

**Disciplina:** Análise Preditiva - Católica de Santa Catarina (Engenharia de Software / Engenharia de IA)
**Professor:** M. Sc. Rodrigo Hagstrom
**Integrantes:** João Vitor Bast, Samuel, George

Um **único workflow agendado** do GitHub Actions executa, a cada ciclo: ingestão de dados novos -> ETL -> três métodos de
seleção de atributos com **votação** -> treino de **dois algoritmos** com as mesmas features -> eleição do vencedor ->
**regra de promoção** contra o modelo vigente -> previsões, registrando tudo no **MLflow**. Como recurso adicional
(critério 10), cada lote novo passa por **monitoramento de drift com alerta**.

```
schedule (cron)
   └─> 01_etl            ingestão do lote novo, diagnóstico antes/depois, atributos, data_version, split, DRIFT
   └─> 02_votacao        SelectKBest(MI) + Random Forest + RFE(LogReg) -> votos -> features eleitas do ciclo
   └─> 03_treino         Modelo A (Reg. Logística) x Modelo B (Random Forest): mesmas features, mesmos folds
   └─> 04_promocao       vencedor por CV -> confronto com o vigente no teste -> promove ou mantém -> manifesto
   └─> 05_previsoes      previsões com o vigente + teste integrado + comparação entre ciclos
   └─> commit do estado (data/raw, models, evidencias, mlruns) + artifact baixável
```

## Problema e dados

* **Problema:** classificação binária - prever `churn` (cliente cancela o serviço) de um provedor de internet fictício.
* **Dados:** **sintéticos**, gerados por `src/simulador.py` com seed fixa (sem dados pessoais). Cada ciclo recebe um lote
  novo (`data/raw/lote_NNN.csv`) com sujeira realista (ausentes, valores impossíveis, outliers, duplicatas e reenvios de
  registros antigos) e **mudanças de distribuição** a partir do lote 3 (campanha de preços), que exercitam o drift e a promoção.
  Também é possível depositar um CSV real em `data/incoming/` (mesmo esquema): ele é incorporado no próximo ciclo.
* **Métrica principal:** F1 macro (classe de churn é minoria). Definida em `config/config.yaml` antes do treino.
* **Protocolo:** teste fixo por **hash do id** (20%), nunca usado em treino/votação/escolha do vencedor; validação cruzada
  estratificada (5 folds) só no treino, com a votação de features **refeita dentro de cada fold**.

## Estrutura

```
.github/workflows/pipeline_mlops.yml   único workflow (schedule + workflow_dispatch)
config/config.yaml                     dados, algoritmos, votação, métrica, direção, limiar de promoção, drift
data/raw/                              lotes versionados (lote_000 = dados iniciais)   data/incoming/  novos CSV
notebooks/01..05_*.ipynb               documentam e acionam as funções de src/
src/                                   ingestao, simulador, preprocessamento, features, modelagem, promocao,
                                       drift (critério 10), rastreio (MLflow), ciclo, resumo_ciclo
models/modelo_vigente.json             manifesto do vigente (id, data_version, features, métrica, run_id, decisão)
models/historico/                      todos os modelos já promovidos (preservados)
evidencias/                            historico_ciclos.csv + uma pasta por ciclo + notebooks executados
mlruns/                                tracking do MLflow (versionado = histórico entre ciclos)
tests/                                 testes das regras centrais (votação, partição, limpeza, promoção, drift)
reports/relatorio_n3.pdf               relatório técnico
```

## Instalação e execução local

Requisitos: Python 3.11 (3.10+ deve funcionar) e Git.

```bash
git clone <URL-DO-REPOSITORIO> && cd projeto-n3
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name python3

python -m pytest -q tests                              # testes rápidos
python scripts/executar_local.py                       # 1 ciclo completo (01 -> 05)
python scripts/executar_local.py                       # 2º ciclo: entra o lote_001, há comparação com o vigente
```

O primeiro ciclo usa só o `lote_000` (ciclo inicial: o primeiro modelo é promovido). A partir do segundo, um lote novo
é incorporado, a votação é refeita, os dois algoritmos são retreinados e a regra decide entre **promover** e **manter**.
Para zerar o estado local: apague `mlruns/`, `evidencias/`, `models/modelo_vigente.json`, `models/historico/*.joblib`
e os `data/raw/lote_*.csv` exceto o `lote_000.csv`.

## Execução agendada (GitHub Actions)

1. Publique o repositório no GitHub (a branch padrão deve conter o workflow; **agendamentos só rodam na branch padrão**).
2. Em *Settings > Actions > General > Workflow permissions*, marque **Read and write permissions**
   (o workflow faz commit do estado do ciclo e abre issue de alerta).
3. O cron está em `.github/workflows/pipeline_mlops.yml` (`17 */3 * * *`, a cada 3 h em UTC). Ajuste ao prazo de entrega;
   o GitHub pode atrasar execuções agendadas. Use *Actions > pipeline-mlops > Run workflow* só para depuração
   (`workflow_dispatch` **não** substitui a prova do schedule).
4. **Como comprovar o schedule:** em *Actions*, o run exibe "Event: schedule"; o *Job Summary* mostra `Gatilho: schedule`;
   a coluna `gatilho` de `evidencias/historico_ciclos.csv`, o arquivo `evidencias/<cycle_id>/decisao.json` e a tag `gatilho`
   no MLflow registram o mesmo.
5. **Estado persistente:** os runners são temporários, então o workflow lê o estado do próprio repositório
   (`data/raw`, `models/`, `evidencias/`, `mlruns/`) e, ao fim de um ciclo bem-sucedido, faz commit dele. Também publica um
   **artifact** (`resultados-ciclo-N`) com o pacote completo. Se qualquer notebook falhar, o job para **antes** do commit:
   nada é promovido e o estado anterior permanece intacto.

## Consultar o MLflow

```bash
python -m src.rastreio rebase                 # ajusta caminhos absolutos do mlruns para esta máquina (necessário após clonar/baixar)
mlflow ui --backend-store-uri ./mlruns        # abra http://127.0.0.1:5000  (experimento: n3_churn_mlops)
```

Cada ciclo gera 6 runs com os mesmos `cycle_id` e `data_version`: `etl_ingestao`, `votacao_features` (votos, features
eleitas, parâmetros), **duas** de treino (`modelo_A_*` e `modelo_B_*`, hiperparâmetros, seed, métricas de CV e modelo
serializado), `selecao_promocao` (decisão, métricas, manifesto) e `previsoes_vigente`. Filtro útil na UI:
`tags.cycle_id = "C002_..."`. Em código: `mlflow.search_runs(experiment_names=["n3_churn_mlops"])`.

## Reproduzir as previsões com o modelo vigente

```python
import pandas as pd, sys; sys.path.insert(0, ".")
from src import features as ft, preprocessamento as pre, modelagem as mo, promocao as pr
from src.config import carregar_config, p

cfg = carregar_config()
manifesto = pr.ler_manifesto()                                   # models/modelo_vigente.json
bundle = mo.carregar_modelo(p(manifesto["caminho_modelo"]))      # pipeline = pré-processador + features eleitas + algoritmo
novos = pd.read_csv("data/scoring/scoring_lote_000.csv")         # registros sem rótulo
prep = ft.criar_atributos(pre.aplicar_regras_de_dominio(novos, cfg))
print(bundle["pipeline"].predict_proba(prep[ft.COLS_NUM + ft.COLS_CAT])[:, 1][:5])
```

As previsões de cada ciclo ficam em `evidencias/<cycle_id>/previsoes.csv` (notebook 05).

## Regras principais (todas em `config/config.yaml`)

| Item | Definição |
|---|---|
| Votação | atributo eleito se está no top-10 de **>= 2 dos 3** métodos; piso 6 e teto 14; desempate por escore médio normalizado |
| Vencedor do ciclo | maior F1 macro médio na CV; diferença < 0,002 = empate, vence o modelo A (mais simples) |
| Promoção | `CV(vencedor) >= 0,60` **e** `F1_teste(vencedor) - F1_teste(vigente) >= 0,005`; sem vigente promove; senão **mantém** |
| Drift (critério 10) | PSI < 0,10 estável; 0,10-0,25 atenção; >= 0,25 alerta (annotation + issue no GitHub) |

## Recurso adicional (critério 10): monitoramento de drift com alerta

* **Problema:** o pipeline retreina sozinho a cada lote; sem monitorar a entrada, uma mudança de comportamento dos clientes
  passaria despercebida.
* **Solução:** `src/drift.py` compara o lote novo com o histórico (PSI + KS por atributo, e variação da taxa de churn),
  gerando `evidencias/<cycle_id>/drift_report.csv`, gráfico `drift_psi.png` e `drift_resumo.json`.
* **Integração:** executa no notebook 01, vai para o MLflow (métrica `drift_max_psi`, tag `drift_alerta`), entra no manifesto e
  no histórico dos ciclos, e o workflow lê o resultado para emitir `::warning::` e abrir/comentar uma issue de alerta.

## Limitações

* Dados sintéticos: os números provam o funcionamento do pipeline, não o desempenho em um caso real.
* O conjunto de teste é reutilizado entre ciclos como árbitro da promoção (cada ciclo o usa uma vez); em produção seria
  prudente renová-lo periodicamente.
* O histórico do MLflow é um *file store* versionado no Git (adequado a este porte); para volume maior, usar servidor MLflow.
