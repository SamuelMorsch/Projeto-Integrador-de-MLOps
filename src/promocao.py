"""Eleição do vencedor do ciclo e promoção controlada frente ao modelo vigente."""
from __future__ import annotations

import shutil
from pathlib import Path

from .config import gravar_json, ler_json, p

MANIFESTO = p("models", "modelo_vigente.json")


def eleger_vencedor(cfg: dict, resultados_cv: dict) -> dict:
    """Vence quem tem maior média de CV na métrica principal; diferença < epsilon = empate (vence o A, mais simples)."""
    m = cfg["avaliacao"]["metrica"]
    eps = cfg["avaliacao"]["empate_epsilon"]
    a, b = resultados_cv["modelo_A"]["media"][m], resultados_cv["modelo_B"]["media"][m]
    sinal = 1 if cfg["avaliacao"]["direcao"] == "maximizar" else -1
    if abs(a - b) < eps:
        vencedor, motivo = "modelo_A", f"empate técnico (|diferença| < {eps}); vence o modelo mais simples"
    elif sinal * (a - b) > 0:
        vencedor, motivo = "modelo_A", "maior média de CV"
    else:
        vencedor, motivo = "modelo_B", "maior média de CV"
    return {"vencedor": vencedor, "motivo": motivo, "cv_A": a, "cv_B": b, "metrica": m}


def ler_manifesto() -> dict | None:
    return ler_json(MANIFESTO, None)


def decidir_promocao(cfg: dict, cv_vencedor: float, teste_vencedor: float, teste_vigente: float | None) -> dict:
    """Regra objetiva e auditável (ver config.yaml > promocao). Não depende de MLflow nem do runner anterior."""
    pr = cfg["promocao"]
    sinal = 1 if cfg["avaliacao"]["direcao"] == "maximizar" else -1
    out = {"piso_metrica_cv": pr["piso_metrica_cv"], "limiar_melhoria": pr["limiar_melhoria"],
           "cv_vencedor": cv_vencedor, "teste_vencedor": teste_vencedor, "teste_vigente": teste_vigente,
           "delta_teste": None}
    if sinal * (cv_vencedor - pr["piso_metrica_cv"]) < 0:
        return {**out, "decisao": "mantido", "motivo": "vencedor abaixo do piso mínimo de CV"}
    if teste_vigente is None:
        return {**out, "decisao": "promovido", "motivo": "não havia modelo vigente (primeiro ciclo)"}
    delta = sinal * (teste_vencedor - teste_vigente)
    out["delta_teste"] = float(delta)
    if delta >= pr["limiar_melhoria"]:
        return {**out, "decisao": "promovido",
                "motivo": f"melhora de {delta:.4f} >= limiar {pr['limiar_melhoria']}"}
    return {**out, "decisao": "mantido",
            "motivo": f"melhora de {delta:.4f} < limiar {pr['limiar_melhoria']}; vigente preservado"}


def promover(cfg: dict, ctx: dict, caminho_candidato: Path, info_vencedor: dict, decisao: dict) -> dict:
    """Copia o modelo para models/historico/ (anteriores são preservados) e reescreve o manifesto."""
    modelo_id = f"{ctx['cycle_id']}_{info_vencedor['algoritmo']}"
    destino = p("models", "historico", f"{modelo_id}.joblib")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(caminho_candidato, destino)
    manifesto = {
        "modelo_id": modelo_id,
        "algoritmo": info_vencedor["algoritmo"],
        "chave": info_vencedor["vencedor"],
        "cycle_id": ctx["cycle_id"],
        "data_version": ctx["data_version"],
        "features": info_vencedor["features"],
        "metrica": cfg["avaliacao"]["metrica"],
        "valor_cv": decisao["cv_vencedor"],
        "valor_teste": decisao["teste_vencedor"],
        "run_id": info_vencedor["run_id"],
        "caminho_modelo": f"models/historico/{modelo_id}.joblib",
        "promovido_em_utc": ctx.get("fim_utc"),
        "decisao": decisao["decisao"],
        "motivo": decisao["motivo"],
        "modelo_anterior": (ler_manifesto() or {}).get("modelo_id"),
        "ultima_avaliacao": _resumo_avaliacao(ctx, decisao),
    }
    gravar_json(MANIFESTO, manifesto)
    return manifesto


def _resumo_avaliacao(ctx: dict, decisao: dict) -> dict:
    return {"cycle_id": ctx["cycle_id"], "data_version": ctx["data_version"], "decisao": decisao["decisao"],
            "motivo": decisao["motivo"], "teste_candidato": decisao["teste_vencedor"],
            "teste_vigente": decisao["teste_vigente"], "delta_teste": decisao["delta_teste"]}


def manter(ctx: dict, decisao: dict) -> dict:
    """Vigente preservado: só registra, no manifesto, a avaliação feita neste ciclo."""
    manifesto = ler_manifesto()
    if manifesto is None:
        raise RuntimeError("Manutenção sem modelo vigente: não deveria ocorrer (o primeiro ciclo promove).")
    manifesto["ultima_avaliacao"] = _resumo_avaliacao(ctx, decisao)
    gravar_json(MANIFESTO, manifesto)
    return manifesto
