#  Sistema de Recomendação de Filmes

> API REST para recomendação personalizada de filmes usando **Filtragem Colaborativa com SVD**, construída com **FastAPI** e containerizada com **Docker**.

---

##  Sobre o Projeto

Este sistema implementa um motor de recomendação de filmes baseado em **Filtragem Colaborativa** utilizando a técnica de **Decomposição em Valores Singulares (SVD — Singular Value Decomposition)**.

### Como funciona o modelo SVD?

A Filtragem Colaborativa parte do princípio de que usuários com gostos similares tendem a gostar dos mesmos filmes. O SVD decompõe a matriz de ratings usuário-item (geralmente muito esparsa) em três matrizes menores que capturam **fatores latentes** — características implícitas de usuários e filmes que não estão diretamente observáveis nos dados.

**Matematicamente:**

```
R ≈ U × Σ × Vᵀ
```

Onde:
- **R**: Matriz original de ratings (usuários × filmes)
- **U**: Fatores latentes dos usuários
- **Σ**: Valores singulares (importância de cada fator)
- **Vᵀ**: Fatores latentes dos filmes

Com esses fatores, o modelo prediz a nota que um usuário daria a qualquer filme, mesmo os que ele nunca avaliou.

### Dataset

- **MovieLens ml-latest-small** — 100.836 ratings, 9.742 filmes, 610 usuários
- Fonte: [GroupLens Research](https://grouplens.org/datasets/movielens/)
- Baixado automaticamente na primeira execução

---

##  Pré-requisitos

### Para Docker (recomendado)
- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.0

### Para execução local
- Python ≥ 3.11
- pip ≥ 23.0

---

##  Como Executar com Docker

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd Sistema-de-Recomendacao-TrabalhoFinal

# Sobe a aplicação (build + start)
docker compose up --build
```

>  **Atenção**: O primeiro startup leva alguns minutos pois baixa o dataset MovieLens (~3 MB) e treina o modelo SVD com validação cruzada 5-fold.

A API estará disponível em:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Para parar:
```bash
docker compose down
```

---

##  Como Executar Localmente

```bash
# 1. Clone e acesse o projeto
git clone <url-do-repositorio>
cd Sistema-de-Recomendacao-TrabalhoFinal

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. (Opcional) Baixe o dataset antecipadamente
python data/download_data.py

# 5. Inicie a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

##  Executando os Testes

```bash
# Ativa o ambiente virtual (se local)
source .venv/bin/activate

# Roda todos os testes com relatório detalhado
pytest tests/ -v

# Roda com cobertura de código
pytest tests/ -v --tb=short
```

---

##  Endpoints da API

### Status

| Método | Rota      | Descrição                        |
|--------|-----------|----------------------------------|
| GET    | `/`       | Verifica se a API está online    |
| GET    | `/health` | Status de saúde e do modelo      |

### Usuários

| Método | Rota              | Descrição                         |
|--------|-------------------|-----------------------------------|
| POST   | `/users/`         | Cria um novo usuário              |
| GET    | `/users/`         | Lista todos os usuários           |
| GET    | `/users/{id}`     | Busca usuário por ID              |
| DELETE | `/users/{id}`     | Remove usuário (e seus ratings)   |

### Filmes

| Método | Rota              | Descrição                         |
|--------|-------------------|-----------------------------------|
| POST   | `/items/`         | Adiciona um novo filme            |
| GET    | `/items/`         | Lista filmes (com paginação)      |
| GET    | `/items/{id}`     | Busca filme por ID                |

### Recomendações

| Método | Rota                         | Descrição                                    |
|--------|------------------------------|----------------------------------------------|
| GET    | `/recommendations/{user_id}` | Top-N recomendações para o usuário           |
| POST   | `/recommendations/rate`      | Registra avaliação de um filme               |
| GET    | `/recommendations/{user_id}/history` | Histórico de avaliações do usuário |

---

##  Exemplos de Uso

### Criar um usuário

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joao_silva"}'
```

**Resposta:**
```json
{
  "id": 1,
  "username": "joao_silva",
  "created_at": "2024-01-15T10:30:00"
}
```

### Obter recomendações

```bash
curl http://localhost:8000/recommendations/1?n=5
```

**Resposta:**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "item_id": 318,
      "title": "Shawshank Redemption, The (1994)",
      "predicted_rating": 4.82,
      "genres": "Crime|Drama"
    },
    {
      "item_id": 50,
      "title": "Usual Suspects, The (1995)",
      "predicted_rating": 4.71,
      "genres": "Crime|Mystery|Thriller"
    }
  ],
  "total": 5
}
```

### Avaliar um filme

```bash
curl -X POST http://localhost:8000/recommendations/rate \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "item_id": 1, "rating": 4.5}'
```

### Buscar filme por ID

```bash
curl http://localhost:8000/items/1
```

### Listar filmes com paginação

```bash
curl "http://localhost:8000/items/?skip=0&limit=10"
```

### Ver histórico de avaliações

```bash
curl http://localhost:8000/recommendations/1/history
```

---

##  Estrutura do Projeto

```
Sistema-de-Recomendacao-TrabalhoFinal/
├── app/
│   ├── __init__.py          # Pacote da aplicação
│   ├── main.py              # Ponto de entrada FastAPI
│   ├── models.py            # Schemas Pydantic (validação E/S)
│   ├── database.py          # SQLAlchemy ORM + SQLite
│   ├── recommender.py       # Motor SVD (scikit-surprise)
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # Endpoints de usuários
│       ├── items.py         # Endpoints de filmes
│       └── recommendations.py  # Endpoints de recomendação
├── data/
│   ├── download_data.py     # Script de download do MovieLens
│   ├── ml-latest-small/     # Dataset (gerado automaticamente)
│   ├── recommendation.db    # Banco SQLite (gerado automaticamente)
│   └── svd_model.pkl        # Modelo treinado (gerado automaticamente)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures compartilhadas (DB em memória)
│   ├── test_users.py        # Testes de usuários
│   ├── test_items.py        # Testes de itens
│   └── test_recommendations.py  # Testes de recomendações
├── Dockerfile               # Imagem Docker
├── docker-compose.yml       # Orquestração de contêineres
├── requirements.txt         # Dependências Python
└── README.md                # Esta documentação
```

---

##  Tecnologias Utilizadas

| Tecnologia         | Versão  | Função                                        |
|--------------------|---------|-----------------------------------------------|
| Python             | 3.11    | Linguagem principal                           |
| FastAPI            | 0.111   | Framework web assíncrono de alta performance  |
| Uvicorn            | 0.30    | Servidor ASGI                                 |
| scikit-surprise    | 1.1.4   | Biblioteca de sistemas de recomendação (SVD)  |
| SQLAlchemy         | 2.0     | ORM para acesso ao banco de dados             |
| SQLite             | —       | Banco de dados leve e sem servidor            |
| Pydantic           | 2.7     | Validação de dados e schemas                  |
| Pandas             | 2.2     | Manipulação de dados tabulares                |
| NumPy              | 1.26    | Computação numérica                           |
| Docker             | ≥ 24    | Containerização                               |
| pytest             | 8.2     | Framework de testes                           |
| httpx              | 0.27    | Cliente HTTP para testes                      |

---

##  Decisões de Design

### 1. SVD como algoritmo principal
O SVD foi escolhido pela sua robustez comprovada em competições de recomendação (ex: Netflix Prize) e pela disponibilidade em bibliotecas maduras como scikit-surprise. Ele lida bem com a esparsidade típica de matrizes de rating.

### 2. Singleton do RecommenderSystem
O modelo SVD é carregado/treinado uma única vez na inicialização da aplicação e mantido em memória como singleton global. Isso evita o custo de carregamento do pickle a cada requisição.

### 3. Re-treino assíncrono
Quando um usuário submete um novo rating, o re-treino do modelo é disparado como **BackgroundTask** do FastAPI. A resposta da API é retornada imediatamente sem bloquear o cliente.

### 4. Persistência em SQLite
SQLite foi escolhido pela simplicidade de deploy (zero configuração, arquivo único) e por ser suficiente para o volume de dados do MovieLens e para fins acadêmicos.

### 5. Cache do modelo em pickle
O modelo SVD treinado é persistido em `./data/svd_model.pkl`. Em startups subsequentes, o modelo é carregado do disco sem necessidade de re-treinar, reduzindo o tempo de inicialização de minutos para segundos.

### 6. Validação de dados com Pydantic v2
Todos os inputs da API são validados com schemas Pydantic, garantindo type safety e mensagens de erro claras para o cliente.
