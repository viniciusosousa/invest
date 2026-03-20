import pandas as pd
import numpy as np

class AnaliseFundamentalista:
    def __init__(self, dados_fundamentalistas):
        self.dados = dados_fundamentalistas
    
    def filtrar_metodo_bazin(self):
        """Aplica critérios do Método Décio Bazin"""
        if self.dados.empty:
            return pd.DataFrame()
        
        # Critérios Bazin
        filtros = (
            (self.dados['Div.Yield'] > 0.06) &  # Dividend Yield > 6%
            (self.dados['Mrg Ebit'] > 0.10) &   # Margem EBIT > 10%
            (self.dados['ROE'] > 0.10) &        # ROE > 10%
            (self.dados['Patrim.Liq'] > 0) &    # Patrimônio Líquido positivo
            (self.dados['Div.Br/Patrim'] < 0.5) # Dívida/Patrimônio < 50%
        )
        
        empresas_bazin = self.dados[filtros].copy()
        empresas_bazin = empresas_bazin.sort_values('Div.Yield', ascending=False)
        
        return empresas_bazin
    
    def calcular_valor_intrinseco(self, ticker, metodo='graham'):
        """Calcula valor intrínseco usando fórmula de Graham"""
        try:
            empresa = self.dados[self.dados.index == ticker]
            if empresa.empty:
                return None
            
            lpa = empresa['LPA'].iloc[0]
            vpa = empresa['VPA'].iloc[0]
            
            if metodo == 'graham':
                # Fórmula de Graham: VI = √(22.5 × LPA × VPA)
                valor_intrinseco = np.sqrt(22.5 * abs(lpa) * abs(vpa))
                return valor_intrinseco
            
        except Exception as e:
            print(f"Erro ao calcular valor intrínseco de {ticker}: {e}")
            return None
    
    def ranking_dividend_yield(self, top_n=20):
        """Ranking das melhores pagadoras de dividendos"""
        if self.dados.empty:
            return pd.DataFrame()
        
        # Filtrar apenas empresas com dividend yield positivo
        boas_pagadoras = self.dados[
            (self.dados['Div.Yield'] > 0.03) &  # DY > 3%
            (self.dados['Patrim.Liq'] > 0) &    # Patrimônio positivo
            (self.dados['ROE'] > 0.05)          # ROE > 5%
        ].copy()
        
        # Ordenar por dividend yield
        ranking = boas_pagadoras.sort_values('Div.Yield', ascending=False).head(top_n)
        
        return ranking[['Cotacao', 'Div.Yield', 'ROE', 'P/L', 'P/VP', 'Mrg Ebit']]
    
    def analise_setorial(self):
        """Análise por setor"""
        if self.dados.empty:
            return pd.DataFrame()
        
        # Agrupar por setor (usando P/L como proxy para identificar setores similares)
        analise_setor = self.dados.groupby(self.dados['P/L'].round(0)).agg({
            'Div.Yield': 'mean',
            'ROE': 'mean',
            'P/L': 'mean',
            'P/VP': 'mean',
            'Cotacao': 'count'
        }).round(2)
        
        analise_setor.columns = ['DY_Medio', 'ROE_Medio', 'PL_Medio', 'PVP_Medio', 'Qtd_Empresas']
        
        return analise_setor

