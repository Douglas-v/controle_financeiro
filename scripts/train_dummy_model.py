import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

def train_dummy_model(data_path="data/df_dashboard.csv", models_dir="models"):
    print("Iniciando treinamento do modelo com dados fictícios...")
    
    # Carregar dados
    df = pd.read_csv(data_path)
    
    if df.empty:
        print("Dataset vazio. Abortando treinamento.")
        return
        
    # Preparar X e y
    X_text = df["lancamento"].fillna("").astype(str)
    y_labels = df["cat"].astype(str)
    
    # 1. Label Encoder para as categorias
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_labels)
    
    # 2. Vectorizer para os textos de lançamento
    vectorizer = TfidfVectorizer(max_features=1000)
    X_vectorized = vectorizer.fit_transform(X_text)
    
    # 3. Treinar classificador (Random Forest Simples)
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_vectorized, y_encoded)
    
    # Garantir que a pasta models existe
    os.makedirs(models_dir, exist_ok=True)
    
    # Salvar modelos
    joblib.dump(le, os.path.join(models_dir, "le_cat.pkl"))
    joblib.dump(vectorizer, os.path.join(models_dir, "vectorizer.pkl"))
    joblib.dump(clf, os.path.join(models_dir, "random_forest.pkl"))
    
    print("Modelos salvos com sucesso em:")
    print(f"- {os.path.join(models_dir, 'le_cat.pkl')}")
    print(f"- {os.path.join(models_dir, 'vectorizer.pkl')}")
    print(f"- {os.path.join(models_dir, 'random_forest.pkl')}")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base_path, "data", "df_dashboard.csv")
    target_models = os.path.join(base_path, "models")
    
    train_dummy_model(data_path=target_csv, models_dir=target_models)
