import pandas as pd
import numpy as np
import glob
from unidecode import unidecode
import joblib
import os
import warnings
import re

warnings.filterwarnings('ignore')

print("Carregando novas faturas...")
archivos = glob.glob(r'data/raw/novas_faturas/*.csv')
lista_dfs = []

for f in archivos:
    df_temp = pd.read_csv(f)
    match = re.search(r'fatura-(\d{4})(\d{2})\d{2}\.csv', f)
    if match:
        ano = match.group(1)
        mes = match.group(2)
        df_temp['fatura'] = f"01/{mes}/{ano}"
    else:
        print(f"Aviso: Não foi possível extrair a data do arquivo {f}. Usando fallback.")
        data_primeira_linha = pd.to_datetime(df_temp['data'].iloc[0])
        df_temp['fatura'] = f"01/{str(data_primeira_linha.month).zfill(2)}/{data_primeira_linha.year}"
    lista_dfs.append(df_temp)

if not lista_dfs:
    print("Nenhum arquivo CSV encontrado em data/raw/novas_faturas/")
    exit()

df = pd.concat(lista_dfs, ignore_index=True)

# Datas e limpeza base
df['data_'] = pd.to_datetime(df['data'])
df['dia'] = df['data_'].dt.day
df['dia_semana'] = df['data_'].dt.dayofweek
df['mes'] = df['data_'].dt.month
df['ano'] = df['data_'].dt.year

df['fatura'] = pd.to_datetime(df['fatura'], format='%d/%m/%Y', errors='coerce')
df['mes_fatura'] = df['fatura'].dt.month

df.rename(columns={'lançamento': 'lancamento'}, inplace=True)
df['lancamento'] = df['lancamento'].str.replace(r'\*|-ct|\.|-|/', ' ', regex=True)
df['lancamento'] = df['lancamento'].str.replace(r'\s+', ' ', regex=True)
df['lancamento'] = df['lancamento'].str.replace(r'\d{2} \d{2}$', '', regex=True)
df['lancamento'] = df['lancamento'].astype(str).str.lower().apply(unidecode).str.strip()


# --- DESDUPLICAÇÃO INTELIGENTE COM A BASE RAW (E EXCLUSÃO FANTASMA DA ELEFANTINHO) ---
# Precisamos evitar que as faturas novas ressuscitem as transações "Elefantinho" do final de 2025.
# Para isso, carregamos a base bruta (antes dos filtros de Elefantinho) e cruzamos.
df_raw = pd.read_excel(r'data/raw/df_hist.xlsx')
meses = [col for col in df_raw.columns if re.match(r'[a-z]{3}/\d{2}$', col, re.IGNORECASE)]
df_raw_melt = df_raw.melt(id_vars=['data', 'lancamento'], value_vars=meses, value_name='valor')
df_raw_melt.dropna(subset=['valor'], inplace=True)
df_raw_melt = df_raw_melt[df_raw_melt['valor'] != 0]

# Tratamento básico no raw pra bater as strings
df_raw_melt['lancamento'] = df_raw_melt['lancamento'].str.replace(r'\*|-ct|\.|-|/', ' ', regex=True)
df_raw_melt['lancamento'] = df_raw_melt['lancamento'].str.replace(r'\s+', ' ', regex=True)
df_raw_melt['lancamento'] = df_raw_melt['lancamento'].str.replace(r'\d{2} \d{2}$', '', regex=True)
df_raw_melt['lancamento'] = df_raw_melt['lancamento'].astype(str).str.lower().apply(unidecode).str.strip()
df_raw_melt['data_'] = pd.to_datetime(df_raw_melt['data'], errors='coerce')

# Vamos criar chaves de dedup
df['chave_dedup'] = df['data_'].dt.strftime('%Y-%m-%d') + '|' + df['lancamento'] + '|' + df['valor'].astype(str)
df_raw_melt['chave_dedup'] = df_raw_melt['data_'].dt.strftime('%Y-%m-%d') + '|' + df_raw_melt['lancamento'] + '|' + df_raw_melt['valor'].astype(str)

chaves_historicas = set(df_raw_melt['chave_dedup'].unique())

# Remover faturas novas que JÁ EXISTIAM no raw history (seja Elefantinho ou não)
tamanho_antes = len(df)
df = df[~df['chave_dedup'].isin(chaves_historicas)]
tamanho_depois = len(df)
print(f"Desduplicação: {tamanho_antes - tamanho_depois} transações das novas faturas já existiam no histórico bruto e foram descartadas.")
df.drop(columns=['chave_dedup'], inplace=True)
# --------------------------------------------------------------------------------------


# Engenharia de Features
df['comida'] = df['lancamento'].str.contains('pizza|restaurante|lanch|food|burg|dog', case=False).astype(int)
df['streaming'] = df['lancamento'].str.contains('netflix|spotify|twitch' , case=False).astype(int)
df['combustivel'] = df['lancamento'].str.contains('posto|shell', case=False).astype(int)
df['cachorros'] = df['lancamento'].str.contains('pet|agro|animal|racoes|kao', case=False).astype(int)
df['veiculos'] = df['lancamento'].str.contains('pecas|moto|oficina|seguro', case=False).astype(int)

print("Carregando modelos de Machine Learning...")
try:
    arvore = joblib.load('models/random_forest.pkl')
    vectorizer = joblib.load('models/vectorizer.pkl')
    le_cat = joblib.load('models/le_cat.pkl')
except FileNotFoundError:
    print("Modelos não encontrados. Execute classificacao.py primeiro para treiná-los.")
    exit()

if len(df) > 0:
    from scipy.sparse import hstack
    X_text = vectorizer.transform(df['lancamento'])
    X_base = df[['valor', 'dia', 'dia_semana', 'mes', 'ano',
           'mes_fatura', 'comida', 'streaming', 'combustivel', 'cachorros', 'veiculos']]
    X = hstack([X_base, X_text])

    print("Predizendo categorias...")
    preds_le = arvore.predict(X)
    df['cat'] = le_cat.inverse_transform(preds_le)
else:
    print("Nenhuma transação nova a predizer (todas foram deduplicadas).")
    df['cat'] = []

df.loc[(df['valor'] < 0) & (~df['lancamento'].str.contains('pagamento efet', case=False)), 'cat'] = 'estorno'
df.loc[(df['valor'] < 0) & (df['lancamento'].str.contains('pagamento efet', case=False)), 'cat'] = 'pagamento_fatura'

seq = ['cat', 'data_', 'fatura', 'lancamento', 'valor']
df_novas = df[seq]

print(f"Inseridas {len(df_novas)} novas transações à base.")

df_novas.to_csv(r'data/processed/novas_faturas_classificadas.csv', index=False)

# Consolidar
df_hist = pd.read_csv(r'data/processed/df_hist_organizado.csv')
df_consolidado = pd.concat([df_hist, df_novas], ignore_index=True)

# Aplicar correções do Dash se existirem
if os.path.exists(r'data/processed/correcoes.csv'):
    df_correcoes = pd.read_csv(r'data/processed/correcoes.csv')
    df_correcoes['data_'] = pd.to_datetime(df_correcoes['data_'])
    df_consolidado['data_'] = pd.to_datetime(df_consolidado['data_'])
    
    df_consolidado['id'] = df_consolidado['data_'].dt.strftime('%Y-%m-%d') + '_' + df_consolidado['lancamento'] + '_' + df_consolidado['valor'].astype(str)
    df_correcoes['id'] = df_correcoes['data_'].dt.strftime('%Y-%m-%d') + '_' + df_correcoes['lancamento'] + '_' + df_correcoes['valor'].astype(str)
    
    map_correcoes = dict(zip(df_correcoes['id'], df_correcoes['cat']))
    df_consolidado['cat'] = df_consolidado.apply(lambda row: map_correcoes.get(row['id'], row['cat']), axis=1)
    df_consolidado.drop(columns=['id'], inplace=True)

df_consolidado['data_'] = pd.to_datetime(df_consolidado['data_'])
df_consolidado.sort_values(by=['data_', 'cat'], ascending=False, inplace=True)
df_consolidado.to_csv(r'data/final/df_dashboard.csv', index=False)
print("Base consolidada gerada em data/final/df_dashboard.csv")
