"""Gerador de dados SINTÉTICOS de churn de clientes (provedor de internet fictício).

Por que sintético: o enunciado permite dados públicos, sintéticos ou autorizados, e a
simulação nos dá controle de (a) lotes que chegam a cada ciclo do pipeline, (b) sujeira
realista para a etapa de ETL e (c) mudanças graduais/estruturais na distribuição (drift),
que são o que faz a regra de promoção e o monitoramento do critério 10 terem o que decidir.

Determinístico: o mesmo (indice_lote, seed) sempre gera o mesmo lote.
Sem dados pessoais reais.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

COLUNAS = [
    "id_cliente", "idade", "regiao", "plano", "tipo_contrato", "forma_pagamento",
    "tempo_contrato_meses", "mensalidade", "num_servicos", "uso_dados_gb",
    "chamados_suporte_3m", "atraso_pagamentos_6m", "satisfacao",
    "numero_dependentes", "dia_semana_cadastro",
]
ALVO = "churn"


def _norm(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, None)
    return p / p.sum()


def gerar_lote(n: int, indice_lote: int, seed: int, id_inicial: int,
               com_alvo: bool = True, sujeira: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    i = int(indice_lote)
    choque = 1.0 if i >= 3 else 0.0  # a partir do lote 3: campanha de preços + mais chamados (mudança estrutural)

    idade = np.clip(rng.normal(43, 13, n), 18, 85).round().astype(int)
    regiao = rng.choice(["Sul", "Sudeste", "Centro-Oeste", "Nordeste", "Norte"], size=n,
                        p=[0.22, 0.38, 0.12, 0.20, 0.08])

    p_prem = min(0.20 + 0.03 * i, 0.38)
    plano = rng.choice(["basico", "intermediario", "premium"], size=n,
                       p=_norm([0.42, 1 - 0.42 - p_prem, p_prem]))
    p_mensal = min(0.45 + 0.01 * i, 0.55)
    tipo = rng.choice(["mensal", "anual", "bianual"], size=n,
                      p=_norm([p_mensal, 0.35, 1 - p_mensal - 0.35]))
    p_pix = min(0.15 + 0.04 * i, 0.40)
    forma = rng.choice(["boleto", "cartao", "debito", "pix"], size=n,
                       p=_norm([0.30 - p_pix / 3, 0.35 - p_pix / 3, 0.20 - p_pix / 3, p_pix]))

    tempo = np.clip(rng.gamma(2.0, 14.0, n), 1, 110).round().astype(int)
    base = pd.Series(plano).map({"basico": 70.0, "intermediario": 110.0, "premium": 170.0}).to_numpy()
    mensalidade = (base + rng.normal(0, 12, n)) * (1 + 0.008 * i) * (1.10 if choque else 1.0)
    mensalidade = mensalidade.round(2)
    lam_serv = 1.2 + 0.3 * (plano == "intermediario") + 0.6 * (plano == "premium")
    num_serv = np.clip(1 + rng.poisson(lam_serv), 1, 7)
    idx_plano = pd.Series(plano).map({"basico": 0, "intermediario": 1, "premium": 2}).to_numpy()
    uso = rng.lognormal(np.log(90 + 55 * idx_plano), 0.5, n) * (1 + 0.03 * i)
    uso = uso.round(1)
    chamados = rng.poisson(0.9 + 0.08 * i + 0.25 * choque, n)
    atraso = np.clip(rng.poisson(0.30 + 0.35 * (forma == "boleto")), 0, 6)
    satisf = np.clip(np.round(4.0 - 0.35 * chamados + rng.normal(0, 0.9, n)), 1, 5).astype(int)
    dependentes = np.clip(rng.poisson(1.1, n), 0, 6)
    dia = rng.choice(["seg", "ter", "qua", "qui", "sex", "sab", "dom"], size=n)

    ids = np.arange(id_inicial, id_inicial + n)
    df = pd.DataFrame({
        "id_cliente": ids, "idade": idade, "regiao": regiao, "plano": plano,
        "tipo_contrato": tipo, "forma_pagamento": forma, "tempo_contrato_meses": tempo,
        "mensalidade": mensalidade, "num_servicos": num_serv, "uso_dados_gb": uso,
        "chamados_suporte_3m": chamados, "atraso_pagamentos_6m": atraso,
        "satisfacao": satisf, "numero_dependentes": dependentes, "dia_semana_cadastro": dia,
    })

    if com_alvo:
        # Mecanismo gerador do churn. Parte do efeito muda com o lote (concept drift):
        # a antiguidade protege cada vez menos e os chamados pesam cada vez mais.
        w_tempo = max(0.50, 1 - 0.05 * i)
        ganho = 1.6  # intensidade do sinal: quanto maior, mais previsível é o churn
        z = (-2.15
             + ganho * (0.85 * (tipo == "mensal") - 0.70 * (tipo == "bianual")
                        - 0.028 * tempo * w_tempo
                        + 0.007 * (mensalidade - 100)
                        + 0.38 * chamados * (1 + 0.03 * i)
                        + 0.45 * atraso
                        - 0.22 * (num_serv - 2)
                        + 0.55 * (satisf <= 2)
                        + 0.35 * (forma == "pix") * (i >= 2)
                        - 0.012 * (idade - 43))
             + rng.normal(0, 0.4, n))
        prob = 1 / (1 + np.exp(-z))
        df[ALVO] = (rng.random(n) < prob).astype(int)

    if sujeira:
        df = _injetar_sujeira(df, rng)
    return df


def _injetar_sujeira(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Problemas típicos de dados reais: ausentes, valores impossíveis, outliers e duplicatas."""
    df = df.copy()
    n = len(df)

    def amostra(frac):
        return rng.choice(n, size=max(1, int(n * frac)), replace=False)

    df.loc[amostra(0.030), "satisfacao"] = np.nan
    df.loc[amostra(0.020), "uso_dados_gb"] = np.nan
    df["forma_pagamento"] = df["forma_pagamento"].astype(object)
    df.loc[amostra(0.015), "forma_pagamento"] = None
    df.loc[amostra(0.006), "idade"] = rng.choice([-3, 0, 150, 999], size=max(1, int(n * 0.006)))
    df.loc[amostra(0.004), "tempo_contrato_meses"] = -1
    df.loc[amostra(0.003), "mensalidade"] = rng.choice([0.0, -50.0], size=max(1, int(n * 0.003)))
    df.loc[amostra(0.004), "uso_dados_gb"] = rng.uniform(4000, 9000, size=max(1, int(n * 0.004))).round(1)
    dup = df.iloc[rng.choice(n, size=max(1, int(n * 0.015)), replace=False)]
    return pd.concat([df, dup], ignore_index=True)
