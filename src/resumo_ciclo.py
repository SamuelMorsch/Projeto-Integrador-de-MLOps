"""Resumo do ciclo para o GitHub Actions: Job Summary, outputs do step e texto do alerta de drift.

Uso (no workflow, depois do notebook 05):  python -m src.resumo_ciclo
Fora do Actions apenas imprime o resumo.
"""
from __future__ import annotations

import os

from .config import carregar_config, ler_json, p
from .ciclo import carregar_contexto, dir_evidencias


def montar_resumo(ctx: dict, aud: dict) -> str:
    d, dr = aud["decisao"], aud.get("drift") or {}
    linhas = [
        f"## Ciclo `{ctx['cycle_id']}`",
        f"- **Gatilho:** `{ctx['gatilho']}`" + (f" (run {ctx['github_run_id']})" if ctx.get("github_run_id") else ""),
        f"- **data_version:** `{ctx['data_version']}` | lotes: {ctx['n_lotes']} | linhas: {ctx['n_linhas']}",
        f"- **Features eleitas ({len(aud['features_eleitas'])}):** " + ", ".join(f"`{f}`" for f in aud["features_eleitas"]),
        f"- **CV (F1 macro):** A = {aud['eleicao_vencedor']['cv_A']:.4f} | B = {aud['eleicao_vencedor']['cv_B']:.4f} "
        f"-> vencedor do ciclo: **{aud['eleicao_vencedor']['vencedor']}**",
        f"- **Teste:** vencedor = {d['teste_vencedor']:.4f}" + (f" | vigente anterior = {d['teste_vigente']:.4f}" if d["teste_vigente"] is not None else ""),
        f"- **Decisão:** **{d['decisao'].upper()}**, {d['motivo']}",
        f"- **Modelo vigente agora:** `{aud['modelo_vigente_apos_ciclo']}`",
    ]
    if dr.get("avaliado"):
        linhas.append(f"- **Drift:** PSI máx. = {dr['max_psi']:.3f} (`{dr['atributo_max_psi']}`) | atributos em alerta: "
                      f"{dr['n_features_alerta']} | {'ALERTA' if dr['alerta'] else 'sem alerta'}")
    else:
        linhas.append(f"- **Drift:** não avaliado ({dr.get('motivo', '-')})")
    return "\n".join(linhas) + "\n"


def texto_alerta(ctx: dict, dr: dict) -> str:
    return (f"### Alerta de drift de dados\n\nO lote incorporado no ciclo `{ctx['cycle_id']}` (`{ctx['data_version']}`) "
            f"mudou em relação ao histórico.\n\n- PSI máximo: **{dr['max_psi']:.3f}** em `{dr['atributo_max_psi']}`\n"
            f"- Atributos em alerta (PSI >= limite): {', '.join(dr['features_em_alerta'])}\n"
            f"- Taxa de churn: histórico {dr['taxa_alvo_ref']:.1%} -> lote novo {dr['taxa_alvo_novo']:.1%}\n\n"
            f"Relatório completo: `evidencias/{ctx['cycle_id']}/drift_report.csv`. "
            "O pipeline retreinou e aplicou a regra de promoção normalmente; verifique se o vigente continua adequado.\n")


def main() -> None:
    cfg = carregar_config()
    ctx = carregar_contexto(cfg)
    ev = dir_evidencias(ctx)
    aud = ler_json(ev / "decisao.json")
    md = montar_resumo(ctx, aud)
    (ev / "resumo_ciclo.md").write_text(md, encoding="utf-8")
    print(md)

    dr = aud.get("drift") or {}
    alerta = bool(dr.get("alerta"))
    arq_alerta = ""
    if alerta:
        arq_alerta = str((ev / "alerta_drift.md").relative_to(p()))
        (ev / "alerta_drift.md").write_text(texto_alerta(ctx, dr), encoding="utf-8")
        print(f"::warning title=Drift de dados detectado::PSI max {dr['max_psi']:.3f} em {dr['atributo_max_psi']} (ciclo {ctx['cycle_id']})")

    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"cycle_id={ctx['cycle_id']}\ndecisao={aud['decisao']['decisao']}\n"
                    f"drift_alerta={'true' if alerta else 'false'}\narquivo_alerta={arq_alerta}\n")


if __name__ == "__main__":
    main()
