"""Leitura da configuração e caminhos do projeto (sempre relativos à raiz do repositório)."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def carregar_config(caminho: str | Path | None = None) -> dict:
    caminho = Path(caminho) if caminho else RAIZ / "config" / "config.yaml"
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def p(*partes: str) -> Path:
    """Caminho absoluto a partir da raiz do projeto."""
    return RAIZ.joinpath(*partes)


def dir_(cfg: dict, chave: str) -> Path:
    d = p(cfg["dados"][chave])
    d.mkdir(parents=True, exist_ok=True)
    return d


def ler_json(caminho: Path, padrao=None):
    caminho = Path(caminho)
    if not caminho.exists():
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def gravar_json(caminho: Path, obj) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
