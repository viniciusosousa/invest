import pandas as pd
import numpy as np
from datetime import datetime

class GestaoCarteira:
    """
    Classe para gerenciar uma carteira de investimentos, incluindo operações,
    cálculo de performance e geração de análises.
    """
    def __init__(self):
        """Inicializa a carteira e o histórico de operações."""
        self.carteira = pd.DataFrame(columns=['ticker', 'quantidade', 'preco_compra', 'data_compra', 'valor_investido'])
        self.historico_operacoes = []

    def adicionar_ativo(self, ticker, quantidade, preco_compra, data_compra=None):
        """
        Adiciona ou atualiza um ativo na carteira.
        Se o ativo já existe, calcula o preço médio.
        """
        if data_compra is None:
            data_compra = datetime.now().strftime('%Y-%m-%d')

        # Registrar a operação no histórico
        self.historico_operacoes.append({
            'data': data_compra, 'ticker': ticker, 'operacao': 'COMPRA',
            'quantidade': quantidade, 'preco': preco_compra
        })

        # Verifica se o ativo já está na carteira
        if ticker in self.carteira['ticker'].values:
            # Atualiza a posição existente com preço médio
            pos_atual = self.carteira[self.carteira['ticker'] == ticker].iloc[0]
            
            novo_valor_total = pos_atual['valor_investido'] + (quantidade * preco_compra)
            nova_quantidade_total = pos_atual['quantidade'] + quantidade
            novo_preco_medio = novo_valor_total / nova_quantidade_total
            
            self.carteira.loc[self.carteira['ticker'] == ticker, 'quantidade'] = nova_quantidade_total
            self.carteira.loc[self.carteira['ticker'] == ticker, 'preco_compra'] = novo_preco_medio
            self.carteira.loc[self.carteira['ticker'] == ticker, 'valor_investido'] = novo_valor_total
        else:
            # Adiciona uma nova posição
            nova_posicao = {
                'ticker': ticker, 'quantidade': quantidade, 'preco_compra': preco_compra,
                'data_compra': data_compra, 'valor_investido': quantidade * preco_compra
            }
            self.carteira = pd.concat([self.carteira, pd.DataFrame([nova_posicao])], ignore_index=True)

    def calcular_performance(self, precos_atuais):
        """
        Calcula a performance detalhada de cada ativo e da carteira total.

        Args:
            precos_atuais (dict): Um dicionário com {ticker: preco_atual}.

        Returns:
            dict: Um dicionário com a performance de cada ativo e um item 'TOTAL'.
        """
        if self.carteira.empty:
            return {}

        resultado = {}
        valor_total_investido = 0
        valor_total_atual = 0

        for _, posicao in self.carteira.iterrows():
            ticker = posicao['ticker']
            preco_atual = precos_atuais.get(ticker, 0) # Usa 0 se o preço não for encontrado
            
            # Pula ativos sem preço atual para evitar distorções
            if preco_atual == 0:
                continue

            valor_investido = posicao['valor_investido']
            quantidade = posicao['quantidade']
            valor_atual = quantidade * preco_atual
            lucro_prejuizo = valor_atual - valor_investido
            
            # Evita divisão por zero se o valor investido for 0
            rentabilidade = (lucro_prejuizo / valor_investido) * 100 if valor_investido > 0 else 0

            resultado[ticker] = {
                'quantidade': quantidade, 'preco_compra': posicao['preco_compra'],
                'preco_atual': preco_atual, 'valor_investido': valor_investido,
                'valor_atual': valor_atual, 'lucro_prejuizo': lucro_prejuizo,
                'rentabilidade': rentabilidade
            }
            
            valor_total_investido += valor_investido
            valor_total_atual += valor_atual

        # Performance geral da carteira
        if valor_total_investido > 0:
            rentabilidade_total = ((valor_total_atual - valor_total_investido) / valor_total_investido) * 100
            resultado['TOTAL'] = {
                'valor_investido': valor_total_investido,
                'valor_atual': valor_total_atual,
                'lucro_prejuizo': valor_total_atual - valor_total_investido,
                'rentabilidade': rentabilidade_total
            }

        return resultado

    def calcular_dividend_yield_carteira(self, dados_fundamentalistas):
        """
        Calcula o dividend yield médio ponderado da carteira.

        Args:
            dados_fundamentalistas (pd.DataFrame): DataFrame do `fundamentus`.

        Returns:
            float: O dividend yield médio da carteira.
        """
        if self.carteira.empty or dados_fundamentalistas is None or dados_fundamentalistas.empty:
            return 0.0

        dy_ponderado = 0
        valor_total = self.carteira['valor_investido'].sum()

        if valor_total == 0:
            return 0.0

        # Merge para alinhar dados da carteira com os fundamentalistas
        carteira_com_dy = pd.merge(self.carteira, dados_fundamentalistas[['Div.Yield']], left_on='ticker', right_index=True, how='left')
        carteira_com_dy['Div.Yield'] = carteira_com_dy['Div.Yield'].fillna(0)
        
        # Cálculo ponderado
        dy_ponderado = (carteira_com_dy['valor_investido'] * carteira_com_dy['Div.Yield']).sum() / valor_total
        
        return dy_ponderado

    def sugerir_rebalanceamento(self, precos_atuais, peso_maximo_por_ativo=0.20):
        """
        Analisa a concentração da carteira e sugere vendas para rebalanceamento.

        Args:
            precos_atuais (dict): Dicionário com {ticker: preco_atual}.
            peso_maximo_por_ativo (float): O peso máximo que um ativo pode ter na carteira.

        Returns:
            list: Uma lista de dicionários com sugestões de venda.
        """
        performance = self.calcular_performance(precos_atuais)
        
        if 'TOTAL' not in performance or performance['TOTAL']['valor_atual'] == 0:
            return []

        valor_total_carteira = performance['TOTAL']['valor_atual']
        sugestoes = []

        for ticker, dados in performance.items():
            if ticker == 'TOTAL':
                continue
            
            peso_atual = dados['valor_atual'] / valor_total_carteira
            if peso_atual > peso_maximo_por_ativo and dados['preco_atual'] > 0:
                valor_excesso = dados['valor_atual'] - (valor_total_carteira * peso_maximo_por_ativo)
                quantidade_sugerida_venda = int(valor_excesso / dados['preco_atual'])
                
                if quantidade_sugerida_venda > 0:
                    sugestoes.append({
                        'ticker': ticker, 'acao': 'VENDER', 'quantidade': quantidade_sugerida_venda,
                        'motivo': f"Reduzir concentração (peso atual: {peso_atual:.1%})"
                    })
        return sugestoes
    
    def gerar_resumo_analitico(self, precos_atuais):
        """
        Gera um resumo analítico da carteira, incluindo melhores e piores performances.
        
        Args:
            precos_atuais (dict): Dicionário com {ticker: preco_atual}.

        Returns:
            dict: Um dicionário com as principais métricas e destaques da carteira.
        """
        performance = self.calcular_performance(precos_atuais)
        if 'TOTAL' not in performance:
            return {"erro": "Não foi possível calcular a performance."}

        # Converte para DataFrame para facilitar a análise
        df_performance = pd.DataFrame.from_dict(performance, orient='index').drop('TOTAL', errors='ignore')
        
        if df_performance.empty:
            return {"erro": "Carteira vazia ou sem dados de preço."}

        resumo = {
            "valor_total_investido": performance['TOTAL']['valor_investido'],
            "valor_total_atual": performance['TOTAL']['valor_atual'],
            "lucro_prejuizo_total": performance['TOTAL']['lucro_prejuizo'],
            "rentabilidade_total": performance['TOTAL']['rentabilidade'],
            "melhor_performer_rentabilidade": df_performance.loc[df_performance['rentabilidade'].idxmax()].name,
            "pior_performer_rentabilidade": df_performance.loc[df_performance['rentabilidade'].idxmin()].name,
            "melhor_performer_lucro": df_performance.loc[df_performance['lucro_prejuizo'].idxmax()].name,
            "pior_performer_lucro": df_performance.loc[df_performance['lucro_prejuizo'].idxmin()].name,
            "total_ativos": len(df_performance)
        }
        return resumo
