import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

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
URL_ROTAS = "https://docs.google.com/spreadsheets/d/1F8HC2D8UxRc5R_QBdd-zWu7y6Twqyk3r0NTPN0HCWUI/export?format=csv&gid=1803149397"
URL_DRIVERS = "https://docs.google.com/spreadsheets/d/1F8HC2D8UxRc5R_QBdd-zWu7y6Twqyk3r0NTPN0HCWUI/export?format=csv&gid=36116218"

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSffKb0EPcHCRXv-XiHhgk-w2bTGbt179fJkr879jNdp-AbTxg/viewform"

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
if "interesses" not in st.session_state:
    st.session_state.interesses = set()

if "id_motorista" not in st.session_state:
    st.session_state.id_motorista = ""

if "consultado" not in st.session_state:
    st.session_state.consultado = False

# ================= CSS COMPACTO =================
st.markdown("""
<style>
.card {
    background-color: #ffffff;
    padding: 10px 12px;          /* padding reduzido */
    border-radius: 8px;          /* borda menos arredondada */
    box-shadow: 0 2px 6px rgba(0,0,0,0.07); /* sombra mais leve */
    border-left: 4px solid #ff7a00;
    margin-bottom: 12px;
    font-size: 14px;             /* fonte menor */
    line-height: 1.3;            /* menos espaçamento entre linhas */
}

.card p {
    margin: 4px 0;               /* reduz o espaçamento entre parágrafos */
}

.card .flex-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

@media only screen and (max-width: 480px) {
    .card {
        padding: 8px 10px;
        font-size: 13px;
    }
}
</style>
""", unsafe_allow_html=True)

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
        elif senha == "LPA2026":
            nivel = "ADMIN"
            st.success("Acesso ADMIN liberado")
        elif senha:
            st.error("Senha incorreta")

        if nivel in ["ADMIN", "MASTER"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔓 ABRIR"):
                    config["status_site"] = "ABERTO"
                    registrar_acao(nivel, "ABRIU CONSULTA")
            with col2:
                if st.button("🔒 FECHAR"):
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
st.markdown("### 🔍 Consulta Operacional de Rotas")

id_input = st.text_input(
    "Digite seu ID de motorista",
    value=st.session_state.id_motorista
)

if st.button("🔍 Consultar"):
    st.session_state.id_motorista = id_input.strip()
    st.session_state.consultado = True

if st.session_state.consultado and st.session_state.id_motorista:

    id_motorista = st.session_state.id_motorista

    df_rotas = carregar_rotas(URL_ROTAS)
    df_drivers = carregar_motoristas(URL_DRIVERS)

    if id_motorista not in set(df_drivers["ID"]):
        st.warning("⚠️ ID não encontrado.")
        st.stop()

    # ===== ROTAS DO MOTORISTA =====
    rotas_motorista = df_rotas[df_rotas["ID"] == id_motorista]
    if not rotas_motorista.empty:
        st.markdown("### 🚚 Suas rotas atribuídas")
        for _, row in rotas_motorista.iterrows():
            data_fmt = row["Data Exp."].strftime("%d/%m/%Y") if pd.notna(row["Data Exp."]) else "-"
            st.markdown(f"""
            <div class="card">
                <div class="flex-row">
                    <span><strong>ROTA:</strong> {row['Rota']}</span>
                    <span><strong>PLACA:</strong> {row['Placa']}</span>
                </div>
                <p><strong>NOME:</strong> {row['Nome']}</p>
                <div class="flex-row">
                    <span><strong>TIPO:</strong> {row['Tipo Veiculo']}</span>
                    <span><strong>DATA:</strong> {data_fmt}</span>
                </div>
                <div class="flex-row">
                    <span><strong>BAIRRO:</strong> {row['Bairro']}</span>
                    <span><strong>CIDADE:</strong> {row['Cidade']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ===== ROTAS DISPONÍVEIS =====
    rotas_disp = df_rotas[df_rotas["ID"] == ""]

    if not rotas_disp.empty:
        st.markdown("### 📦 Rotas disponíveis")

        for cidade, df_cidade in rotas_disp.groupby("Cidade"):
            with st.expander(f"🏙️ {cidade}", expanded=False):
                for _, row in df_cidade.iterrows():
                    data_fmt = row["Data Exp."].strftime("%d/%m/%Y") if pd.notna(row["Data Exp."]) else "-"
                    rota_key = f"{row['Rota']}_{row['Bairro']}_{data_fmt}"

                    form_url = (
                        f"{GOOGLE_FORM_URL}?usp=pp_url"
                        f"&entry.392776957={id_motorista}"
                        f"&entry.1682939517={row['Rota']}"
                        f"&entry.625563351={row['Cidade']}"
                        f"&entry.1284288730={row['Bairro']}"
                        f"&entry.1534916252=Tenho+Interesse"
                    )

                    # --- CARD COM ÍCONE DE VEÍCULO ---
                    icone = "🚗" if str(row["Tipo Veiculo"]).upper() == "PASSEIO" else "🏍️"

                    st.markdown(f"""
                    <div class="card">
                        <div class="flex-row">
                            <span>📍 Bairro: {row['Bairro']}</span>
                            <span>{icone} {row['Tipo Veiculo']}</span>
                        </div>
                        <p>📅 Data: {data_fmt}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if rota_key in st.session_state.interesses:
                        st.success("✔ Interesse registrado")
                        st.markdown(f"[👉 Abrir formulário]({form_url})")
                    else:
                        if st.button("✋ Tenho interesse nesta rota", key=f"btn_{rota_key}"):
                            st.session_state.interesses.add(rota_key)
                            st.success("✔ Interesse registrado")
                            st.markdown(f"[👉 Abrir formulário]({form_url})")

# ================= RODAPÉ =================
st.markdown("""
<hr>
<div style="text-align:center; color:#888; font-size:0.85em;">
<strong>RouteAssist</strong><br>
Concept & Development — Claudiane Vieira<br>
Since Dec/2025
</div>
""", unsafe_allow_html=True)
