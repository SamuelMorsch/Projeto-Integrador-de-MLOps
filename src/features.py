"""Engenharia de atributos (sem estado: não aprende nada dos dados) e votação de features.

Três métodos de importância/seleção, todos aplicados sobre o espaço JÁ pré-processado
(numéricas padronizadas + categóricas one-hot) e ajustados apenas no treino:
  1. SelectKBest com informação mútua (captura relações não lineares; categóricas tratadas como discretas)
  2. Importância por Random Forest
  3. RFE com Regressão Logística (L2)
Votação: atributo eleito = aparece no top-k de pelo menos `min_votos` métodos. Piso/teto e
desempate são definidos em config.yaml ANTES da execução.
"""
from __future__ import annotations

from functools import partial

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, SelectKBest, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

COLS_NUM_BASE = [
    "idade", "tempo_contrato_meses", "mensalidade", "num_servicos", "uso_dados_gb",
    "chamados_suporte_3m", "atraso_pagamentos_6m", "satisfacao", "numero_dependentes",
]
COLS_NUM_ENG = ["gasto_por_servico", "chamados_por_ano", "uso_por_servico", "contrato_recente", "tem_atraso"]
COLS_NUM = COLS_NUM_BASE + COLS_NUM_ENG
COLS_CAT = ["regiao", "plano", "tipo_contrato", "forma_pagamento", "dia_semana_cadastro"]

METODOS = ["selectkbest_mi", "random_forest", "rfe_logreg"]


def criar_atributos(df: pd.DataFrame) -> pd.DataFrame:
    """Atributos derivados linha a linha (determinísticos => não há vazamento)."""
    d = df.copy()
    meses = d["tempo_contrato_meses"].clip(lower=0)
    d["gasto_por_servico"] = d["mensalidade"] / d["num_servicos"].replace(0, np.nan)
    d["chamados_por_ano"] = d["chamados_suporte_3m"] * 4 / (meses / 12 + 1)
    d["uso_por_servico"] = d["uso_dados_gb"] / d["num_servicos"].replace(0, np.nan)
    d["contrato_recente"] = (d["tempo_contrato_meses"] <= 6).astype(float).where(d["tempo_contrato_meses"].notna())
    d["tem_atraso"] = (d["atraso_pagamentos_6m"] > 0).astype(float).where(d["atraso_pagamentos_6m"].notna())
    return d


# ----------------------------------------------------------------------------- métodos
def _norm01(s: pd.Series) -> pd.Series:
    r = s.max() - s.min()
    return (s - s.min()) / r if r > 0 else s * 0.0


def metodo_selectkbest(X: pd.DataFrame, y, k: int, seed: int) -> pd.Series:
    discreta = np.array([c.startswith("cat__") for c in X.columns])
    score = partial(mutual_info_classif, discrete_features=discreta, random_state=seed)
    sel = SelectKBest(score_func=score, k=min(k, X.shape[1])).fit(X, y)
    return pd.Series(sel.scores_, index=X.columns, name="selectkbest_mi")


def metodo_random_forest(X: pd.DataFrame, y, n_estimators: int, seed: int) -> pd.Series:
    rf = RandomForestClassifier(n_estimators=n_estimators, min_samples_leaf=5, class_weight="balanced",
                                random_state=seed, n_jobs=1).fit(X, y)
    return pd.Series(rf.feature_importances_, index=X.columns, name="random_forest")


def metodo_rfe(X: pd.DataFrame, y, k: int, seed: int) -> pd.Series:
    """RFE devolve um ranking (1 = melhor). Convertido em escore: maior = melhor."""
    est = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)
    rfe = RFE(est, n_features_to_select=min(k, X.shape[1]), step=1).fit(X, y)
    escore = (rfe.ranking_.max() - rfe.ranking_ + 1).astype(float)
    return pd.Series(escore, index=X.columns, name="rfe_logreg")


def votar_features(X: pd.DataFrame, y, cfg: dict) -> dict:
    """Executa os 3 métodos e aplica a regra de votação. Retorna tabela de votos e conjunto final."""
    sf, seed = cfg["selecao_features"], cfg["projeto"]["seed"]
    k = sf["k_por_metodo"]
    escores = pd.concat([
        metodo_selectkbest(X, y, k, seed),
        metodo_random_forest(X, y, sf["rf_n_estimators"], seed),
        metodo_rfe(X, y, k, seed),
    ], axis=1)

    votos = pd.DataFrame(index=X.columns)
    for m in METODOS:
        topk = escores[m].sort_values(ascending=False, kind="mergesort").head(k).index
        votos[f"voto_{m}"] = votos.index.isin(topk).astype(int)
    votos["votos"] = votos[[f"voto_{m}" for m in METODOS]].sum(axis=1)
    for m in METODOS:
        votos[f"escore_{m}"] = escores[m]
    votos["escore_medio_norm"] = pd.concat([_norm01(escores[m]) for m in METODOS], axis=1).mean(axis=1)

    # Ordenação determinística: mais votos, depois maior escore médio normalizado (desempate), depois nome.
    ordem = votos.reset_index(names="feature").sort_values(
        ["votos", "escore_medio_norm", "feature"], ascending=[False, False, True]).reset_index(drop=True)
    aprovadas = ordem[ordem["votos"] >= sf["min_votos"]]["feature"].tolist()
    if len(aprovadas) < sf["min_features"]:
        aprovadas = ordem["feature"].head(sf["min_features"]).tolist()        # piso
    elif len(aprovadas) > sf["max_features"]:
        aprovadas = aprovadas[: sf["max_features"]]                            # teto (já ordenado)
    votos["eleita"] = votos.index.isin(aprovadas).astype(int)
    tabela = votos.reset_index(names="feature").sort_values(
        ["eleita", "votos", "escore_medio_norm"], ascending=[False, False, False]).reset_index(drop=True)
    return {"tabela": tabela, "eleitas": [f for f in ordem["feature"] if f in set(aprovadas)]}


def votar_em_folds(X: pd.DataFrame, y, folds: list[tuple[np.ndarray, np.ndarray]], cfg: dict,
                   preproc_factory) -> list[dict]:
    """Repete votação DENTRO de cada fold de treino (pré-processador ajustado só no fold)."""
    saida = []
    for i, (idx_tr, _) in enumerate(folds):
        pre = preproc_factory()
        Xt = pre.fit_transform(X.iloc[idx_tr], y.iloc[idx_tr])
        r = votar_features(Xt, y.iloc[idx_tr], cfg)
        saida.append({"fold": i, "eleitas": r["eleitas"], "n_colunas": int(Xt.shape[1])})
    return saida


def gerar_folds(y, cfg: dict):
    skf = StratifiedKFold(n_splits=cfg["avaliacao"]["cv_folds"], shuffle=True, random_state=cfg["projeto"]["seed"])
    return list(skf.split(np.zeros(len(y)), y))
