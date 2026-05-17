# analise_fundamentalista.py
import pandas as pd
import numpy as np


# Mapeamento centralizado: nome semântico → coluna real do fundamentus
COL = {
    "dy":         "dy",
    "cotacao":    "cotacao",
    "pl":         "pl",
    "pvp":        "pvp",
    "roe":        "roe",
    "roic":       "roic",
    "mrgebit":    "mrgebit",
    "mrgliq":     "mrgliq",
    "patrliq":    "patrliq",
    "divbpatr":   "divbpatr",
    "liq2m":      "liq2m",
    "evebit":     "evebit",
    "evebitda":   "evebitda",
    "c5y":        "c5y",
    "lpa":        "lpa",   # nem sempre disponível
    "vpa":        "vpa",   # nem sempre disponível
}


def _col(df: pd.DataFrame, nome: str):
    """Retorna o nome de coluna correto, testando maiúsculas e minúsculas."""
    candidatos = [nome, nome.lower(), nome.upper()]
    for c in candidatos:
        if c in df.columns:
            return c
    return None


class AnaliseFundamentalista:

    def __init__(self, dados_fundamentalistas: pd.DataFrame):
        self.dados = dados_fundamentalistas

    # ──────────────────────────────────────────────────────────
    # RANKING DIVIDEND YIELD
    # ──────────────────────────────────────────────────────────

    def ranking_dividend_yield(self, top_n: int = 20) -> pd.DataFrame:
        """Ranking das melhores pagadoras de dividendos."""
        if self.dados.empty:
            return pd.DataFrame()

        dy_col      = _col(self.dados, "dy")
        patrliq_col = _col(self.dados, "patrliq")
        roe_col     = _col(self.dados, "roe")

        if dy_col is None:
            print(f"❌ Coluna DY não encontrada. Colunas disponíveis: {list(self.dados.columns)}")
            return pd.DataFrame()

        filtros = self.dados[dy_col] > 0.03   # DY > 3%

        if roe_col:
            filtros &= self.dados[roe_col] > 0.05

        if patrliq_col:
            filtros &= self.dados[patrliq_col] > 0

        boas_pagadoras = self.dados[filtros].copy()
        ranking = boas_pagadoras.sort_values(dy_col, ascending=False).head(top_n)

        # Monta DataFrame de exibição com as colunas disponíveis
        colunas_exibir = {}
        for alias, col_key in [
            ("Cotação",    "cotacao"),
            ("DY",         "dy"),
            ("ROE",        "roe"),
            ("P/L",        "pl"),
            ("P/VP",       "pvp"),
            ("Mrg EBIT",   "mrgebit"),
            ("Mrg Liq",    "mrgliq"),
            ("Patrim Liq", "patrliq"),
        ]:
            real = _col(self.dados, col_key)
            if real:
                colunas_exibir[real] = alias

        df_result = ranking[list(colunas_exibir.keys())].rename(columns=colunas_exibir)
        return df_result

    # ──────────────────────────────────────────────────────────
    # FILTRO MÉTODO BAZIN
    # ──────────────────────────────────────────────────────────

    def filtrar_metodo_bazin(self) -> pd.DataFrame:
        """Aplica os critérios do Método Décio Bazin."""
        if self.dados.empty:
            return pd.DataFrame()

        dy_col      = _col(self.dados, "dy")
        mrgebit_col = _col(self.dados, "mrgebit")
        roe_col     = _col(self.dados, "roe")
        patrliq_col = _col(self.dados, "patrliq")
        divbpatr_col = _col(self.dados, "divbpatr")

        if dy_col is None:
            print("❌ Coluna DY não encontrada.")
            return pd.DataFrame()

        filtros = self.dados[dy_col] > 0.06  # DY > 6%

        if mrgebit_col:
            filtros &= self.dados[mrgebit_col] > 0.10
        if roe_col:
            filtros &= self.dados[roe_col] > 0.10
        if patrliq_col:
            filtros &= self.dados[patrliq_col] > 0
        if divbpatr_col:
            filtros &= self.dados[divbpatr_col] < 0.5

        empresas_bazin = self.dados[filtros].copy()
        empresas_bazin = empresas_bazin.sort_values(dy_col, ascending=False)

        # Renomeia para exibição
        rename_map = {}
        for col_key, alias in [
            ("cotacao",  "Cotação"),
            ("dy",       "DY"),
            ("roe",      "ROE"),
            ("mrgebit",  "Mrg EBIT"),
            ("divbpatr", "Dív/Patrim"),
        ]:
            real = _col(self.dados, col_key)
            if real:
                rename_map[real] = alias

        cols_disp = [c for c in rename_map.keys() if c in empresas_bazin.columns]
        return empresas_bazin[cols_disp].rename(columns=rename_map)

    # ──────────────────────────────────────────────────────────
    # VALOR INTRÍNSECO — GRAHAM
    # ──────────────────────────────────────────────────────────

    def calcular_valor_intrinseco(self, ticker: str, metodo: str = "graham"):
        """Calcula valor intrínseco pela fórmula de Graham: √(22.5 × LPA × VPA)."""
        try:
            empresa = self.dados[self.dados.index == ticker]
            if empresa.empty:
                return None

            lpa_col = _col(self.dados, "lpa")
            vpa_col = _col(self.dados, "vpa")

            if lpa_col is None or vpa_col is None:
                print(f"⚠️ Colunas LPA/VPA não disponíveis para cálculo Graham.")
                return None

            lpa = empresa[lpa_col].iloc[0]
            vpa = empresa[vpa_col].iloc[0]

            if metodo == "graham":
                valor = np.sqrt(22.5 * abs(lpa) * abs(vpa))
                return round(valor, 2)

        except Exception as e:
            print(f"❌ Erro ao calcular valor intrínseco de {ticker}: {e}")
            return None

    # ──────────────────────────────────────────────────────────
    # ANÁLISE SETORIAL
    # ──────────────────────────────────────────────────────────

    def analise_setorial(self) -> pd.DataFrame:
        """Análise agregada por faixa de P/L."""
        if self.dados.empty:
            return pd.DataFrame()

        pl_col  = _col(self.dados, "pl")
        dy_col  = _col(self.dados, "dy")
        roe_col = _col(self.dados, "roe")
        pvp_col = _col(self.dados, "pvp")

        if pl_col is None:
            return pd.DataFrame()

        agg = {col: "mean" for col in [dy_col, roe_col, pl_col, pvp_col] if col}
        agg_result = (
            self.dados
            .groupby(self.dados[pl_col].round(0))
            .agg(agg | {pl_col: "count"})
        )
        agg_result.rename(columns={pl_col: "Qtd_Empresas"}, inplace=True)
        return agg_result.round(4)
