"""Entrada e versionamento de dados.

Como chegam dados novos (definido na Etapa 1):
  (a) arquivo CSV depositado em data/incoming/ (ex.: exportação do sistema de origem), ou
  (b) simulação: a cada ciclo agendado o gerador cria o próximo lote (src/simulador.py).
Cada lote vira data/raw/lote_NNN.csv, imutável e versionado no Git. A data_version é um
hash do conjunto consolidado e deduplicado, então muda sempre que o dado muda.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

from .config import carregar_config, dir_, p
from .simulador import ALVO, COLUNAS, gerar_lote

PADRAO_LOTE = re.compile(r"lote_(\d{3})\.csv$")


def listar_lotes(cfg: dict) -> list[Path]:
    d = dir_(cfg, "dir_raw")
    return sorted(f for f in d.glob("lote_*.csv") if PADRAO_LOTE.search(f.name))


def indice_do_lote(caminho: Path) -> int:
    return int(PADRAO_LOTE.search(caminho.name).group(1))


def carregar_bruto(cfg: dict) -> pd.DataFrame:
    """Concatena todos os lotes de data/raw (sem tratar nada), com a coluna 'lote'."""
    partes = []
    for f in listar_lotes(cfg):
        d = pd.read_csv(f)
        d["lote"] = indice_do_lote(f)
        partes.append(d)
    if not partes:
        raise FileNotFoundError("Nenhum lote em data/raw. Rode: python -m src.ingestao --inicial")
    return pd.concat(partes, ignore_index=True)


def _validar_esquema(df: pd.DataFrame, origem: str) -> None:
    faltando = [c for c in COLUNAS + [ALVO] if c not in df.columns]
    if faltando:
        raise ValueError(f"Lote '{origem}' fora do esquema esperado; colunas ausentes: {faltando}")


def gerar_lote_inicial(cfg: dict) -> Path:
    """Cria o lote 000 (dados iniciais). Só roda se ainda não existir nenhum lote."""
    sim = cfg["simulacao"]
    if listar_lotes(cfg):
        raise RuntimeError("Já existem lotes em data/raw; o lote inicial não será recriado.")
    df = gerar_lote(sim["tamanho_lote_inicial"], 0, sim["seed_base"], id_inicial=100_000)
    destino = dir_(cfg, "dir_raw") / "lote_000.csv"
    df.to_csv(destino, index=False)
    return destino


def _reenviar_registros_antigos(novo: pd.DataFrame, cfg: dict, seed: int) -> pd.DataFrame:
    """Simula a realidade de um sistema de origem que reenvia registros já entregues."""
    n = cfg["ingestao"].get("reenvio_registros", 0)
    antigos = carregar_bruto(cfg).drop(columns=["lote"])
    if n <= 0 or antigos.empty:
        return novo
    reenvio = antigos.sample(n=min(n, len(antigos)), random_state=seed)
    return pd.concat([novo, reenvio], ignore_index=True)


def ingerir_novos_dados(cfg: dict, ha_ciclo_anterior: bool) -> dict:
    """Incorpora dados novos ao data/raw. Retorna um dicionário descrevendo o que entrou.

    No primeiro ciclo (sem ciclo anterior) nada é adicionado: o ciclo inicial usa só o lote 000.
    """
    info = {"origem": "nenhuma", "arquivo": None, "linhas_recebidas": 0, "indice_lote": None}
    lotes = listar_lotes(cfg)
    if not lotes:
        raise FileNotFoundError("data/raw vazio. Gere o lote inicial: python -m src.ingestao --inicial")
    if not ha_ciclo_anterior:
        info["motivo"] = "ciclo inicial: usa apenas os dados já presentes em data/raw"
        return info

    proximo = indice_do_lote(lotes[-1]) + 1
    destino = dir_(cfg, "dir_raw") / f"lote_{proximo:03d}.csv"
    incoming = sorted(dir_(cfg, "dir_incoming").glob("*.csv"))
    modo = cfg["ingestao"]["modo"]

    if incoming and modo in ("auto", "arquivos"):
        arq = incoming[0]
        df = pd.read_csv(arq)
        _validar_esquema(df, arq.name)
        df[COLUNAS + [ALVO]].to_csv(destino, index=False)
        arq.rename(arq.with_suffix(".csv.processado"))
        info.update(origem="arquivo", arquivo=arq.name, linhas_recebidas=len(df), indice_lote=proximo)
    elif modo in ("auto", "simulado") and cfg["simulacao"]["ativa"] and proximo <= cfg["simulacao"]["max_lotes"]:
        sim = cfg["simulacao"]
        seed = sim["seed_base"] + proximo
        df = gerar_lote(sim["tamanho_lote"], proximo, seed, id_inicial=100_000 * (proximo + 1))
        df = _reenviar_registros_antigos(df, cfg, seed)
        df.to_csv(destino, index=False)
        info.update(origem="simulado", arquivo=destino.name, linhas_recebidas=len(df), indice_lote=proximo)
    else:
        info["motivo"] = "sem dados novos neste ciclo"
    return info


def gerar_registros_producao(cfg: dict, indice: int) -> Path:
    """Registros SEM rótulo (clientes a pontuar em produção) para o notebook 05.

    Usam ids de outra faixa, logo nunca participam de treino, validação ou teste.
    """
    sim = cfg["simulacao"]
    df = gerar_lote(sim["tamanho_scoring"], indice, sim["seed_base"] + 5000 + indice,
                    id_inicial=9_000_000 + 1000 * indice, com_alvo=False, sujeira=True)
    destino = dir_(cfg, "dir_scoring") / f"scoring_lote_{indice:03d}.csv"
    df.to_csv(destino, index=False)
    return destino


def calcular_data_version(df_limpo: pd.DataFrame, n_lotes: int, id_col: str) -> str:
    """vNNN_<hash>: NNN = nº de lotes; hash = conteúdo do conjunto consolidado e deduplicado."""
    import hashlib

    base = df_limpo.sort_values(id_col).reset_index(drop=True)
    h = hashlib.sha256(pd.util.hash_pandas_object(base, index=False).values.tobytes()).hexdigest()[:10]
    return f"v{n_lotes:03d}_{h}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Utilitários de ingestão")
    ap.add_argument("--inicial", action="store_true", help="gera data/raw/lote_000.csv")
    a = ap.parse_args()
    cfg = carregar_config()
    if a.inicial:
        print("Lote inicial criado em", gerar_lote_inicial(cfg))
