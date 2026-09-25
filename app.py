import streamlit as st
import sqlite3
import pandas as pd
from pymongo import MongoClient, GEOSPHERE
import folium
from streamlit_folium import st_folium
import plotly.express as px
import random
from datetime import datetime

if 'contador_simulacao' not in st.session_state:
    st.session_state.contador_simulacao = 0
# ==========================================
# 1. CONFIGURAÇÃO INICIAL E CONEXÕES
# ==========================================

# Conexão MongoDB
client = MongoClient("mongodb://localhost:27017/")
db_mongo = client["geolog_db"]
colecao = db_mongo["telemetria"]
# Criação do índice obrigatório (Módulo 1)
colecao.create_index([("location", GEOSPHERE)])

# Conexão SQLite
conn_sqlite = sqlite3.connect('logitech.db')
cursor = conn_sqlite.cursor()

# Criação das tabelas relacionais com as colunas exatas do documento
cursor.execute("""
CREATE TABLE IF NOT EXISTS motoristas (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cnh TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS veiculos (
    id INTEGER PRIMARY KEY,
    placa TEXT,
    modelo TEXT,
    motorista_id INTEGER,
    FOREIGN KEY(motorista_id) REFERENCES motoristas(id)
)
""")

# ==========================================
# 2. CARGA INICIAL (SEED)
# ==========================================

# Verifica se o SQLite está vazio para inserir o Seed
cursor.execute("SELECT COUNT(*) FROM motoristas")
if cursor.fetchone()[0] == 0:
    motoristas_seed = [
        (1, "Carlos Andrade", "123456789", "Ativo"),
        (2, "Mariana Silva", "987654321", "Ativo"),
        (3, "Roberto Souza", "456789123", "Em Descanso")
    ]
    veiculos_seed = [
        (101, "ABC-1A23", "Volvo FH 540", 1),
        (102, "XYZ-9876", "Scania R450", 2),
        (103, "KGB-4567", "Mercedes Actros", 3)
    ]
    cursor.executemany("INSERT INTO motoristas (id, nome, cnh, status) VALUES (?, ?, ?, ?)", motoristas_seed)
    cursor.executemany("INSERT INTO veiculos (id, placa, modelo, motorista_id) VALUES (?, ?, ?, ?)", veiculos_seed)
    conn_sqlite.commit()

# Verifica se o MongoDB está vazio para inserir o Seed
if colecao.count_documents({}) == 0:
    TELEMETRIA_SEED = [
        {
            "veiculo_id": 101,
            "location": {"type": "Point", "coordinates": [-34.873, -7.115]},
            "temperatura": 4.2,
            "velocidade": 65,
            "timestamp": "2026-09-11T10:00:00Z"
        },
        {
            "veiculo_id": 102,
            "location": {"type": "Point", "coordinates": [-34.832, -7.121]},
            "temperatura": -18.5,
            "velocidade": 85,
            "timestamp": "2026-09-11T10:05:00Z"
        },
        {
            "veiculo_id": 103,
            "location": {"type": "Point", "coordinates": [-34.950, -7.150]},
            "temperatura": 22.0,
            "velocidade": 0,
            "timestamp": "2026-09-11T09:45:00Z"
        }
    ]
    colecao.insert_many(TELEMETRIA_SEED)

# ==========================================
# 3. INTERFACE STREAMLIT E LÓGICA DE NEGÓCIO
# ==========================================

st.set_page_config(page_title="Plataforma GeoLog", layout="wide")
st.title("🚛 Plataforma GeoLog - Monitoramento Logístico")

# Coordenadas do Ponto de Apoio (Centro de João Pessoa) para referência
LAT_APOIO = -7.115
LON_APOIO = -34.873

# --- DESAFIO BÔNUS: SIMULADOR ---
st.sidebar.header("Desafio Bônus")
if st.sidebar.button("🚨 Resetar Banco (Zerar tudo)"):
    colecao.drop()
    st.session_state.contador_simulacao = 0
    st.rerun() # Força a página a recarregar limpa

if st.sidebar.button("Simular Movimentação"):
    st.session_state.contador_simulacao += 1
    veiculos = [101, 102, 103]
    for v_id in veiculos:
        # Pega a última localização do veículo
        ultimo_reg = list(colecao.find({"veiculo_id": v_id}).sort("timestamp", -1).limit(1))[0]
        lon_atual = ultimo_reg["location"]["coordinates"][0]
        lat_atual = ultimo_reg["location"]["coordinates"][1]

        # Gera variação aleatória simulando movimento
        nova_lon = lon_atual + random.uniform(-0.005, 0.005)
        nova_lat = lat_atual + random.uniform(-0.005, 0.005)

        novo_ponto = {
            "veiculo_id": v_id,
            "location": {"type": "Point", "coordinates": [nova_lon, nova_lat]},
            "temperatura": ultimo_reg["temperatura"] + random.uniform(-1, 1),
            "velocidade": random.randint(40, 90) if v_id != 103 else 0,  # Veículo 103 está parado
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        colecao.insert_one(novo_ponto)
    st.sidebar.success("Novos pontos de telemetria gerados!")

tab1, tab2, tab3 = st.tabs(["🗺️ Módulo 2: Mapa", "📋 Módulo 3: Visão Unificada", "📊 Módulo 4: Dashboard"])

# --- MÓDULO 2: Geoprocessamento e Busca por Raio ---
with tab1:
    st.header("Busca por Proximidade ($near)")

    raio_km = st.slider("Raio de busca a partir do Ponto de Apoio (km)", min_value=1, max_value=20, value=5)
    raio_metros = raio_km * 1000

    # Query Geoespacial
    pipeline_geo = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [LON_APOIO, LAT_APOIO]
                },
                "distanceField": "distancia",
                "maxDistance": raio_metros,
                "spherical": True
            }
        },
        {"$sort": {"timestamp": -1}},  # Ordena do mais novo pro mais velho
        {"$group": {
            "_id": "$veiculo_id",
            "veiculo_id": {"$first": "$veiculo_id"},
            "velocidade": {"$first": "$velocidade"},
            "location": {"$first": "$location"}
        }}
    ]

    veiculos_no_raio = list(colecao.aggregate(pipeline_geo))

    # Renderização do Mapa com Folium
    m = folium.Map(location=[LAT_APOIO, LON_APOIO], zoom_start=12)

    # Marca o Ponto de Apoio e o círculo do raio
    folium.Marker([LAT_APOIO, LON_APOIO], popup="Ponto de Apoio", icon=folium.Icon(color='red')).add_to(m)
    folium.Circle([LAT_APOIO, LON_APOIO], radius=raio_metros, color='blue', fill=True, fill_opacity=0.2).add_to(m)

    # Adiciona os veículos encontrados no mapa
    for v in veiculos_no_raio:
        coords = v["location"]["coordinates"]
        folium.Marker(
            [coords[1], coords[0]],
            popup=f"Veículo ID: {v['veiculo_id']} | Vel: {v['velocidade']}km/h",
            icon=folium.Icon(color='green', icon='truck', prefix='fa')
        ).add_to(m)

    st_folium(m, width=800, height=400, key=f"mapa_{st.session_state.contador_simulacao}")
    st.write(f"Veículos encontrados em um raio de {raio_km}km: **{len(veiculos_no_raio)}**")

# --- MÓDULO 3: Visão Unificada (Join Poliglota) ---
with tab2:
    st.header("Visão Unificada de Frota")

    query_sqlite = """
    SELECT v.id as veiculo_id, v.placa, m.nome as motorista, m.status
    FROM veiculos v
    JOIN motoristas m ON v.motorista_id = m.id
    """
    df_sqlite = pd.read_sql_query(query_sqlite, conn_sqlite)

    # Buscar apenas o log MAIS RECENTE de cada veículo no MongoDB
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$veiculo_id",
            "temperatura": {"$first": "$temperatura"},
            "velocidade": {"$first": "$velocidade"},
            "location": {"$first": "$location"}
        }}
    ]
    telemetria_data = list(colecao.aggregate(pipeline))

    # Prepara o df do MongoDB (renomeia _id para veiculo_id para o Join)
    for t in telemetria_data:
        t["veiculo_id"] = t.pop("_id")
        t["coordenadas"] = str(t["location"]["coordinates"])

    df_mongo = pd.DataFrame(telemetria_data)

    if not df_mongo.empty:
        df_unificado = pd.merge(df_sqlite, df_mongo, on="veiculo_id", how="inner")
        df_final = df_unificado[['motorista', 'placa', 'status', 'temperatura', 'velocidade', 'coordenadas']]
        df_final.columns = ['Nome do Motorista', 'Placa', 'Status', 'Última Temp. (°C)', 'Velocidade (km/h)',
                            'Coordenadas']
        st.dataframe(df_final, use_container_width=True)
    else:
        st.warning("Nenhum dado de telemetria encontrado.")

# --- MÓDULO 4: Dashboard Analítico ---
with tab3:
    st.header("Métricas e Indicadores")

    if not df_mongo.empty:
        col1, col2, col3 = st.columns(3)

        # KPI 1: Frotas Ativas (Status no SQLite)
        frotas_ativas = len(df_sqlite[df_sqlite['status'] == 'Ativo'])
        col1.metric("Frotas Ativas", frotas_ativas)

        # KPI 2: Média de Temperatura da Carga
        media_temp = df_unificado['temperatura'].mean()
        col2.metric("Média de Temp. da Carga", f"{media_temp:.1f} °C")

        # KPI 3: Alertas de Velocidade (> 80 km/h)
        alertas = len(df_unificado[df_unificado['velocidade'] > 80])
        col3.metric("Alertas de Velocidade", alertas)

        st.divider()

        col_graf1, col_graf2 = st.columns(2)

        # Gráfico 1: Variação de temperatura (Pegando todos os registros do MongoDB)
        todos_logs = pd.DataFrame(list(colecao.find({}, {"_id": 0})))
        # Faz um join rápido para pegar as placas ao invés dos IDs
        todos_logs = pd.merge(todos_logs, df_sqlite[['veiculo_id', 'placa']], on='veiculo_id', how='left')

        with col_graf1:
            fig_temp = px.line(todos_logs, x="timestamp", y="temperatura", color="placa",
                               title="Histórico de Temperatura por Veículo")
            st.plotly_chart(fig_temp, use_container_width=True)

        # Gráfico 2: Distribuição do status dos motoristas (Dados do SQLite)
        with col_graf2:
            fig_status = px.pie(df_sqlite, names="status", title="Distribuição do Status dos Motoristas")
            st.plotly_chart(fig_status, use_container_width=True)

    else:
        st.info("Aguardando dados para gerar o dashboard.")