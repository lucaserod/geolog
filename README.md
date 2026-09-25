[readme_geolog.md](https://github.com/user-attachments/files/32659521/readme_geolog.md)
# 🚚 GeoLog — Plataforma de Telemetria Logística

## 📋 Sobre o Projeto

O **GeoLog** é uma plataforma de monitoramento logístico e análise de telemetria desenvolvida como desafio integrador acadêmico. O sistema resolve o problema de lidar com dados heterogêneos de uma frota de caminhões aplicando o conceito de **Persistência Poliglota**.

Os dados transacionais e cadastrais (motoristas e veículos) são armazenados em um banco relacional (**SQLite**), garantindo integridade referencial. Já os dados de telemetria e sensores IoT (coordenadas GPS, velocidade, temperatura) são armazenados em um banco NoSQL (**MongoDB**), permitindo alta flexibilidade e o uso de índices geoespaciais avançados.

## 🚀 Funcionalidades

* **Integração Poliglota:** Cruzamento (Join) em memória utilizando `pandas` para unificar dados do SQLite e MongoDB.
* **Geoprocessamento:** Criação automática de índices `2dsphere` e uso do operador `$geoNear` para buscar veículos próximos a um ponto de apoio num raio específico.
* **Mapa Interativo:** Renderização de um mapa dinâmico com marcadores de frota utilizando `Folium`.
* **Dashboard Analítico:** Visualização de KPIs (frotas ativas, alertas de velocidade, média de temperatura) e gráficos interativos com `Plotly`.
* **Simulador IoT (Bônus):** Geração de dados sintéticos em tempo real que simulam a movimentação contínua dos veículos e atualizam diretamente o banco NoSQL.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface Visual:** Streamlit
* **Bancos de Dados:** SQLite (via `sqlite3`) e MongoDB (via `pymongo`)
* **Processamento de Dados:** Pandas
* **Visualização:** Folium, Streamlit-Folium, Plotly Express

## ⚙️ Como Executar o Projeto (Local)

### 1. Pré-requisitos

* Python 3.9 ou superior instalado.
* Um servidor MongoDB rodando na porta padrão (`localhost:27017`). Você pode instalar o MongoDB Community Server ou rodar facilmente usando Docker:
  ```bash
  docker run -d -p 27017:27017 --name mongodb mongo
  ```

### 2. Clonar e Configurar

Clone o repositório e acesse a pasta do projeto:
```bash
git clone https://github.com/SEU_USUARIO/geolog.git
cd geolog
```

Crie um ambiente virtual e ative-o (recomendado):
```bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate
```

Instale as dependências do projeto através do arquivo `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Rodar a Aplicação

Inicie o servidor do Streamlit:
```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no seu navegador no endereço `http://localhost:8501`. Na primeira execução, o script criará os bancos de dados e fará a carga inicial (seed) dos dados de teste.

## 👥 Equipe de Desenvolvimento

Projeto desenvolvido para a disciplina de Implementação e Gerenciamento de Bancos de Dados NoSQL / Arquitetura de Software (UNIPÊ).

* **Lucas Espindola Rodrigues** - Desenvolvedor
* **Maihrendson Cauã de Carvalho Cassiano** - Desenvolvedor

*Professor: Me. Ricardo Roberto de Lima*
