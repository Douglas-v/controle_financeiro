import pandas as pd
import numpy as np
import re
from unidecode import unidecode
import os

# 1. Carregar os Dados Históricos
df = pd.read_excel(r'data/raw/df_hist.xlsx')
print(f"Base carregada. Linhas: {len(df)}")

meses = [col for col in df.columns if re.match(r'[a-z]{3}/\d{2}$', col, re.IGNORECASE)]

df_melt = df.melt(id_vars=['nat', 'cat', 'origem', 'data', 'lancamento',],
                  value_vars=meses,
                  var_name='mes',
                  value_name='valor')

# Filtrando valores válidos (e removendo Elefantinho do histórico via origem e categorias fantasmas)
df_melt = df_melt[((df_melt['valor'].notnull()) & (df_melt['valor'] != 0) & (df_melt['origem'] != 'Elefantinho'))]

# Excluindo categorias da Elefantinho definitivamente
categorias_proibidas = ['insumos elefantinho', 'embalagens e publicidade impressa']
df_melt = df_melt[~df_melt['cat'].astype(str).str.lower().apply(unidecode).str.strip().isin(categorias_proibidas)]

df_melt[['mes_br','ano']] = df_melt['mes'].str.split('/', expand=True)

meses_en = {
    'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
    'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
}

df_melt['mes_br'] = df_melt['mes_br'].str.lower().replace(meses_en)
df_melt['dia'] = df_melt['data'].dt.day.astype(str).str.zfill(2)

df_melt['data_'] = pd.to_datetime(df_melt['dia'] + '/' +df_melt['mes_br'] + '/' + df_melt['ano'], format='%d/%b/%y', errors='coerce')
df_melt.loc[df_melt['data_'].isnull(), 'dia'] = '28'
df_melt['data_'] = pd.to_datetime(df_melt['dia'] + '/' +df_melt['mes_br'] + '/' + df_melt['ano'], format='%d/%b/%y', errors='coerce')

mes_corrente = (df_melt['data_'].dt.day <= 16)
mes_seguinte = ((df_melt['data_'].dt.day > 16) & (df_melt['data_'].dt.month < 12))
mes_final = ((df_melt['data_'].dt.day > 16) & (df_melt['data_'].dt.month == 12))
df_melt['fatura'] = 'ERRO DE DATA'

df_melt.loc[mes_corrente, 'fatura'] = ('01' + '/' + (df_melt['data_'].dt.month.astype(str).str.zfill(2)) + '/' + df_melt['data_'].dt.year.astype(str))
df_melt.loc[mes_seguinte, 'fatura'] = ('01' + '/' + ((df_melt['data_'].dt.month + 1).astype(str).str.zfill(2)) + '/' + df_melt['data_'].dt.year.astype(str))
df_melt.loc[mes_final, 'fatura'] = ('01/01' + '/' + (df_melt['data_'].dt.year + 1).astype(str))

df_melt['fatura'] = pd.to_datetime(df_melt['fatura'], format='%d/%m/%Y', errors='coerce')

seq = ['cat', 'data_', 'fatura', 'lancamento', 'valor']
df_melt = df_melt[seq]

df_melt.loc[df_melt['valor'] < 0, 'cat'] = 'estorno'

df_melt['lancamento'] = df_melt['lancamento'].str.replace(r'\*|-ct|\.|-|/', ' ', regex=True)
df_melt['lancamento'] = df_melt['lancamento'].str.replace(r'\s+', ' ', regex=True)
df_melt['lancamento'] = df_melt['lancamento'].str.replace(r'\d{2} \d{2}$', '', regex=True)

df_melt.sort_values(by=['data_', 'cat'], ascending=False, inplace=True)
df_melt.reset_index(drop=True, inplace=True)

df_melt['cat'] = df_melt['cat'].astype(str).str.lower().apply(unidecode).str.strip()
df_melt['lancamento'] = df_melt['lancamento'].astype(str).str.lower().apply(unidecode).str.strip()

# 5. Salvar
os.makedirs(r'data/processed', exist_ok=True)
df_melt.to_csv(r'data/processed/df_hist_organizado.csv', index=False)
print("Base histórica reorganizada e salva em: data/processed/df_hist_organizado.csv")