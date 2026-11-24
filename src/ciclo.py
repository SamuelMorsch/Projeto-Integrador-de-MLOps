"""Identidade e memória do ciclo: cycle_id, contexto compartilhado entre notebooks e histórico.

Os notebooks 01..05 rodam em processos separados (nbconvert). O contexto do ciclo fica em
data/processed/ciclo_atual.json e garante que votação, os dois treinos e a decisão compartilhem
o mesmo cycle_id e a mesma data_version.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd

from .config import dir_, gravar_json, ler_json, p

COLUNAS_HISTORICO = [
    "cycle_id", "timestamp_utc", "gatilho", "github_run_id", "data_version", "n_lotes", "n_linhas",
    "n_features_eleitas", "features_eleitas", "vencedor", "algoritmo_vencedor", "f1_cv_A", "f1_cv_B",
    "f1_teste_vencedor", "f1_teste_vigente_anterior", "delta_teste", "decisao", "motivo",
    "modelo_vigente_id", "drift_alerta", "max_psi",
]


def caminho_contexto(cfg: dict):
    return dir_(cfg, "dir_processed") / "ciclo_atual.json"


def caminho_historico():
    return p("evidencias", "historico_ciclos.csv")


def ler_historico() -> pd.DataFrame:
    c = caminho_historico()
    if not c.exists():
        return pd.DataFrame(columns=COLUNAS_HISTORICO)
    return pd.read_csv(c)


def iniciar_ciclo(cfg: dict) -> dict:
    """Cria cycle_id sequencial (C001, C002, ...) + carimbo de tempo UTC e grava o contexto."""
    hist = ler_historico()
    n = len(hist) + 1
    agora = datetime.now(timezone.utc)
    ctx = {
        "cycle_id": f"C{n:03d}_{agora.strftime('%Y%m%dT%H%M%SZ')}",
        "numero_ciclo": n,
        "ha_ciclo_anterior": n > 1,
        "inicio_utc": agora.isoformat(timespec="seconds"),
        # github.event_name: 'schedule' comprova a execução agendada; 'workflow_dispatch' = manual; 'local' = fora do Actions
        "gatilho": os.environ.get("PIPELINE_TRIGGER", "local"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_url": (f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}"
                           f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}") if os.environ.get("GITHUB_RUN_ID") else "",
        "run_ids": {},
    }
    gravar_json(caminho_contexto(cfg), ctx)
    dir_evidencias(ctx).mkdir(parents=True, exist_ok=True)
    return ctx


def carregar_contexto(cfg: dict) -> dict:
    ctx = ler_json(caminho_contexto(cfg))
    if not ctx:
        raise FileNotFoundError("Contexto do ciclo não encontrado: execute o notebook 01 antes.")
    return ctx


def salvar_contexto(cfg: dict, ctx: dict) -> None:
    gravar_json(caminho_contexto(cfg), ctx)


def dir_evidencias(ctx: dict):
    return p("evidencias", ctx["cycle_id"])
