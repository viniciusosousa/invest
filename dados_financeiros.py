import yfinance as yf
import pandas as pd
import fundamentus as fd
import requests_cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime

class ColetorDados:
    """
    Classe robusta para coletar dados, com cache, sessão e retentativas.
    """
    def __init__(self):
        # Configura uma sessão que se comporta como um navegador e armazena respostas em cache
        self.session = requests_cache.CachedSession(
            'yfinance_cache',
            backend='sqlite',
            expire_after=300 # Cache de 5 minutos
        )
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # Configura uma estratégia de retentativas para ser mais resiliente
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        print("✅ Coletor de Dados inicializado com Sessão, Cache e Retentativas.")

    def obter_dados_fundamentalistas(self):
        """Obtém dados fundamentalistas de todas as empresas da B3."""
        try:
            # A biblioteca fundamentus não usa a nossa sessão, então a chamamos diretamente
            dados = fd.get_resultado()
            if dados is None or dados.empty:
                print("⚠️ Fundamentus não retornou dados.")
                return pd.DataFrame()

            for col in ['Div.Yield', 'Mrg Ebit', 'Mrg. Líq.', 'ROE', 'ROIC', 'Cresc. Rec.5a']:
                if col in dados.columns:
                    dados[col] = pd.to_numeric(
                        dados[col].astype(str).str.replace('%', '').str.replace(',', '.'),
                        errors='coerce'
                    ) / 100
            return dados
        except Exception as e:
            print(f"🚨 Erro crítico ao obter dados fundamentalistas: {e}")
            return pd.DataFrame()

    def obter_historico_preco_alternativo(self, ticker, periodo="1y"):
        """Obtém o histórico de preços usando yfinance com nossa sessão robusta."""
        try:
            # Passa nossa sessão configurada para o yfinance usar
            df = yf.download(f"{ticker}.SA", period=periodo, auto_adjust=True, progress=False, session=self.session)
            if df.empty:
                print(f"⚠️ Aviso: Nenhum dado histórico encontrado para {ticker}.SA. Pode ser um ticker inválido ou delistado.")
            return df
        except Exception as e:
            print(f"🚨 Erro crítico ao obter histórico de {ticker}: {e}")
            return pd.DataFrame()

    def obter_preco_atual(self, ticker):
        """Obtém o preço atual, variação e volume."""
        try:
            hist = yf.download(f"{ticker}.SA", period="2d", auto_adjust=True, progress=False, session=self.session)
            if not hist.empty and len(hist) > 1:
                ultimo_dia = hist.iloc[-1]
                dia_anterior = hist.iloc[-2]
                
                preco_atual = ultimo_dia['Close']
                variacao_dia = ((preco_atual / dia_anterior['Close']) - 1) * 100 if dia_anterior['Close'] > 0 else 0
                volume = ultimo_dia['Volume']

                return {'preco': preco_atual, 'variacao_dia': variacao_dia, 'volume': volume}
            else:
                print(f"⚠️ Aviso: Dados insuficientes para calcular o preço atual de {ticker}.SA")
                return {'preco': 0, 'variacao_dia': 0, 'volume': 0}
        except Exception as e:
            print(f"🚨 Erro crítico ao obter preço de {ticker}: {e}")
            return {'preco': 0, 'variacao_dia': 0, 'volume': 0}

    def monitorar_carteira_tempo_real(self, tickers):
        """Monitora uma lista de tickers em tempo real."""
        # Usa download em lote para ser muito mais eficiente
        tickers_sa = [f"{t}.SA" for t in tickers]
        try:
            data = yf.download(tickers_sa, period="2d", auto_adjust=True, progress=False, session=self.session)
            if data.empty:
                return {}

            resultados = {}
            for ticker in tickers:
                ticker_sa = f"{ticker}.SA"
                # Acessa os dados do ticker específico (pode ter múltiplos níveis de coluna)
                hist = data.loc[:, (slice(None), ticker_sa)]
                if not hist.empty and len(hist) > 1:
                    preco = hist['Close'].iloc[-1]
                    variacao = ((preco / hist['Close'].iloc[-2]) - 1) * 100 if hist['Close'].iloc[-2] > 0 else 0
                    volume = hist['Volume'].iloc[-1]
                    resultados[ticker] = {'preco': preco, 'variacao_dia': variacao, 'volume': volume}
            return resultados
        except Exception as e:
            print(f"🚨 Erro crítico ao monitorar carteira: {e}")
            return {}

