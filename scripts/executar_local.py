"""Executa o pipeline completo localmente (01 -> 05), igual ao workflow do GitHub Actions.

Uso (na raiz do projeto):  python scripts/executar_local.py
Cada execução = 1 ciclo. Rode duas ou mais vezes para ver o histórico, a promoção/manutenção e o drift.
"""
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NOTEBOOKS = ["01_etl", "02_votacao_features", "03_treino_competicao", "04_selecao_promocao", "05_previsoes"]


def main() -> None:
    os.chdir(RAIZ)
    env = dict(os.environ, PIPELINE_TRIGGER=os.environ.get("PIPELINE_TRIGGER", "local"))
    subprocess.run([sys.executable, "-m", "src.rastreio", "rebase"], check=True, env=env)
    for nb in NOTEBOOKS:
        print(f"\n=== {nb} ===", flush=True)
        subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
                        f"notebooks/{nb}.ipynb", "--output", f"{nb[:2]}_executado.ipynb",
                        "--output-dir", "evidencias/notebooks_executados",
                        "--ExecutePreprocessor.timeout=1800"], check=True, env=env)   # falhou? interrompe o ciclo
    subprocess.run([sys.executable, "-m", "src.resumo_ciclo"], check=True, env=env)


if __name__ == "__main__":
    main()
