import pandas as pd
import pandas_ta as ta
import numpy as np

class AnaliseTecnica:
    def __init__(self, dados_historicos):
        self.dados = dados_historicos
    
    def calcular_indicadores(self):
        """Calcula principais indicadores técnicos"""
        if self.dados.empty:
            return self.dados
        
        df = self.dados.copy()
        
        # Médias móveis
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['EMA_12'] = ta.ema(df['Close'], length=12)
        df['EMA_26'] = ta.ema(df['Close'], length=26)
        
        # RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd_data = ta.macd(df['Close'])
        df['MACD'] = macd_data['MACD_12_26_9']
        df['MACD_Signal'] = macd_data['MACDs_12_26_9']
        df['MACD_Histogram'] = macd_data['MACDh_12_26_9']
        
        # Bandas de Bollinger
        bb_data = ta.bbands(df['Close'], length=20)
        df['BB_Upper'] = bb_data['BBU_20_2.0']
        df['BB_Middle'] = bb_data['BBM_20_2.0']
        df['BB_Lower'] = bb_data['BBL_20_2.0']
        
        # Stochastic
        stoch_data = ta.stoch(df['High'], df['Low'], df['Close'])
        df['Stoch_K'] = stoch_data['STOCHk_14_3_3']
        df['Stoch_D'] = stoch_data['STOCHd_14_3_3']
        
        return df
    
    def identificar_sinais(self):
        """Identifica sinais de compra e venda"""
        df = self.calcular_indicadores()
        sinais = []
        
        if len(df) < 2:
            return sinais
        
        ultimo = df.iloc[-1]
        penultimo = df.iloc[-2]
        
        # Sinal de cruzamento de médias móveis
        if (ultimo['SMA_20'] > ultimo['SMA_50'] and 
            penultimo['SMA_20'] <= penultimo['SMA_50']):
            sinais.append("COMPRA: Cruzamento SMA 20 > SMA 50")
        
        # Sinal RSI
        if ultimo['RSI'] < 30:
            sinais.append("COMPRA: RSI oversold (<30)")
        elif ultimo['RSI'] > 70:
            sinais.append("VENDA: RSI overbought (>70)")
        
        # Sinal MACD
        if (ultimo['MACD'] > ultimo['MACD_Signal'] and 
            penultimo['MACD'] <= penultimo['MACD_Signal']):
            sinais.append("COMPRA: MACD cruzou acima da linha de sinal")
        
        # Sinal Bandas de Bollinger
        if ultimo['Close'] < ultimo['BB_Lower']:
            sinais.append("COMPRA: Preço abaixo da Banda de Bollinger inferior")
        elif ultimo['Close'] > ultimo['BB_Upper']:
            sinais.append("VENDA: Preço acima da Banda de Bollinger superior")
        
        return sinais
    
    def calcular_suporte_resistencia(self, janela=20):
        """Identifica níveis de suporte e resistência"""
        if len(self.dados) < janela * 2:
            return None, None
        
        # Usar máximas e mínimas locais
        highs = self.dados['High'].rolling(window=janela).max()
        lows = self.dados['Low'].rolling(window=janela).min()
        
        # Resistência: média das máximas recentes
        resistencia = highs.tail(10).mean()
        
        # Suporte: média das mínimas recentes
        suporte = lows.tail(10).mean()
        
        return suporte, resistencia

