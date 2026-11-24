"""Camada fina sobre o MLflow: configuração, runs padronizadas e manutenção do diretório de tracking.

O tracking usa o armazenamento em arquivos (./mlruns), que é versionado no repositório pelo workflow
e também exportado como artifact. Assim o histórico entre ciclos sobrevive aos runners temporários.
Atenção: o MLflow grava caminhos ABSOLUTOS nos metadados; rebase_mlruns() os ajusta ao diretório atual
(necessário quando o mlruns vem de outro computador/runner).
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path

import mlflow

from .config import p

DIR_MLRUNS = p("mlruns")


def rebase_mlruns(destino: Path = DIR_MLRUNS) -> int:
    """Reescreve file:///.../mlruns/... nos meta.yaml para o caminho atual. Retorna nº de arquivos ajustados."""
    destino = Path(destino)
    if not destino.exists():
        return 0
    novo_prefixo = destino.resolve().as_uri()
    padrao = re.compile(r"file://[^\s'\"]*?/mlruns(?=[/\s'\"]|$)")
    ajustados = 0
    for meta in destino.rglob("meta.yaml"):
        texto = meta.read_text(encoding="utf-8")
        novo = padrao.sub(novo_prefixo, texto)
        if novo != texto:
            meta.write_text(novo, encoding="utf-8")
            ajustados += 1
    return ajustados


def configurar(cfg: dict) -> str:
    DIR_MLRUNS.mkdir(parents=True, exist_ok=True)
    rebase_mlruns()
    mlflow.set_tracking_uri(DIR_MLRUNS.resolve().as_uri())
    nome = cfg["projeto"]["experimento_mlflow"]
    mlflow.set_experiment(nome)
    return nome


@contextmanager
def run(nome: str, ctx: dict, etapa: str, tags_extra: dict | None = None):
    """Run com identificadores obrigatórios (cycle_id, data_version, gatilho) em todas as etapas."""
    tags = {"cycle_id": ctx["cycle_id"], "data_version": ctx.get("data_version", ""),
            "etapa": etapa, "gatilho": ctx.get("gatilho", "local"),
            "github_run_id": ctx.get("github_run_id", "")}
    tags.update(tags_extra or {})
    with mlflow.start_run(run_name=f"{ctx['cycle_id']}__{nome}") as r:
        mlflow.set_tags(tags)
        yield r


def historico_runs(cfg: dict):
    """Todas as runs do experimento (DataFrame) - prova de histórico recuperável entre ciclos."""
    return mlflow.search_runs(experiment_names=[cfg["projeto"]["experimento_mlflow"]])


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("comando", choices=["rebase"], help="rebase: ajusta caminhos do mlruns para esta máquina")
    ap.parse_args()
    print("meta.yaml ajustados:", rebase_mlruns())
