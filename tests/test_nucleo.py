"""Testes rápidos das regras centrais. Não alteram nenhum arquivo do repositório."""
import numpy as np
import pandas as pd
import pytest

from src.config import carregar_config
from src import drift, features as ft, preprocessamento as pre, promocao as pr
from src.simulador import gerar_lote

CFG = carregar_config()


def _dados_votacao(n=600, seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 14)), columns=[f"num__f{i}" for i in range(10)] + [f"cat__c{i}" for i in range(4)])
    y = pd.Series(((X["num__f0"] + 0.8 * X["num__f1"] - 0.6 * X["num__f2"] + rng.normal(0, 0.7, n)) > 0).astype(int))
    return X, y


def test_votacao_respeita_regra_piso_teto_e_e_deterministica():
    X, y = _dados_votacao()
    r1, r2 = ft.votar_features(X, y, CFG), ft.votar_features(X, y, CFG)
    sf = CFG["selecao_features"]
    assert r1["eleitas"] == r2["eleitas"]
    assert sf["min_features"] <= len(r1["eleitas"]) <= sf["max_features"]
    # os atributos realmente informativos precisam ser eleitos
    assert {"num__f0", "num__f1"} <= set(r1["eleitas"])
    # tudo que tem >= min_votos e cabe no teto foi eleito
    t = r1["tabela"]
    assert set(t.loc[t["eleita"] == 1, "feature"]) == set(r1["eleitas"])
    assert (t[["voto_selectkbest_mi", "voto_random_forest", "voto_rfe_logreg"]].sum() == CFG["selecao_features"]["k_por_metodo"]).all()


def test_particao_por_hash_e_estavel_e_disjunta():
    df = gerar_lote(2000, 0, 1, 1, sujeira=False)
    tr, te = pre.dividir_treino_teste(df, CFG)
    assert set(tr["id_cliente"]).isdisjoint(te["id_cliente"]) and len(tr) + len(te) == len(df)
    assert abs(len(te) / len(df) - CFG["avaliacao"]["fracao_teste"]) < 0.03
    # chegada de lote novo: quem estava no teste continua no teste
    novo = pd.concat([df, gerar_lote(500, 1, 2, 500_000, sujeira=False)], ignore_index=True)
    _, te2 = pre.dividir_treino_teste(novo, CFG)
    assert set(te["id_cliente"]) <= set(te2["id_cliente"])


def test_limpeza_remove_duplicatas_entre_lotes_e_trata_impossiveis():
    a = gerar_lote(300, 0, 5, 1, sujeira=False)
    a["lote"] = 0
    reenviado = a.sample(10, random_state=1).copy()
    reenviado["lote"] = 1
    b = gerar_lote(100, 1, 6, 10_000, sujeira=False)
    b["lote"] = 1
    b.loc[b.index[0], "idade"] = -5
    bruto = pd.concat([a, b, reenviado], ignore_index=True)
    limpo, resumo = pre.limpar_dados(bruto, CFG)
    assert len(limpo) == 400 and limpo["id_cliente"].is_unique
    assert resumo["removidas_duplicadas_exatas"] == 10
    assert limpo["idade"].isna().sum() >= 1 and (limpo["idade"].dropna() >= 18).all()


@pytest.mark.parametrize("cv,teste_v,teste_vig,esperado", [
    (0.70, 0.70, None, "promovido"),        # primeiro ciclo
    (0.55, 0.80, 0.60, "mantido"),          # abaixo do piso de CV
    (0.70, 0.705, 0.700, "promovido"),      # melhora == limiar
    (0.70, 0.704, 0.700, "mantido"),        # melhora < limiar
    (0.70, 0.650, 0.700, "mantido"),        # piorou
])
def test_regra_de_promocao(cv, teste_v, teste_vig, esperado):
    assert pr.decidir_promocao(CFG, cv, teste_v, teste_vig)["decisao"] == esperado


def test_empate_tecnico_favorece_modelo_simples():
    cv = {"modelo_A": {"media": {"f1_macro": 0.700}}, "modelo_B": {"media": {"f1_macro": 0.701}}}
    assert pr.eleger_vencedor(CFG, cv)["vencedor"] == "modelo_A"
    cv["modelo_B"]["media"]["f1_macro"] = 0.720
    assert pr.eleger_vencedor(CFG, cv)["vencedor"] == "modelo_B"


def test_drift_psi_detecta_mudanca():
    rng = np.random.default_rng(0)
    ref = pd.Series(rng.normal(0, 1, 5000))
    assert drift.psi_numerico(ref, pd.Series(rng.normal(0, 1, 2000))) < 0.05
    assert drift.psi_numerico(ref, pd.Series(rng.normal(1.5, 1, 2000))) > CFG["drift"]["psi_alerta"]
    a, b = pd.Series(["x"] * 800 + ["y"] * 200), pd.Series(["x"] * 300 + ["y"] * 700)
    assert drift.psi_categorico(a, b) > CFG["drift"]["psi_alerta"]


def test_rebase_mlruns_reescreve_caminhos(tmp_path):
    pytest.importorskip("mlflow")
    from src.rastreio import rebase_mlruns
    d = tmp_path / "mlruns" / "1"
    d.mkdir(parents=True)
    (d / "meta.yaml").write_text("artifact_location: file:///home/runner/work/x/x/mlruns/1\n", encoding="utf-8")
    assert rebase_mlruns(tmp_path / "mlruns") == 1
    assert (tmp_path / "mlruns").resolve().as_uri() in (d / "meta.yaml").read_text(encoding="utf-8")
    assert rebase_mlruns(tmp_path / "mlruns") == 0   # idempotente
