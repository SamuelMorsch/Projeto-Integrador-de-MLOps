"""Treino, validação e serialização dos dois algoritmos que disputam o ciclo.

Protocolo comum aos dois (A e B): mesmas linhas de treino, mesmos folds estratificados,
mesmas features por fold (votadas DENTRO do fold, no notebook 02) e mesma métrica principal.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

from .preprocessamento import construir_preprocessador

CHAVES = ["modelo_A", "modelo_B"]


class SelecionarColunas(BaseEstimator, TransformerMixin):
    """Mantém só as features eleitas (por nome) na saída do pré-processador.

    Faz parte do Pipeline serializado: o vigente sempre prevê com o conjunto de features com que foi treinado.
    """

    def __init__(self, colunas=None):
        self.colunas = colunas

    def fit(self, X, y=None):
        faltando = [c for c in self.colunas if c not in X.columns]
        if faltando:
            raise ValueError(f"Features eleitas ausentes após o pré-processamento: {faltando}")
        return self

    def transform(self, X):
        return X[list(self.colunas)]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.colunas, dtype=object)


def criar_estimador(cfg: dict, chave: str):
    spec = cfg["algoritmos"][chave]
    params = dict(spec["params"])
    seed = cfg["projeto"]["seed"]
    if spec["nome"] == "regressao_logistica":
        return LogisticRegression(random_state=seed, **params)
    if spec["nome"] == "random_forest":
        return RandomForestClassifier(random_state=seed, **params)
    raise ValueError(f"Algoritmo desconhecido: {spec['nome']}")


# ----------------------------------------------------------------------------- métricas
def calcular_metricas(y_true, y_pred, y_proba=None) -> dict:
    m = {
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
    }
    if y_proba is not None:
        m["roc_auc"] = roc_auc_score(y_true, y_proba)
    return {k: float(v) for k, v in m.items()}


def avaliar_pipeline(pipe, X: pd.DataFrame, y) -> dict:
    pred = pipe.predict(X)
    proba = pipe.predict_proba(X)[:, 1] if hasattr(pipe, "predict_proba") else None
    return calcular_metricas(y, pred, proba)


# ----------------------------------------------------------------------------- validação cruzada
def validar_cruzado(cfg: dict, X: pd.DataFrame, y: pd.Series, folds, features_por_fold: list[list[str]]) -> dict:
    """CV dos DOIS candidatos nos MESMOS folds e com as MESMAS features de cada fold.

    Em cada fold: pré-processador ajustado só no treino do fold -> subconjunto de features votadas
    naquele fold -> fit de A e B -> métricas na parte de validação do fold.
    """
    res = {k: [] for k in CHAVES}
    for (idx_tr, idx_va), feats in zip(folds, features_por_fold):
        pre = construir_preprocessador()
        Xtr = pre.fit_transform(X.iloc[idx_tr], y.iloc[idx_tr])[feats]
        Xva = pre.transform(X.iloc[idx_va])[feats]
        for k in CHAVES:
            est = criar_estimador(cfg, k).fit(Xtr, y.iloc[idx_tr])
            proba = est.predict_proba(Xva)[:, 1]
            res[k].append(calcular_metricas(y.iloc[idx_va], est.predict(Xva), proba))
    resumo = {}
    for k, lista in res.items():
        df = pd.DataFrame(lista)
        resumo[k] = {"por_fold": lista,
                     "media": {c: float(df[c].mean()) for c in df.columns},
                     "desvio": {c: float(df[c].std(ddof=1)) for c in df.columns}}
    return resumo


# ----------------------------------------------------------------------------- ajuste final
def treinar_final(cfg: dict, chave: str, X: pd.DataFrame, y: pd.Series, features: list[str]) -> Pipeline:
    """Pipeline = pré-processador (ajustado no treino) + features eleitas + algoritmo."""
    pipe = Pipeline([("pre", construir_preprocessador()),
                     ("sel", SelecionarColunas(features)),
                     ("clf", criar_estimador(cfg, chave))])
    return pipe.fit(X, y)


def salvar_modelo(pipe, caminho: Path, metadados: dict) -> Path:
    """Serializa pipeline + features + metadados juntos (previsão consistente em qualquer ciclo)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipe, "features": list(pipe.named_steps["sel"].colunas), "metadados": metadados},
                caminho, compress=3)
    return caminho


def carregar_modelo(caminho: Path) -> dict:
    return joblib.load(caminho)
