import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
import joblib

# Carregar dados do dashboard final, que já contém o histórico + novas faturas + correções manuais do usuário
df = pd.read_csv(r'data/final/df_dashboard.csv')

# Preparar Target
le_cat = LabelEncoder()
df['cat_le'] = le_cat.fit_transform(df['cat'])

# Preparar Datas
df['data_'] = pd.to_datetime(df['data_'], format='mixed', errors='coerce')
df['fatura'] = pd.to_datetime(df['fatura'], format='mixed', errors='coerce')

df['dia'] = df['data_'].dt.day
df['dia_semana'] = df['data_'].dt.dayofweek
df['mes'] = df['data_'].dt.month
df['ano'] = df['data_'].dt.year
df['mes_fatura'] = df['fatura'].dt.month

# Remover categorias raras
cat_rara = df['cat_le'].value_counts()[df['cat_le'].value_counts() < 2].index
df = df[~df['cat_le'].isin(cat_rara)]

# Features Manuais
df['comida'] = df['lancamento'].str.contains('pizza|restaurante|lanch|food|burg|dog', case=False).astype(int)
df['streaming'] = df['lancamento'].str.contains('netflix|spotify|twitch' , case=False).astype(int)
df['combustivel'] = df['lancamento'].str.contains('posto|shell', case=False).astype(int)
df['cachorros'] = df['lancamento'].str.contains('pet|agro|animal|racoes|kao', case=False).astype(int)
df['veiculos'] = df['lancamento'].str.contains('pecas|moto|oficina|seguro', case=False).astype(int)

# Features de Texto
vectorizer = TfidfVectorizer(max_features=50)
X_text = vectorizer.fit_transform(df['lancamento'])

# Matriz Base
X_base = df[['valor', 'dia', 'dia_semana', 'mes', 'ano',
       'mes_fatura', 'comida', 'streaming', 'combustivel', 'cachorros', 'veiculos']]

X = hstack([X_base, X_text])
y = df['cat_le']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Treinamento
print("Treinando o modelo Random Forest...")
arvore = RandomForestClassifier(n_estimators=100, random_state=42)
arvore.fit(X_train, y_train)

# Avaliação
y_pred = arvore.predict(X_test)
print(classification_report(y_test, y_pred))

# Salvar Modelos
os.makedirs('models', exist_ok=True)
joblib.dump(arvore, 'models/random_forest.pkl')
joblib.dump(vectorizer, 'models/vectorizer.pkl')
joblib.dump(le_cat, 'models/le_cat.pkl')
print("Modelos retreinados e salvos em 'models/' com sucesso!")
