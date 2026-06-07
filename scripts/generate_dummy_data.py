import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_dummy_data(output_path="data/df_dashboard.csv", num_rows=1000):
    # Categorias teis
    categories = {
        "Alimentação": ["Carrefour", "Pao de Acucar", "McDonalds", "Burger King", "Ifood", "Z Delivery", "Padaria Central"],
        "Transporte": ["Uber", "99App", "Posto Ipiranga", "Shell Select", "Sem Parar", "Metrô SP"],
        "Moradia": ["Enel", "Sabesp", "Vivo Internet", "Condomínio", "Leroy Merlin"],
        "Lazer": ["Netflix", "Spotify", "Cinemark", "Steam", "Amazon Prime"],
        "Saúde": ["Droga Raia", "Farmacia Pague Menos", "Dr Consulta", "Academia SmartFit"],
        "Vestuário": ["C&A", "Renner", "Zara", "Shopee", "Mercado Livre"],
        "Educação": ["Alura", "Udemy", "Livraria Cultura", "Papelaria"]
    }

    data = []
    
    # Gerar datas para os ltimos 6 meses
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    for _ in range(num_rows):
        # Escolher uma categoria aleatria
        cat = random.choice(list(categories.keys()))
        
        # Escolher um estabelecimento dessa categoria
        lancamento = random.choice(categories[cat])
        
        # Gerar uma data aleatria
        random_days = random.randint(0, 180)
        data_ = (start_date + timedelta(days=random_days)).date()
        
        # O ms de fatura ser o ms da data
        fatura_date = data_.replace(day=1)
        fatura = fatura_date.strftime("%Y-%m-%d 00:00:00")
        
        # Gerar um valor aleatrio baseado na categoria
        if cat == "Moradia":
            valor = round(random.uniform(50.0, 500.0), 2)
        elif cat == "Transporte":
            valor = round(random.uniform(10.0, 200.0), 2)
        elif cat == "Alimentação":
            valor = round(random.uniform(20.0, 300.0), 2)
        elif cat == "Lazer":
            valor = round(random.uniform(15.0, 60.0), 2)
        else:
            valor = round(random.uniform(10.0, 150.0), 2)
            
        data.append([cat, data_.strftime("%Y-%m-%d"), fatura, lancamento, valor])
        
    df = pd.DataFrame(data, columns=["cat", "data_", "fatura", "lancamento", "valor"])
    
    # Ordenar por data
    df = df.sort_values(by="data_", ascending=False)
    
    # Garantir que a pasta data/ existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"[{output_path}] gerado com {num_rows} registros fictícios.")

if __name__ == "__main__":
    # Caminho ajustado para rodar a partir do dir raiz ou da pasta scripts
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base_path, "data", "df_dashboard.csv")
    generate_dummy_data(output_path=target_csv)
