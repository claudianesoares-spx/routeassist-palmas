import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from urllib.parse import quote_plus

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(
    page_title="RouteAssist | Apoio Operacional",
    page_icon="🧭",
    layout="centered"
)

# ================= CONFIG LOCAL =================
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "status_site": "FECHADO",
    "senha_master": "MASTER2026",
    "historico": []
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

config = load_config()

def registrar_acao(usuario, acao):
    config["historico"].append({
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario,
        "acao": acao
    })
    save_config(config)

# ================= URLs =================
URL_ROTAS = "https://docs.google.com/spreadsheets/d/1UomeywJI8KNGNIin7KKRrkPzBWtlhlp2G-4RCCtJwXY/export?format=csv&gid=1803149397"
URL_DRIVERS = "https://docs.google.com/spreadsheets/d/1UomeywJI8KNGNIin7KKRrkPzBWtlhlp2G-4RCCtJwXY/export?format=csv&gid=709174551"

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSde2R2AHQkQ4D4U_Pg1Q6OdDQinb3fgsj8JMxXFEKDvTVynUQ/viewform"

# ================= FUNÇÕES =================
def limpar_id(valor):
    if pd.isna(valor):
        return ""
    valor = str(valor).strip()
    return "" if valor.lower() in ["nan", "-", "none"] else valor

@st.cache_data(ttl=120)
def carregar_rotas(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df["ID"] = df["ID"].apply(limpar_id)
    df["Data Exp."] = pd.to_datetime(df["Data Exp."], errors="coerce").dt.date
    return df

@st.cache_data(ttl=300)
def carregar_motoristas(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df["ID"] = df["ID"].apply(limpar_id)
    return df

# ================= SESSION STATE =================
if "id_motorista" not in st.session_state:
    st.session_state.id_motorista = ""
if "consultado" not in st.session_state:
    st.session_state.consultado = False

# ================= INTERFACE =================
st.title("🧭 RouteAssist")
st.markdown("Ferramenta de apoio operacional para alocação e redistribuição de rotas.")
st.divider()

# ================= ADMIN =================
nivel = None
with st.sidebar:
    with st.expander("🔒 Área Administrativa"):
        senha = st.text_input("Senha", type="password")

        if senha == config["senha_master"]:
            nivel = "MASTER"
            st.success("Acesso MASTER liberado")
        elif senha == "MANAUS2026":
            nivel = "ADMIN"
            st.success("Acesso ADMIN liberado")
        elif senha:
            st.error("Senha incorreta")

        if nivel in ["ADMIN", "MASTER"]:
            col1, col2 = st.columns(2)
            if col1.button("🔓 ABRIR"):
                config["status_site"] = "ABERTO"
                registrar_acao(nivel, "ABRIU CONSULTA")
            if col2.button("🔒 FECHAR"):
                config["status_site"] = "FECHADO"
                registrar_acao(nivel, "FECHOU CONSULTA")
            if st.button("🔄 Atualizar dados agora"):
                st.cache_data.clear()
                st.success("Dados atualizados")

st.markdown(f"### 📌 Status atual: **{config['status_site']}**")
st.divider()

if config["status_site"] == "FECHADO":
    st.warning("🚫 Consulta indisponível no momento.")
    st.stop()

# ================= CONSULTA =================
st.markdown("### 🔍 Consulta de Rotas")
id_input = st.text_input("Digite seu ID de motorista")

if st.button("🔍 Consultar"):
    if not id_input.strip():
        st.warning("Informe seu ID.")
        st.stop()
    st.session_state.id_motorista = id_input.strip()
    st.session_state.consultado = True

# ================= RESULTADOS =================
if st.session_state.consultado:
    id_motorista = st.session_state.id_motorista

    df_rotas = carregar_rotas(URL_ROTAS)
    df_drivers = carregar_motoristas(URL_DRIVERS)

    if id_motorista not in set(df_drivers["ID"]):
        st.error("ID não encontrado.")
        st.stop()

    registrar_acao(id_motorista, "CONSULTOU ROTAS")

    # ===== ROTAS DISPONÍVEIS =====
    rotas_disp = df_rotas[
        df_rotas["Status"].str.contains("No Show", case=False, na=False)
    ]

    if rotas_disp.empty:
        st.info("📭 Nenhuma rota disponível no momento.")
    else:
        st.markdown("### 📦 Rotas disponíveis")

        for cluster, df_cluster in rotas_disp.groupby("Cluster"):
            with st.expander(f"📍 {cluster}"):
                for _, row in df_cluster.iterrows():
                    data_fmt = row["Data Exp."].strftime("%d/%m/%Y") if pd.notna(row["Data Exp."]) else "-"

                    form_url = (
                        f"{GOOGLE_FORM_URL}?usp=pp_url"
                        f"&entry.392776957={quote_plus(id_motorista)}"
                        f"&entry.1682939517={quote_plus(str(row['Gaiola']))}"
                        f"&entry.1100254277={quote_plus(str(row['Tipo Veiculo']))}"
                        f"&entry.1284288730={quote_plus(str(row['Nome']))}"
                        f"&entry.933833967={quote_plus(str(row['Cluster']))}"
                        f"&entry.1534916252=Tenho+Interesse"
                    )

                    st.markdown(f"""
                    <div style="border:1px solid #eee; padding:12px; border-radius:8px; margin-bottom:10px;">
                        <strong>ROTA:</strong> {row['Gaiola']}<br>
                        <strong>TIPO:</strong> {row['Tipo Veiculo']}<br>
                        <strong>NOME:</strong> {row['Nome']}<br>
                        <strong>CLUSTER:</strong> {row['Cluster']}<br>
                        <strong>DATA:</strong> {data_fmt}<br><br>
                        <a href="{form_url}" target="_blank">💚 Tenho interesse</a>
                    </div>
                    """, unsafe_allow_html=True)

# ================= RODAPÉ =================
st.markdown("""
<hr>
<div style="text-align:center; font-size:0.85em; color:#888;">
<strong>RouteAssist</strong><br>
Concept & Development — Claudiane Vieira<br>
Since Dec/2025
</div>
""", unsafe_allow_html=True)
