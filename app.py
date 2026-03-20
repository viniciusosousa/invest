from flask import Flask, render_template_string, request
import plotly.graph_objs as go
import plotly.utils
import json
from datetime import datetime

# Importa as classes dos outros módulos que você criou
from dados_financeiros import ColetorDados
from analise_fundamentalista import AnaliseFundamentalista
from analise_tecnica import AnaliseTecnica
from gestao_carteira import GestaoCarteira

# Inicializa a aplicação Flask
app = Flask(__name__)

# --- INICIALIZAÇÃO GLOBAL ---
print("🔄 Carregando dados iniciais. Aguarde...")
coletor = ColetorDados()

# Tenta carregar os dados fundamentalistas
dados_fund = coletor.obter_dados_fundamentalistas()
if dados_fund is not None and not dados_fund.empty:
    analise_fund = AnaliseFundamentalista(dados_fund)
    print("✅ Dados fundamentalistas carregados com sucesso.")
else:
    # Se falhar, o app continua rodando, mas as funções que dependem dele serão desabilitadas
    analise_fund = None 
    dados_fund = pd.DataFrame() # Garante que é um DataFrame vazio para não dar erro
    print("⚠️ Falha ao carregar dados fundamentalistas. Funções de análise fundamentalista estarão indisponíveis.")

# Simula a carteira do usuário com base nos dados fornecidos
carteira_usuario = GestaoCarteira()
carteira_data = {
    'COGN3': {'qtd': 470, 'preco_compra': 27.90}, 'EGIE3': {'qtd': 200, 'preco_compra': 40.30},
    'BBAS3': {'qtd': 300, 'preco_compra': 22.90}, 'VALE3': {'qtd': 100, 'preco_compra': 50.10},
    'HBOR3': {'qtd': 1500, 'preco_compra': 2.96}, 'IRBR3': {'qtd': 1213, 'preco_compra': 3.17},
    'SIMH3': {'qtd': 600, 'preco_compra': 4.50}, 'AGRO3': {'qtd': 100, 'preco_compra': 20.00},
    'VAMO3': {'qtd': 400, 'preco_compra': 4.65}, 'GFSA3': {'qtd': 600, 'preco_compra': 2.50},
    'EZTC3': {'qtd': 300, 'preco_compra': 4.60}, 'VIVT3': {'qtd': 800, 'preco_compra': 1.50},
    'AMOB3': {'qtd': 450, 'preco_compra': 1.43}
}
for ticker, dados in carteira_data.items():
    carteira_usuario.adicionar_ativo(ticker, dados['qtd'], dados['preco_compra'])

# --- TEMPLATES HTML ---
# Manter os templates aqui facilita a edição
HTML_HEADER = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: #f0f2f5; color: #1c1e21; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 15px; }
        h1, h2, h3 { color: #1877f2; }
        a { color: #1877f2; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .card { background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f5f7fa; font-weight: 600; }
        .positive { color: #42b72a; font-weight: bold; }
        .negative { color: #fa3e3e; font-weight: bold; }
        .button { background-color: #1877f2; color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        .button:hover { background-color: #166fe5; }
        input[type="text"] { padding: 10px; border: 1px solid #ddd; border-radius: 6px; width: calc(100% - 22px); }
        .footer { text-align: center; margin-top: 30px; color: #606770; font-size: 14px; }
        .nav-back { display: inline-block; margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
'''

HTML_FOOTER = '''
        <div class="footer">
            <p>Dashboard de Investimentos B3 © {{ year }}</p>
        </div>
    </div>
</body>
</html>
'''

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def dashboard():
    """Página principal do dashboard."""
    # Obter dados para o resumo da carteira
    precos_atuais = {t: coletor.obter_preco_atual(t)['preco'] for t in carteira_data.keys()}
    performance = carteira_usuario.calcular_performance(precos_atuais)
    total_investido = performance.get('TOTAL', {}).get('valor_investido', 0)
    valor_atual = performance.get('TOTAL', {}).get('valor_atual', 0)
    dy_carteira = carteira_usuario.calcular_dividend_yield_carteira(dados_fund)

    template = HTML_HEADER + '''
        <h1>🚀 Dashboard de Investimentos B3</h1>
        
        <div class="grid">
            <div class="card">
                <h3>🎯 Resumo da Carteira</h3>
                <p><strong>Valor Investido:</strong> R$ {{ "%.2f"|format(total_investido) }}</p>
                <p><strong>Valor Atual:</strong> R$ {{ "%.2f"|format(valor_atual) }}</p>
                <p><strong>Resultado:</strong> <span class="{{ 'positive' if valor_atual >= total_investido else 'negative' }}">R$ {{ "%.2f"|format(valor_atual - total_investido) }}</span></p>
                <p><strong>Dividend Yield Médio:</strong> {{ "%.2f"|format(dy_carteira) }}%</p>
            </div>

            <div class="card">
                <h3>🔍 Análises</h3>
                <p><a href="/fundamentalista">🏆 Ranking Dividend Yield</a></p>
                <p><a href="/bazin">🎯 Filtro Método Bazin</a></p>
                <p><a href="/monitoramento">⏰ Monitoramento em Tempo Real</a></p>
                <p><a href="/carteira">💼 Detalhes da Minha Carteira</a></p>
            </div>
        </div>

        <div class="card">
            <h3>📈 Análise Técnica Rápida</h3>
            <form action="/tecnica" method="post">
                <input type="text" name="ticker" placeholder="Ex: PETR4, VALE3, BBAS3..." required>
                <br><br>
                <button type="submit" class="button">Analisar Ativo</button>
            </form>
        </div>
    ''' + HTML_FOOTER

    return render_template_string(template, title="Dashboard Principal", year=datetime.now().year,
                                  total_investido=total_investido, valor_atual=valor_atual, dy_carteira=dy_carteira)

@app.route('/fundamentalista')
def ranking_dy():
    """Exibe o ranking de Dividend Yield."""
    if analise_fund:
        ranking_df = analise_fund.ranking_dividend_yield(20)
        html_table = ranking_df.to_html(classes='table', float_format='{:.2f}'.format, border=0)
    else:
        html_table = "<p>Erro: Dados fundamentalistas não disponíveis.</p>"

    template = HTML_HEADER + '<h1>🏆 Top 20 Dividend Yield</h1>' + html_table + '<a href="/" class="nav-back">← Voltar</a>' + HTML_FOOTER
    return render_template_string(template, title="Ranking DY", year=datetime.now().year)

@app.route('/bazin')
def filtro_bazin():
    """Exibe empresas que passam no filtro do Método Décio Bazin."""
    if analise_fund:
        bazin_df = analise_fund.filtrar_metodo_bazin()
        html_table = bazin_df[['Cotacao', 'Div.Yield', 'ROE', 'Mrg Ebit', 'Div.Br/Patrim']].to_html(classes='table', float_format='{:.2f}'.format, border=0)
    else:
        html_table = "<p>Erro: Dados fundamentalistas não disponíveis.</p>"

    template = HTML_HEADER + '<h1>🎯 Empresas pelo Método Bazin</h1>' + html_table + '<a href="/" class="nav-back">← Voltar</a>' + HTML_FOOTER
    return render_template_string(template, title="Filtro Bazin", year=datetime.now().year)

@app.route('/tecnica', methods=['POST'])
def analise_tecnica():
    """Exibe a análise técnica para um ticker específico."""
    ticker = request.form.get('ticker', '').upper()
    dados_hist = coletor.obter_historico_preco_alternativo(ticker, "1y") # Usando o método alternativo

    if dados_hist.empty:
        return render_template_string(HTML_HEADER + f"<h1>Erro</h1><p>Não foi possível obter dados para o ticker {ticker}. Verifique o código e tente novamente.</p><a href='/' class='nav-back'>← Voltar</a>" + HTML_FOOTER, title="Erro", year=datetime.now().year)

    analise_tec = AnaliseTecnica(dados_hist)
    dados_com_indicadores = analise_tec.calcular_indicadores()
    sinais = analise_tec.identificar_sinais()
    suporte, resistencia = analise_tec.calcular_suporte_resistencia()

    # Criação do gráfico interativo com Plotly
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=dados_com_indicadores.index, open=dados_com_indicadores['Open'], high=dados_com_indicadores['High'], low=dados_com_indicadores['Low'], close=dados_com_indicadores['Close'], name='Preço'))
    fig.add_trace(go.Scatter(x=dados_com_indicadores.index, y=dados_com_indicadores['SMA_20'], name='SMA 20', line=dict(color='blue', width=1)))
    fig.add_trace(go.Scatter(x=dados_com_indicadores.index, y=dados_com_indicadores['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)))
    
    if suporte and resistencia:
        fig.add_hline(y=resistencia, line_dash="dash", line_color="red", annotation_text="Resistência", annotation_position="bottom right")
        fig.add_hline(y=suporte, line_dash="dash", line_color="green", annotation_text="Suporte", annotation_position="bottom right")

    fig.update_layout(title=f'Análise Técnica - {ticker}', yaxis_title='Preço (R$)', height=500, xaxis_rangeslider_visible=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    sinais_html = "<br>".join(sinais) if sinais else "Nenhum sinal claro identificado."

    template = HTML_HEADER + f'''
        <h1>📈 Análise Técnica - {ticker}</h1>
        <div id="grafico" style="width:100%;height:500px;"></div>
        <div class="card">
            <h3>🎯 Sinais Identificados Recentemente:</h3>
            <p>{sinais_html}</p>
            <h3>📊 Níveis Chave:</h3>
            <p><strong>Suporte:</strong> R$ {"%.2f"|format(suporte) if suporte else 'N/A'}</p>
            <p><strong>Resistência:</strong> R$ {"%.2f"|format(resistencia) if resistencia else 'N/A'}</p>
        </div>
        <a href="/" class="nav-back">← Voltar</a>
        <script>
            var graphs = {graphJSON};
            Plotly.plot('grafico', graphs, {{}});
        </script>
    ''' + HTML_FOOTER
    return render_template_string(template, title=f"Análise de {ticker}", year=datetime.now().year, suporte=suporte, resistencia=resistencia)

@app.route('/monitoramento')
def monitoramento():
    """Página de monitoramento em tempo real da carteira."""
    tickers_carteira = list(carteira_data.keys())
    dados_tempo_real = coletor.monitorar_carteira_tempo_real(tickers_carteira)
    
    html_rows = ""
    for ticker, dados in dados_tempo_real.items():
        cor = "positive" if dados['variacao_dia'] >= 0 else "negative"
        html_rows += f"<tr><td>{ticker}</td><td>R$ {dados['preco']:.2f}</td><td class='{cor}'>{dados['variacao_dia']:.2f}%</td><td>{dados['volume']:,.0f}</td></tr>"
    
    template = HTML_HEADER + '''
        <h1>⏰ Monitoramento em Tempo Real</h1>
        <p><em>Esta página atualiza automaticamente a cada 30 segundos.</em></p>
        <table>
            <tr><th>Ticker</th><th>Preço Atual</th><th>Variação Dia</th><th>Volume</th></tr>
            {{ html_rows|safe }}
        </table>
        <a href="/" class="nav-back">← Voltar</a>
    ''' + HTML_FOOTER
    # Adicionando o meta refresh no template
    template = template.replace("<head>", "<head><meta http-equiv='refresh' content='30'>")
    return render_template_string(template, title="Monitoramento", year=datetime.now().year, html_rows=html_rows)

@app.route('/carteira')
def minha_carteira():
    """Exibe os detalhes e performance da carteira do usuário."""
    precos_atuais = {t: coletor.obter_preco_atual(t)['preco'] for t in carteira_data.keys()}
    performance = carteira_usuario.calcular_performance(precos_atuais)

    html_rows = ""
    for ticker, dados in performance.items():
        if ticker == 'TOTAL': continue
        cor_lucro = 'positive' if dados['lucro_prejuizo'] >= 0 else 'negative'
        html_rows += f"""
        <tr>
            <td>{ticker}</td>
            <td>{dados['quantidade']}</td>
            <td>R$ {dados['preco_compra']:.2f}</td>
            <td>R$ {dados['preco_atual']:.2f}</td>
            <td>R$ {dados['valor_investido']:.2f}</td>
            <td>R$ {dados['valor_atual']:.2f}</td>
            <td class="{cor_lucro}">R$ {dados['lucro_prejuizo']:.2f} ({dados['rentabilidade']:.2f}%)</td>
        </tr>
        """
    
    total = performance.get('TOTAL', {})
    cor_total = 'positive' if total.get('lucro_prejuizo', 0) >= 0 else 'negative'
    html_total = f"""
        <tr style="font-weight: bold; background-color: #f5f7fa;">
            <td colspan="4">TOTAL</td>
            <td>R$ {total.get('valor_investido', 0):.2f}</td>
            <td>R$ {total.get('valor_atual', 0):.2f}</td>
            <td class="{cor_total}">R$ {total.get('lucro_prejuizo', 0):.2f} ({total.get('rentabilidade', 0):.2f}%)</td>
        </tr>
    """

    template = HTML_HEADER + '''
        <h1>💼 Performance da Minha Carteira</h1>
        <table>
            <tr><th>Ticker</th><th>Qtd.</th><th>Preço Médio</th><th>Preço Atual</th><th>Valor Investido</th><th>Valor Atual</th><th>Resultado (L/P)</th></tr>
            {{ html_rows|safe }}
            {{ html_total|safe }}
        </table>
        <a href="/" class="nav-back">← Voltar</a>
    ''' + HTML_FOOTER
    return render_template_string(template, title="Minha Carteira", year=datetime.now().year, html_rows=html_rows, html_total=html_total)

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard de Investimentos...")
    print("📱 Acesse pelo navegador: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False) # Debug mode False para produção/uso estável
