# chat_ui.py
import streamlit as st
import requests

URL_API = "http://127.0.0.1:8000/gerar"

st.set_page_config(page_title="LLM Chat MVP", page_icon="🤖", layout="wide")

# Inicializa o histórico de mensagens na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
with st.sidebar:
    st.image("https://img.shields.io/badge/vLLM-Ray_Cluster-00BCD4?style=for-the-badge", use_container_width=True)
    st.title("⚙️ Parâmetros do Modelo")
    st.markdown("Ajuste o comportamento do LLM em tempo real.")
    
    temperatura = st.slider("🌡️ Temperatura (Criatividade)", min_value=0.0, max_value=2.0, value=0.7, step=0.1, 
                            help="Valores próximos a 0 deixam o modelo mais robótico e exato. Valores altos deixam ele mais criativo.")
    
    max_tokens = st.slider("📏 Máximo de Tokens (Tamanho da resposta)", min_value=50, max_value=4096, value=1024, step=50)
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()

# --- TELA PRINCIPAL (CHAT) ---
st.title("🤖 Chatbot de Homologação LLM")
st.markdown("Ambiente de testes conectado ao cluster local.")

# Renderiza o histórico de mensagens na tela
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Caixa de input do usuário no rodapé
if prompt_usuario := st.chat_input("Digite sua pergunta ou instrução..."):
    
    # 1. Adiciona e mostra a mensagem do usuário
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # 2. Mostra o "Pensando..." e chama a API
    with st.chat_message("assistant"):
        placeholder_resposta = st.empty()
        placeholder_resposta.markdown("⏳ *Processando...*")
        
        payload = {
            "prompt": prompt_usuario,
            "temperature": temperatura,
            "max_tokens": max_tokens
        }
        
        try:
            res = requests.post(URL_API, json=payload)
            if res.status_code == 200:
                resposta_final = res.json().get("resposta", "")
                placeholder_resposta.markdown(resposta_final)
                
                # Salva a resposta do bot no histórico
                st.session_state.mensagens.append({"role": "assistant", "content": resposta_final})
            else:
                placeholder_resposta.error(f"Erro na API: {res.status_code}")
        except Exception as e:
            placeholder_resposta.error(f"Falha de conexão com o vLLM: {e}")