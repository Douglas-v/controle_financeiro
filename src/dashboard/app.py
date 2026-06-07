# -*- coding: utf-8 -*-
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import subprocess
import sys
import os
import dash_auth
import base64
from dotenv import load_dotenv

# Função para carregar a base atualizada
def load_data():
    df = pd.read_csv(r'data/final/df_dashboard.csv')
    df['fatura'] = pd.to_datetime(df['fatura'], format='mixed', errors='coerce')
    df['data_'] = pd.to_datetime(df['data_'], format='mixed', errors='coerce')
    return df

def get_status_meses():
    caminho = r'data/processed/status_meses.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho).set_index('mes')['status'].to_dict()
    return {}

def save_status_mes(mes, status):
    caminho = r'data/processed/status_meses.csv'
    if os.path.exists(caminho):
        df_status = pd.read_csv(caminho)
    else:
        df_status = pd.DataFrame(columns=['mes', 'status'])
        
    if mes in df_status['mes'].values:
        df_status.loc[df_status['mes'] == mes, 'status'] = status
    else:
        df_status = pd.concat([df_status, pd.DataFrame([{'mes': mes, 'status': status}])], ignore_index=True)
    df_status.to_csv(caminho, index=False)

df = load_data()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Carregar as senhas do arquivo .env que não vai pro GitHub
load_dotenv()

# Autenticação Segura para Nuvem (PythonAnywhere)
user1 = os.getenv('DASH_USER1', 'usuario1')
pwd1 = os.getenv('DASH_PWD1', 'mude_esta_senha1')
user2 = os.getenv('DASH_USER2', 'usuario2')
pwd2 = os.getenv('DASH_PWD2', 'mude_esta_senha2')

VALID_USERNAME_PASSWORD_PAIRS = {
    user1: pwd1,
    user2: pwd2
}
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

server = app.server
app.title = "Finance Dashboard"

CARD_STYLE = {
    "box-shadow": "0 4px 6px 0 rgba(0, 0, 0, 0.18)",
    "border-radius": "15px",
    "background-color": "rgba(43, 43, 43, 0.6)",
    "backdrop-filter": "blur(10px)",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "padding": "20px",
    "margin-bottom": "20px"
}

def get_layout():
    global df
    df = load_data()
    meses_dt = sorted(df['fatura'].dropna().unique())
    meses_fatura = [pd.to_datetime(m).strftime('%m/%Y') for m in meses_dt]
    categorias = sorted(df['cat'].dropna().unique())
    
    # Injetando as opções fixas para garantir que apareçam
    dropdown_options = [{'label': c, 'value': c} for c in categorias if c not in ['terceiros', 'ignorar']]
    # Adicionando as de exclusão com destaque visual
    dropdown_options.append({'label': '⚠️ TERCEIROS (EXCLUIR)', 'value': 'terceiros'})
    dropdown_options.append({'label': '❌ IGNORAR (EXCLUIR)', 'value': 'ignorar'})
    
    return dbc.Container([
        dcc.Location(id='url-refresh', refresh=True),
        dbc.Row([
            dbc.Col(html.H1("Monitoramento Financeiro", className="text-start mt-4 mb-2", style={"font-weight": "bold", "color": "#00E676", "font-size": "1.8rem"}), xs=12, md=9),
            dbc.Col(dbc.Button("👁️ Ocultar Valores", id="btn-privacidade", n_clicks=0, outline=True, color="secondary", className="mt-4 mb-2", style={"width": "100%"}), xs=12, md=3)
        ]),
        
        dbc.Row([
            dbc.Col(
                dcc.Upload(
                    id='upload-data',
                    children=dbc.Button("📥 Importar Nova Fatura", color="info", style={'width': '100%', 'font-weight': 'bold', 'border-radius': '10px'}),
                    multiple=False,
                    className="mb-2 mb-md-4",
                    style={'width': '100%'}
                ), 
                xs=12, md=5
            ),
            dbc.Col(dbc.Button("💾 Salvar tabela e Retreinar IA", id="btn-retreinar", color="success", className="mb-4", style={'width': '100%', 'font-weight': 'bold', 'border-radius': '10px'}), xs=12, md=5)
        ], justify="center"),
        
        dbc.Row([
            dbc.Col(html.Div(id="retreinar-output", className="text-center text-warning fw-bold mb-3"), width=12)
        ]),

        dbc.Row([
            dbc.Col([
                html.Label("Mês da Fatura", style={"color": "#b3b3b3"}),
                dcc.Dropdown(
                    id='mes-dropdown',
                    options=[{'label': m, 'value': m} for m in meses_fatura],
                    value=meses_fatura[-1] if len(meses_fatura) > 0 else None,
                    clearable=False,
                    style={'color': '#000000'}
                )
            ], xs=12, md=4, className="mb-3"),
            dbc.Col([
                html.Label("Status da Conferência", style={"color": "#b3b3b3", "display": "block"}),
                dbc.Button(id="btn-conferido", n_clicks=0, style={'width': '100%', 'font-weight': 'bold'})
            ], xs=12, md=4, className="mb-3"),
            dbc.Col([
                html.Label("Categoria", style={"color": "#b3b3b3"}),
                dcc.Dropdown(
                    id='cat-dropdown',
                    options=[{'label': 'Todas', 'value': 'Todas'}] + [{'label': c.title(), 'value': c} for c in categorias],
                    value='Todas',
                    clearable=False,
                    style={'color': '#000000'}
                )
            ], xs=12, md=4, className="mb-3")
        ], className="mb-4", justify="center"),

        dbc.Row([
            dbc.Col(dbc.Card([
                html.H4("Total da Fatura", className="card-title", style={"color": "#b3b3b3", "font-size": "1rem"}),
                html.H2(id="kpi-total", style={"color": "#00E676", "font-weight": "bold", "font-size": "1.5rem"})
            ], style=CARD_STYLE), xs=12, md=4, className="mb-3"),
            dbc.Col(dbc.Card([
                html.H4("Maior Despesa", className="card-title", style={"color": "#b3b3b3", "font-size": "1rem"}),
                html.H2(id="kpi-maior", style={"color": "#FF5252", "font-weight": "bold", "font-size": "1.5rem"})
            ], style=CARD_STYLE), xs=12, md=4, className="mb-3"),
            dbc.Col(dbc.Card([
                html.H4("Transações (Qtd)", className="card-title", style={"color": "#b3b3b3", "font-size": "1rem"}),
                html.H2(id="kpi-count", style={"color": "#29B6F6", "font-weight": "bold", "font-size": "1.5rem"})
            ], style=CARD_STYLE), xs=12, md=4, className="mb-3"),
        ], justify="center"),

        dbc.Row([
            dbc.Col(dbc.Card([dcc.Graph(id='bar-chart', config={'displayModeBar': False})], style=CARD_STYLE), xs=12, md=7, className="mb-3"),
            dbc.Col(dbc.Card([dcc.Graph(id='pie-chart', config={'displayModeBar': False})], style=CARD_STYLE), xs=12, md=5, className="mb-3"),
        ]),
        
        dbc.Row([
            dbc.Col(dbc.Card([dcc.Graph(id='line-chart', config={'displayModeBar': False})], style=CARD_STYLE), xs=12),
        ]),

        dbc.Row([
            dbc.Col(dbc.Card([
                html.H4("Detalhamento (Edite a Categoria no menu suspenso)", style={"color": "#b3b3b3", "margin-bottom": "20px"}),
                
                # Adicionar Nova Categoria
                dbc.Row([
                    dbc.Col(dbc.Input(id="nova-cat-input", placeholder="Nome da nova categoria...", type="text", className="mb-2"), xs=12, md=6),
                    dbc.Col(dbc.Button("➕ Criar Nova Categoria", id="btn-nova-cat", color="info", className="w-100"), xs=12, md=6),
                ], className="mb-3"),

                html.Div([
                    dash_table.DataTable(
                        id='data-table',
                        editable=True, # Permite edição
                        columns=[
                            {'id': 'data_', 'name': 'Data', 'editable': False},
                            {'id': 'lancamento', 'name': 'Lançamento', 'editable': False},
                            {'id': 'cat', 'name': 'Categoria (Toque p/ Editar)', 'presentation': 'dropdown', 'editable': True},
                            {'id': 'valor', 'name': 'Valor', 'editable': False}
                        ],
                        dropdown={
                            'cat': {
                                'options': dropdown_options,
                                'clearable': False
                            }
                        },
                        css=[
                            {"selector": ".Select-menu-outer", "rule": "display: block !important; z-index: 9999 !important;"},
                        ],
                        style_table={'overflowX': 'auto', 'border-radius': '10px', 'minWidth': '100%'},
                    style_header={
                        'backgroundColor': 'rgba(0, 230, 118, 0.2)',
                        'color': '#00E676',
                        'fontWeight': 'bold',
                        'border': 'none'
                    },
                    style_cell={
                        'backgroundColor': 'rgba(43, 43, 43, 0.4)',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px',
                        'textAlign': 'left'
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{cat} eq "terceiros"'},
                            'backgroundColor': 'rgba(60, 60, 60, 0.5)',
                            'color': '#FF5252',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'filter_query': '{cat} eq "ignorar"'},
                            'backgroundColor': 'rgba(60, 60, 60, 0.5)',
                            'color': '#FF5252',
                            'fontWeight': 'bold'
                        }
                    ],
                    page_size=20,
                    sort_action='native'
                )
            ], style={'overflow': 'visible', 'width': '100%', 'padding-bottom': '100px'})
        ], style=CARD_STYLE), xs=12)
        ])
    ], fluid=True, style={"background-color": "#121212", "min-height": "100vh", "padding": "20px"})

app.layout = get_layout

@app.callback(
    [Output('btn-conferido', 'children'),
     Output('btn-conferido', 'color')],
    [Input('btn-conferido', 'n_clicks'),
     Input('mes-dropdown', 'value')]
)
def toggle_status_mes(n_clicks, mes_selecionado):
    if not mes_selecionado:
        return "N/A", "secondary"
        
    ctx = dash.callback_context
    status_dict = get_status_meses()
    current_status = status_dict.get(mes_selecionado, 'pendente')
    
    # Se o botão foi clicado
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'btn-conferido.n_clicks':
        new_status = 'conferido' if current_status == 'pendente' else 'pendente'
        save_status_mes(mes_selecionado, new_status)
        current_status = new_status
        
    if current_status == 'conferido':
        return "✅ MÊS CONFERIDO", "success"
    else:
        return "⚠️ PENDENTE DE CONFERÊNCIA", "warning"

@app.callback(
    [Output('kpi-total', 'children'),
     Output('kpi-maior', 'children'),
     Output('kpi-count', 'children'),
     Output('bar-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('line-chart', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'dropdown'),
     Output('nova-cat-input', 'value'),
     Output('btn-privacidade', 'children')],
    [Input('mes-dropdown', 'value'),
     Input('cat-dropdown', 'value'),
     Input('btn-nova-cat', 'n_clicks'),
     Input('btn-privacidade', 'n_clicks')],
    [State('nova-cat-input', 'value'),
     State('data-table', 'dropdown')]
)
def update_dashboard(mes_selecionado, cat_selecionada, n_clicks, btn_privacidade_clicks, nova_cat, current_dropdown):
    global df
    if df.empty or mes_selecionado is None:
        return "", "", "", {}, {}, {}, [], {}, "", "👁️ Ocultar Valores"
        
    categorias = sorted(df['cat'].dropna().unique())
    
    # Initialize dropdown options se não tiver
    if not current_dropdown:
        options = [{'label': c, 'value': c} for c in categorias if c not in ['terceiros', 'ignorar']]
        options.append({'label': '⚠️ TERCEIROS (EXCLUIR)', 'value': 'terceiros'})
        options.append({'label': '❌ IGNORAR (EXCLUIR)', 'value': 'ignorar'})
        current_dropdown = {
            'cat': {
                'options': options,
                'clearable': False
            }
        }
        
    # Adicionar nova categoria ao dropdown se solicitado
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'btn-nova-cat.n_clicks':
        if nova_cat and nova_cat.strip() != "":
            cat_limpa = nova_cat.strip().lower()
            existing_options = [opt['value'] for opt in current_dropdown['cat']['options']]
            if cat_limpa not in existing_options:
                current_dropdown['cat']['options'].append({'label': cat_limpa, 'value': cat_limpa})
                
    # Limpa o campo de input
    input_val_return = ""

    dff = df[df['fatura'].dt.strftime('%m/%Y') == mes_selecionado]
    
    if cat_selecionada != 'Todas':
        dff = dff[dff['cat'] == cat_selecionada]
        
    # EXCLUINDO 'terceiros' E 'ignorar' DOS CÁLCULOS!
    despesas_reais = dff[(dff['valor'] > 0) & (~dff['cat'].isin(['terceiros', 'ignorar']))]
    
    total = despesas_reais['valor'].sum() if not despesas_reais.empty else 0
    maior = despesas_reais['valor'].max() if not despesas_reais.empty else 0
    count = len(despesas_reais)
    
    modo_privado = (btn_privacidade_clicks % 2 != 0)
    
    if modo_privado:
        kpi_total = "R$ ••••••"
        kpi_maior = "R$ ••••••"
        btn_priv_text = "🙈 Mostrar Valores"
    else:
        kpi_total = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        kpi_maior = f"R$ {maior:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        btn_priv_text = "👁️ Ocultar Valores"
        
    kpi_count = f"{count}"

    template = "plotly_dark"
    color_discrete_sequence = px.colors.qualitative.Pastel

    # Formatar os valores para os rótulos
    gastos_cat = despesas_reais.groupby('cat')['valor'].sum().reset_index().sort_values('valor', ascending=False)
    gastos_cat['valor_fmt'] = gastos_cat['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Bar Chart Vertical
    max_val = gastos_cat['valor'].max() * 1.2 if not gastos_cat.empty else 100
    fig_bar = px.bar(gastos_cat, x='cat', y='valor', text='valor_fmt', title="Gastos Reais por Categoria",
                     template=template, color='cat', color_discrete_sequence=color_discrete_sequence)
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50, r=20, l=20, b=20))
    fig_bar.update_xaxes(showgrid=False, title=None)
    fig_bar.update_yaxes(showgrid=False, showticklabels=False, title=None, range=[0, max_val])
    
    if modo_privado:
        fig_bar.update_traces(text=None, hoverinfo='none', hovertemplate=None)

    # Horizontal Bar Chart (Substituindo o Pie Chart)
    gastos_cat_h = gastos_cat.sort_values('valor', ascending=False)
    fig_pie = px.bar(gastos_cat_h, x='valor', y='cat', text='valor_fmt', orientation='h', title="Distribuição de Gastos",
                     template=template, color='cat', color_discrete_sequence=color_discrete_sequence)
    fig_pie.update_traces(textposition='outside')
    fig_pie.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=50, r=80, l=20, b=20))
    fig_pie.update_yaxes(categoryorder='total ascending', showgrid=False, title=None)
    fig_pie.update_xaxes(showgrid=False, showticklabels=False, title=None, range=[0, max_val])
    
    if modo_privado:
        fig_pie.update_traces(text=None, hoverinfo='none', hovertemplate=None)

    # Line Chart 
    df_trend = df[(df['valor'] > 0) & (~df['cat'].isin(['terceiros', 'ignorar']))]
    if cat_selecionada != 'Todas':
        df_trend = df_trend[df_trend['cat'] == cat_selecionada]
    
    trend = df_trend.groupby(df_trend['fatura'].dt.strftime('%Y-%m'))['valor'].sum().reset_index()
    fig_line = px.line(trend, x='fatura', y='valor', markers=True, title="Histórico de Despesas (Sem Terceiros)",
                       template=template, color_discrete_sequence=['#00E676'])
    fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                           xaxis_title="Mês", yaxis_title="Total Gasto (R$)")
    fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
    if modo_privado:
        fig_line.update_yaxes(showticklabels=False)
        fig_line.update_traces(hoverinfo='none', hovertemplate=None)

    # Tabela (Inclui tudo para poder ser editado, incluindo os terceiros)
    table_data = dff[['data_', 'lancamento', 'cat', 'valor']].copy()
    # Formatação solicitada
    table_data['data_'] = table_data['data_'].dt.strftime('%d/%m/%Y')
    table_data['valor'] = table_data['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    return kpi_total, kpi_maior, kpi_count, fig_bar, fig_pie, fig_line, table_data.to_dict('records'), current_dropdown, input_val_return, btn_priv_text

@app.callback(
    Output("retreinar-output", "children"),
    Input("btn-retreinar", "n_clicks"),
    State("data-table", "data"),
    prevent_initial_call=True
)
def save_and_retrain(n_clicks, current_table_data):
    global df
    if not current_table_data:
        return "Nenhum dado na tabela."
    
    # 1. Encontrar o que foi alterado na UI vs DataFrame original
    df_ui = pd.DataFrame(current_table_data)
    
    # Cruzar para ver onde a categoria mudou
    mudancas = []
    for _, row in df_ui.iterrows():
        # Limpar o valor formatado de volta para float
        try:
            val_str = str(row['valor']).replace('R$ ', '').replace('.', '').replace(',', '.')
            val_float = float(val_str)
        except ValueError:
            continue
            
        # Achar no df original
        orig_row = df[(df['data_'].dt.strftime('%d/%m/%Y') == row['data_']) & 
                      (df['lancamento'] == row['lancamento']) & 
                      (abs(df['valor'] - val_float) < 0.01)]
        if not orig_row.empty:
            orig_cat = orig_row.iloc[0]['cat']
            if orig_cat != row['cat']:
                mudancas.append({
                    'data_': orig_row.iloc[0]['data_'].strftime('%Y-%m-%d'), # salva no formato nativo pro csv
                    'lancamento': row['lancamento'],
                    'valor': orig_row.iloc[0]['valor'], # salva o float nativo pro csv
                    'cat': row['cat']
                })
    
    if not mudancas:
        return "Nenhuma categoria foi alterada para retreinar."
        
    # 2. Salvar as mudanças em data/processed/correcoes.csv
    caminho_correcoes = r'data/processed/correcoes.csv'
    df_mudancas = pd.DataFrame(mudancas)
    
    if os.path.exists(caminho_correcoes):
        df_antigo = pd.read_csv(caminho_correcoes)
        df_novo = pd.concat([df_antigo, df_mudancas])
        df_novo.drop_duplicates(subset=['data_', 'lancamento', 'valor'], keep='last', inplace=True)
        df_novo.to_csv(caminho_correcoes, index=False)
    else:
        df_mudancas.to_csv(caminho_correcoes, index=False)
        
    # 3. Executar o pipeline de ingestão e treino
    try:
        # Detecta o comando correto dependendo do servidor (Windows vs PythonAnywhere Linux)
        python_cmd = 'python' if os.name == 'nt' else 'python3.10'
        
        # Roda Ingestao (para consolidar a correção)
        subprocess.run([python_cmd, r'src/data_processing/ingestao_itau.py'], check=True)
        # Roda o Treinamento no df_dashboard final
        subprocess.run([python_cmd, r'src/ml/classificacao.py'], check=True)
        
        # Recarregar dataframe em memória no Dash
        df = load_data()
        return "Sucesso! Categorias retreinadas e aplicadas à base."
    except Exception as e:
        return f"❌ Erro ao retreinar: {e}"

@app.callback(
    Output('url-refresh', 'href'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_upload(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        caminho_salvar = os.path.join('data', 'raw', 'novas_faturas', filename)
        os.makedirs(os.path.dirname(caminho_salvar), exist_ok=True)
        
        with open(caminho_salvar, 'wb') as f:
            f.write(decoded)
            
        python_cmd = 'python' if os.name == 'nt' else 'python3.10'
        subprocess.run([python_cmd, r'src/data_processing/ingestao_itau.py'], check=True)
        
        global df
        df = load_data()
        
        return '/'
    return dash.no_update

if __name__ == '__main__':
    app.run(debug=True, port=8050)
