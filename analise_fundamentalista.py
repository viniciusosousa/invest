# analise_fundamentalista.py
import pandas as pd
import numpy as np

def _col(df: pd.DataFrame, nome: str):
    """Retorna o nome de coluna correto, testando maiúsculas e minúsculas."""

    # Mapeamento centralizado: nome semântico → coluna real do fundamentus
    COL = {
        "dy":         ["dy","Div.Yield"],
        "cotacao":    ["cotacao","Cotação"],
        "pl":         ["pl", "P/L"],
        "pvp":        ["pvp","P/VP"],
        "roe":        ["roe","ROE"],
        "roic":       ["roic","ROIC"],
        "mrgebit":    ["mrgebit","Mrg Ebit"],
        "mrgliq":     ["mrgliq","Mrg. Líq."],
        "patrliq":    ["patrliq","Patrim. Líq"],
        "divbpatr":   ["divbpatr","Dív.Líq/ Patrim."],
        "liq2m":      ["liq2m","Liq.2meses"],
        "evebit":     ["evebit","EV/EBIT"],
        "evebitda":   ["evebitda","EV/EBITDA"],
        "c5y":        ["c5y","Cresc. Rec.5a"],
        "l2m":        ["l2m","Liq.2meses"],
        "lpa":        ["lpa","lpa"],   # nem sempre disponível
        "vpa":        ["vpa","vpa"],   # nem sempre disponível
    }
    candidatos = [COL[nome][0], COL[nome][0].lower(), COL[nome][0].upper(), COL[nome][1], COL[nome][1].lower(), COL[nome][1].upper()]
    for c in candidatos:
        if c in df.columns:
            return c
    return None


class AnaliseFundamentalista:

    def __init__(self, dados_fundamentalistas: pd.DataFrame):
        self.dados = dados_fundamentalistas
        divbpatr_col = _col(self.dados, "divbpatr")
        self.dados[divbpatr_col] = pd.to_numeric(self.dados[divbpatr_col], errors='coerce')

    # ──────────────────────────────────────────────────────────
    # RANKING DIVIDEND YIELD
    # ──────────────────────────────────────────────────────────

    def ranking_dividend_yield(self, top_n: int = 20, min_dy: float = 0.03, min_roe: float = 0.05, min_patrliq: float = 0) -> pd.DataFrame:
        """Ranking das melhores pagadoras de dividendos."""
        if self.dados.empty:
            return pd.DataFrame()

        dy_col      = _col(self.dados, "dy")
        patrliq_col = _col(self.dados, "patrliq")
        roe_col     = _col(self.dados, "roe")
        l2m_col     = _col(self.dados, "l2m")

        if dy_col is None:
            print(f"❌ Coluna DY não encontrada. Colunas disponíveis: {list(self.dados.columns)}")
            return pd.DataFrame()

        filtros = self.dados[dy_col] > min_dy   # DY > min_dy

        if roe_col:
            filtros &= self.dados[roe_col] > min_roe

        if patrliq_col:
            filtros &= self.dados[patrliq_col] > min_patrliq

        if l2m_col:
            filtros &= self.dados[l2m_col] > 0  # Liquidez > 0

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

    def filtrar_metodo_bazin(self, selic: float = 14.0, min_mrgebit: float = 0.10, min_roe: float = 0.10, min_patrliq: float = 0, max_divbpatr: float = 0.5 ) -> pd.DataFrame:
        """Aplica os critérios do Método Décio Bazin."""
        if self.dados.empty:
            return pd.DataFrame()

        dy_col      = _col(self.dados, "dy")
        mrgebit_col = _col(self.dados, "mrgebit")
        roe_col     = _col(self.dados, "roe")
        patrliq_col = _col(self.dados, "patrliq")
        divbpatr_col = _col(self.dados, "divbpatr")
        l2m_col     = _col(self.dados, "l2m")

        if dy_col is None:
            print("❌ Coluna DY não encontrada.")
            return pd.DataFrame()

        filtros = self.dados[dy_col] > selic * 0.6  # 60% da Selic
        
        if mrgebit_col:
            filtros &= self.dados[mrgebit_col] > min_mrgebit
        if roe_col:
            filtros &= self.dados[roe_col] > min_roe
        if patrliq_col:
            filtros &= self.dados[patrliq_col] > min_patrliq
        if divbpatr_col:
            filtros &= self.dados[divbpatr_col] < max_divbpatr
        if l2m_col:
            filtros &= self.dados[l2m_col] > 0  # Liquidez > 0

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
