"""Imprime em Markdown as tabelas do relatório a partir das evidências REAIS do repositório.

Uso:  python scripts/tabelas_relatorio.py [cycle_id]     (padrão: último ciclo do histórico)
Cole a saída no relatório (votação, comparação dos modelos, decisão, histórico, drift).
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.config import ler_json  # noqa: E402


def md(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return cab + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in df.itertuples(index=False))


def main() -> None:
    hist = pd.read_csv(RAIZ / "evidencias" / "historico_ciclos.csv")
    cid = sys.argv[1] if len(sys.argv) > 1 else hist["cycle_id"].iloc[-1]
    ev = RAIZ / "evidencias" / cid
    aud = ler_json(ev / "decisao.json")

    print(f"## Histórico de ciclos\n")
    print(md(hist[["cycle_id", "gatilho", "data_version", "n_linhas", "vencedor", "f1_cv_A", "f1_cv_B", "f1_teste_vencedor",
                   "f1_teste_vigente_anterior", "decisao", "drift_alerta"]]))

    v = pd.read_csv(ev / "tabela_votos.csv")
    v = v[["feature", "voto_selectkbest_mi", "voto_random_forest", "voto_rfe_logreg", "votos", "eleita"]].head(20)
    print(f"\n## Tabela de votação ({cid})\n")
    print(md(v))

    print(f"\n## Comparação dos dois modelos ({cid}), CV F1 macro\n")
    cv = pd.DataFrame({k: aud["cv"][k] for k in aud["cv"]}).T.round(4).reset_index(names="modelo")
    print(md(cv))

    print(f"\n## Decisão de promoção ({cid})\n")
    d = aud["decisao"]
    print(md(pd.DataFrame([{k: (round(x, 4) if isinstance(x, float) else x) for k, x in d.items()}])))

    if (ev / "drift_report.csv").exists():
        dr = pd.read_csv(ev / "drift_report.csv")[["atributo", "tipo", "psi", "ks_estatistica", "status"]].head(8).round(3)
        print(f"\n## Drift ({cid})\n")
        print(md(dr))


if __name__ == "__main__":
    main()
