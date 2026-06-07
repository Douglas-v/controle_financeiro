# Controle Financeiro Inteligente

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Dash](https://img.shields.io/badge/dash-2.14.2-blue.svg)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.2-orange.svg)

Um aplicativo web interativo para controle financeiro e categorização automática de despesas usando Machine Learning. Construído com **Dash (Plotly)** e **Scikit-Learn**.

Este repositório é uma versão open-source contendo dados sintéticos e um modelo pré-treinado básico para fins de demonstração, pronto para você expandir e conectar com os seus próprios dados financeiros reais.

## 🚀 Funcionalidades

- **Dashboard Interativo**: Visualize suas despesas, receitas e balanços através de gráficos interativos.
- **Categorização Automática**: Utilize um modelo de *Random Forest* e *NLP (TF-IDF)* para classificar as descrições (nomes dos estabelecimentos) de suas compras em categorias predefinidas automaticamente.
- **Autenticação Básica**: O dashboard possui suporte para autenticação simples usando variáveis de ambiente.

## 📁 Estrutura do Projeto

```
controle_financeiro/
├── data/                    # Dados CSV e planilhas processadas
├── models/                  # Modelos de Machine Learning treinados (.pkl)
├── scripts/                 # Scripts auxiliares (geração de mock e treino)
├── src/
│   ├── dashboard/           # Código-fonte da interface web (Dash)
│   ├── data_processing/     # Scripts de ingestão e limpeza de dados
│   └── ml/                  # Lógica de inferência e classificação
├── .env.example             # Exemplo de variáveis de ambiente
├── requirements.txt         # Dependências do projeto
└── Procfile                 # Configuração para deploy (ex: Heroku)
```

## 🛠️ Instalação e Configuração

### 1. Clonando o Repositório

```bash
https://github.com/Douglas-v/controle_financeiro.git
cd controle_financeiro
```

### 2. Criando o Ambiente Virtual (Recomendado)

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalando as Dependências

```bash
pip install -r requirements.txt
```

### 4. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```
Abra o arquivo `.env` e configure seus usuários e senhas para acessar o dashboard.

## ▶️ Como Executar

### Rodando o Servidor Local

```bash
python src/dashboard/app.py
```
Acesse `http://127.0.0.1:8050/` no seu navegador. O login será o configurado no seu arquivo `.env` (Padrão inicial: Usuário `admin`, Senha `mude_esta_senha1`).

## 🧠 Como Funciona o Machine Learning (Mock)

A aplicação vem com um dataset de 1000 registros fictícios criados para emular transações bancárias reais em estabelecimentos comuns (ex: *Uber, Netflix, Carrefour, Droga Raia*), distribuídas em categorias-chave:
- Alimentação
- Transporte
- Moradia
- Lazer
- Saúde
- Vestuário
- Educação

O modelo pre-treinado (na pasta `models/`) consegue inferir corretamente essas palavras-chave. Ao subir o seu próprio extrato no formato esperado, o modelo tentará adivinhar a categoria.

### Como gerar novos dados e treinar o modelo do zero?

Se você quiser resetar a base fictícia e retreinar o modelo, você pode executar os scripts auxiliares:

```bash
# Gerar novos dados aleatórios em data/df_dashboard.csv
python scripts/generate_dummy_data.py

# Treinar o classificador Random Forest com os novos dados
python scripts/train_dummy_model.py
```

## 🤝 Contribuindo

Sinta-se à vontade para realizar *forks*, criar *branches* para novas *features* e abrir *Pull Requests*. Toda ajuda é bem-vinda para tornar este modelo mais inteligente e a interface mais amigável.

1. Faça o Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/MinhaFeature`)
3. Faça o Commit de suas mudanças (`git commit -m 'feat: Minha nova feature'`)
4. Faça o Push para a Branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request
