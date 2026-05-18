# dados_financeiros.py
import sys
import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
import fundamentus as fd
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
import time
import random 

class ColetorDados:
    """
    Camada de acesso a dados.
    Única responsável por se comunicar com fontes externas.
    """

    def __init__(self):
        # Sessão com retry automático e User-Agent de navegador
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Mobile Safari/537.36"
            )
        })

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        print("✅ Coletor de Dados inicializado com Sessão, Cache e Retentativas.")

    # ──────────────────────────────────────────────────────
    # DADOS FUNDAMENTALISTAS
    # ──────────────────────────────────────────────────────

    def obter_dados_fundamentalistas(self) -> pd.DataFrame:
        """Obtém dados fundamentalistas de todas as empresas da B3 via fundamentus."""
        try:
            dados = fd.get_resultado_raw()
            #Normaliza colunas percentuais para decimal
            colunas_pct = [
                 ""
            #    "Div.Yield", "Mrg Ebit", "Mrg. Líq.", "ROE", "ROIC", "Cresc. Rec.5a"
            ]
            for col in colunas_pct:
                if col in dados.columns:
                    dados[col] = pd.to_numeric(
                        dados[col].astype(str)
                        .str.replace("%", "", regex=False)
                        .str.replace(",", ".", regex=False),
                        errors="coerce"
                    ) / 100

            return dados
        except Exception as e:
            print(f"🚨 Erro ao obter dados fundamentalistas: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────
    # HISTÓRICO DE PREÇOS
    # ──────────────────────────────────────────────────────

    def obter_historico_preco(self, ticker: str, periodo: str = "1y") -> pd.DataFrame:
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker

        for tentativa in range(3):
            try:
                if tentativa > 0:
                    espera = (2 ** tentativa) + random.uniform(1, 3)
                    print(f"⏳ Tentativa {tentativa + 1}/3 — aguardando {espera:.1f}s...")
                    time.sleep(espera)

                df = yf.download(
                    ticker_sa,
                    period=periodo,
                    auto_adjust=True,
                    progress=False,
                    session=self.session,
                )

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                if not df.empty:
                    return df

                print(f"⚠️ Sem dados para {ticker_sa} na tentativa {tentativa + 1}.")

            except Exception as e:
                msg = str(e)
                if "429" in msg:
                    print(f"🚫 Rate limit (429) na tentativa {tentativa + 1}.")
                else:
                    print(f"🚨 Erro: {e}")

        print(f"❌ Falha após 3 tentativas para {ticker_sa}.")
        return pd.DataFrame()

# ──────────────────────────────────────────────────────
    # PREÇOS EM LOTE
    # ──────────────────────────────────────────────────────

    def obter_precos_em_lote(self, tickers) -> dict:
        tickers_lista = list(tickers)
        tickers_sa    = [f"{t}.SA" for t in tickers_lista]

        for tentativa in range(3):
            try:
                if tentativa > 0:
                    espera = (2 ** tentativa) + random.uniform(1, 3)
                    print(f"⏳ Lote — tentativa {tentativa + 1}/3, aguardando {espera:.1f}s...")
                    time.sleep(espera)

                data = yf.download(
                    tickers_sa,
                    period="2d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    session=self.session,
                )

                if data.empty:
                    print(f"⚠️ Download em lote vazio na tentativa {tentativa + 1}.")
                    continue

                precos = {}
                for ticker in tickers_lista:
                    ticker_sa = f"{ticker}.SA"
                    try:
                        if isinstance(data.columns, pd.MultiIndex):
                            if ticker_sa in data.columns.get_level_values(0):
                                serie = data[ticker_sa]["Close"].dropna()
                                precos[ticker] = float(serie.iloc[-1]) if not serie.empty else 0.0
                            else:
                                precos[ticker] = 0.0
                        else:
                            serie = data["Close"].dropna()
                            precos[ticker] = float(serie.iloc[-1]) if not serie.empty else 0.0
                    except Exception:
                        precos[ticker] = 0.0

                # Só retorna se pelo menos 50% dos tickers vieram com preço
                validos = sum(1 for v in precos.values() if v > 0)
                if validos >= len(tickers_lista) * 0.5:
                    if validos < len(tickers_lista):
                        sem_preco = [t for t, v in precos.items() if v == 0]
                        print(f"⚠️ Sem preço para: {', '.join(sem_preco)}")
                    return precos

                print(f"⚠️ Apenas {validos}/{len(tickers_lista)} preços obtidos. Retentando...")

            except Exception as e:
                msg = str(e)
                if "429" in msg:
                    print(f"🚫 Rate limit (429) no lote — tentativa {tentativa + 1}.")
                else:
                    print(f"🚨 Erro no lote: {e}")

        print("❌ Falha após 3 tentativas. Retornando zeros.")
        return {t: 0.0 for t in tickers_lista}
# ──────────────────────────────────────────────────────
    # MONITORAMENTO EM TEMPO REAL
    # ──────────────────────────────────────────────────────

    def monitorar_carteira_tempo_real(self, tickers: list) -> dict:
        tickers_sa = [f"{t}.SA" for t in tickers]

        for tentativa in range(3):
            try:
                if tentativa > 0:
                    espera = (2 ** tentativa) + random.uniform(1, 3)
                    print(f"⏳ Monitor — tentativa {tentativa + 1}/3, aguardando {espera:.1f}s...")
                    time.sleep(espera)

                data = yf.download(
                    tickers_sa,
                    period="2d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    session=self.session,
                )

                if data.empty:
                    continue

                resultados = {}
                for ticker in tickers:
                    ticker_sa = f"{ticker}.SA"
                    try:
                        if isinstance(data.columns, pd.MultiIndex):
                            if ticker_sa not in data.columns.get_level_values(0):
                                continue
                            hist = data[ticker_sa].dropna(subset=["Close"])
                        else:
                            hist = data.dropna(subset=["Close"])

                        if len(hist) < 2:
                            continue

                        preco_atual = float(hist["Close"].iloc[-1])
                        preco_ant   = float(hist["Close"].iloc[-2])
                        variacao    = ((preco_atual / preco_ant) - 1) * 100 if preco_ant > 0 else 0.0
                        volume      = float(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0.0

                        resultados[ticker] = {
                            "preco": preco_atual,
                            "variacao_dia": variacao,
                            "volume": volume,
                        }
                    except Exception:
                        continue

                if resultados:
                    return resultados

            except Exception as e:
                if "429" in str(e):
                    print(f"🚫 Rate limit (429) no monitor — tentativa {tentativa + 1}.")
                else:
                    print(f"🚨 Erro no monitor: {e}")

        print("❌ Monitor: falha após 3 tentativas.")
        return {}

# ──────────────────────────────────────────────────────
    # PREÇO ÚNICO (compatibilidade)
    # ──────────────────────────────────────────────────────

    def obter_preco_atual(self, ticker: str) -> dict:
        """Obtém preço atual de um único ticker. Usa obter_precos_em_lote internamente."""
        resultado = self.obter_precos_em_lote([ticker])
        preco = resultado.get(ticker, 0.0)
        return {"ticker": ticker, "preco": preco}
