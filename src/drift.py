"""Critério 10 - Monitoramento de drift de dados com alerta.

Problema real do projeto: o pipeline retreina sozinho a cada lote, mas ninguém olha se o
lote novo "parece" os anteriores. Se a distribuição muda (preço, chamados, forma de pagamento),
o vigente pode degradar sem aviso. Aqui cada lote novo é comparado com o histórico (PSI e KS),
o resultado vira relatório em evidencias/<cycle_id>/, é registrado no MLflow e, se passar do limite,
o workflow emite alerta (annotation + issue no GitHub).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

EPS = 1e-4


def _psi(p_ref: np.ndarray, p_new: np.ndarray) -> float:
    p_ref = np.clip(p_ref, EPS, None)
    p_new = np.clip(p_new, EPS, None)
    return float(np.sum((p_new - p_ref) * np.log(p_new / p_ref)))


def psi_numerico(ref: pd.Series, novo: pd.Series, n_bins: int = 10) -> float:
    ref, novo = ref.dropna(), novo.dropna()
    if ref.nunique() < 2 or novo.empty:
        return 0.0
    cortes = np.unique(np.quantile(ref, np.linspace(0, 1, n_bins + 1)[1:-1]))
    b_ref = np.digitize(ref, cortes)
    b_new = np.digitize(novo, cortes)
    k = len(cortes) + 1
    return _psi(np.bincount(b_ref, minlength=k) / len(ref), np.bincount(b_new, minlength=k) / len(novo))


def psi_categorico(ref: pd.Series, novo: pd.Series) -> float:
    ref, novo = ref.dropna().astype(str), novo.dropna().astype(str)
    if ref.empty or novo.empty:
        return 0.0
    cats = sorted(set(ref) | set(novo))
    return _psi(ref.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy(),
                novo.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy())


def _status(psi: float, cfg: dict) -> str:
    if psi >= cfg["drift"]["psi_alerta"]:
        return "ALERTA"
    if psi >= cfg["drift"]["psi_aviso"]:
        return "atenção"
    return "estável"


def relatorio_drift(ref: pd.DataFrame, novo: pd.DataFrame, cols_num: list[str], cols_cat: list[str],
                    alvo: str, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Compara o lote novo com o histórico. Retorna tabela por atributo e um resumo do ciclo."""
    d = cfg["drift"]
    linhas = []
    for c in cols_num:
        psi = psi_numerico(ref[c], novo[c], d["n_bins"])
        ks = ks_2samp(ref[c].dropna(), novo[c].dropna())
        linhas.append({"atributo": c, "tipo": "numérico", "psi": psi, "ks_estatistica": float(ks.statistic),
                       "ks_p_valor": float(ks.pvalue), "media_ref": float(ref[c].mean()),
                       "media_novo": float(novo[c].mean()), "status": _status(psi, cfg)})
    for c in cols_cat:
        psi = psi_categorico(ref[c], novo[c])
        linhas.append({"atributo": c, "tipo": "categórico", "psi": psi, "ks_estatistica": np.nan,
                       "ks_p_valor": np.nan, "media_ref": np.nan, "media_novo": np.nan, "status": _status(psi, cfg)})
    tab = pd.DataFrame(linhas).sort_values("psi", ascending=False).reset_index(drop=True)
    n_alerta = int((tab["status"] == "ALERTA").sum())
    resumo = {
        "avaliado": True,
        "n_ref": int(len(ref)), "n_novo": int(len(novo)),
        "max_psi": float(tab["psi"].max()),
        "atributo_max_psi": str(tab.loc[0, "atributo"]),
        "n_features_alerta": n_alerta,
        "n_features_atencao": int((tab["status"] == "atenção").sum()),
        "taxa_alvo_ref": float(ref[alvo].mean()), "taxa_alvo_novo": float(novo[alvo].mean()),
        "alerta": bool(n_alerta >= d["min_features_alerta"]),
        "features_em_alerta": tab.loc[tab["status"] == "ALERTA", "atributo"].tolist(),
    }
    return tab, resumo


def resumo_sem_referencia(motivo: str) -> dict:
    return {"avaliado": False, "motivo": motivo, "max_psi": 0.0, "n_features_alerta": 0,
            "n_features_atencao": 0, "alerta": False, "features_em_alerta": []}
