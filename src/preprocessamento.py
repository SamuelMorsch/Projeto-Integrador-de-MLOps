"""ETL: diagnóstico, limpeza por regras de domínio, divisão treino/teste e pré-processador.

Princípio anti-vazamento: tudo que é APRENDIDO dos dados (medianas, médias, desvios,
categorias) vive dentro do ColumnTransformer e só é ajustado com dados de treino
(ou com o treino de cada fold). As etapas deste módulo, fora do ColumnTransformer, usam
apenas regras fixas de domínio (config.yaml) e hash do id; nunca estatísticas dos dados.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import COLS_CAT, COLS_NUM


# ----------------------------------------------------------------------------- diagnóstico
def diagnosticar(df: pd.DataFrame, cfg: dict) -> dict:
    """Retrato dos problemas de qualidade (usado antes e depois da limpeza)."""
    idc = cfg["dados"]["coluna_id"]
    faixas = cfg["dados"]["faixas_validas"]
    inval = {}
    for col, (lo, hi) in faixas.items():
        if col in df:
            s = df[col]
            inval[col] = int(((s < lo) | (s > hi)).sum())
    num = df.select_dtypes("number").drop(columns=[c for c in ["lote", idc] if c in df.columns], errors="ignore")
    outliers_iqr = {}
    for c in num.columns:
        q1, q3 = num[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers_iqr[c] = int(((num[c] < q1 - 3 * iqr) | (num[c] > q3 + 3 * iqr)).sum()) if iqr > 0 else 0
    return {
        "linhas": int(len(df)),
        "duplicadas_exatas": int(df.drop(columns=["lote"], errors="ignore").duplicated().sum()),
        "ids_repetidos": int(df[idc].duplicated().sum()),
        "ausentes_por_coluna": {c: int(v) for c, v in df.isna().sum().items() if v > 0},
        "valores_fora_da_faixa": {c: v for c, v in inval.items() if v > 0},
        "outliers_iqr3": {c: v for c, v in outliers_iqr.items() if v > 0},
        "taxa_alvo": float(df[cfg["dados"]["alvo"]].mean()) if cfg["dados"]["alvo"] in df else None,
    }


# ----------------------------------------------------------------------------- limpeza
def aplicar_regras_de_dominio(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Valores impossíveis/outliers extremos viram ausentes (imputados depois, só com estatística do treino).

    Justificativa: idade negativa, mensalidade <= 0 ou 5.000 GB/mês são erros de captura, não
    comportamento real; descartar a linha perderia as demais colunas, que estão corretas.
    """
    d = df.copy()
    for col, (lo, hi) in cfg["dados"]["faixas_validas"].items():
        if col in d:
            d.loc[(d[col] < lo) | (d[col] > hi), col] = np.nan
    return d


def limpar_dados(bruto: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Deduplica (entre lotes também), remove linhas sem alvo e aplica regras de domínio."""
    idc, alvo = cfg["dados"]["coluna_id"], cfg["dados"]["alvo"]
    n0 = len(bruto)
    d = bruto.sort_values(["lote", idc], kind="mergesort").reset_index(drop=True)
    d = d.drop_duplicates(subset=[c for c in d.columns if c != "lote"], keep="first")
    n_exatas = n0 - len(d)
    antes_id = len(d)
    d = d.drop_duplicates(subset=[idc], keep="first")      # mesmo cliente reenviado: vale o primeiro lote
    n_id = antes_id - len(d)
    antes_alvo = len(d)
    d = d.dropna(subset=[alvo])
    n_sem_alvo = antes_alvo - len(d)
    d = aplicar_regras_de_dominio(d, cfg)
    d[alvo] = d[alvo].astype(int)
    resumo = {"linhas_entrada": n0, "removidas_duplicadas_exatas": n_exatas,
              "removidas_id_repetido": n_id, "removidas_sem_alvo": n_sem_alvo, "linhas_saida": len(d)}
    return d.reset_index(drop=True), resumo


# ----------------------------------------------------------------------------- partição
def _bucket(valor, seed: int) -> float:
    h = hashlib.md5(f"{seed}:{valor}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def dividir_treino_teste(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Teste definido pelo HASH do id: um cliente que foi para o teste fica no teste em todos os ciclos.

    Assim, modelos de ciclos anteriores nunca viram o teste atual, e a comparação com o vigente é justa
    mesmo com a chegada de lotes novos.
    """
    idc, seed = cfg["dados"]["coluna_id"], cfg["projeto"]["seed"]
    b = df[idc].map(lambda v: _bucket(v, seed))
    teste = b < cfg["avaliacao"]["fracao_teste"]
    return df[~teste].reset_index(drop=True), df[teste].reset_index(drop=True)


# ----------------------------------------------------------------------------- transformação
def construir_preprocessador() -> ColumnTransformer:
    """Imputação + escala (numéricas) e imputação + one-hot (categóricas). Saída em DataFrame."""
    num = Pipeline([("imp", SimpleImputer(strategy="median")), ("esc", StandardScaler())])
    cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    ct = ColumnTransformer([("num", num, COLS_NUM), ("cat", cat, COLS_CAT)], remainder="drop")
    ct.set_output(transform="pandas")
    return ct
