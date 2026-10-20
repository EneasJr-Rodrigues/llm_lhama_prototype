# chat_ui.py
import streamlit as st
import requests
import time
import json
import os
from datetime import datetime

URL_API = "http://127.0.0.1:8000/gerar"
MODELO_ATUAL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct")

st.set_page_config(page_title="LLM Chat MVP", page_icon="🤖", layout="wide")

# --- FUNÇÃO DE AUDITORIA (LOGS) ---
def salvar_log_interacao(prompt, resposta, latencia, tokens, tps, temperatura, max_tokens):
    """Salva silenciosamente cada interação no formato JSON na pasta de logs."""
    os.makedirs("/app/logs", exist_ok=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_log = f"/app/logs/chat_history_{hoje}.json"
    
    novo_registro = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "parametros": {
            "temperatura": temperatura,
            "max_tokens": max_tokens
        },
        "prompt": prompt,
        "resposta_preview": resposta[:150].replace("\n", " ") + "...",
        "metricas_reais": {
            "latencia_segundos": latencia,
            "tokens_estimados": tokens,
            "tps_local": tps
        }
    }
    
    # Se o arquivo já existir no dia, adiciona o log na lista. Se não, cria um novo.
    logs = []
    if os.path.exists(arquivo_log):
        try:
            with open(arquivo_log, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            pass
            
    logs.append(novo_registro)
    
    with open(arquivo_log, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)


# Inicializa o histórico de mensagens na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
with st.sidebar:
    # Ajustado para a nova diretriz (use_container_width)
    st.image("https://img.shields.io/badge/vLLM-Ray_Cluster-00BCD4?style=for-the-badge", use_container_width=True)
    st.title("⚙️ Parâmetros do Modelo")
    st.markdown("Ajuste o comportamento do LLM em tempo real.")
    
    temperatura = st.slider("🌡️ Temperatura (Criatividade)", min_value=0.0, max_value=2.0, value=0.7, step=0.1, 
                            help="Valores próximos a 0 deixam o modelo mais exato. Valores altos deixam criativo.")
    st.info(f"**🧠 Modelo Ativo:**\n`{MODELO_ATUAL}`")
    
    max_tokens = st.slider("📏 Máximo de Tokens", min_value=50, max_value=4096, value=1024, step=50)
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()

# --- TELA PRINCIPAL (CHAT) ---
st.title("🤖 Chatbot de Homologação LLM")
st.markdown("Ambiente de testes conectado ao cluster local.")

# Renderiza o histórico de mensagens na tela (incluindo as métricas)
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Se a mensagem tiver métricas salvas, exibe um rodapé elegante
        if "metricas" in msg:
            st.caption(msg["metricas"])

# Caixa de input do usuário no rodapé
if prompt_usuario := st.chat_input("Digite sua pergunta ou instrução..."):
    
    # 1. Adiciona e mostra a mensagem do usuário
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    # 2. Mostra o "Pensando...", calcula métricas e chama a API
    with st.chat_message("assistant"):
        placeholder_resposta = st.empty()
        placeholder_resposta.markdown("⏳ *Processando...*")
        
        payload = {
            "prompt": prompt_usuario,
            "temperature": temperatura,
            "max_tokens": max_tokens
        }
        
        inicio = time.time()
        try:
            res = requests.post(URL_API, json=payload)
            fim = time.time()
            
            if res.status_code == 200:
                resposta_final = res.json().get("resposta", "")
                
                # --- MATEMÁTICA DE PERFORMANCE ---
                latencia = round(fim - inicio, 2)
                tokens_estimados = int(len(resposta_final.split()) * 1.3)
                tps = round(tokens_estimados / latencia, 2) if latencia > 0 else 0
                
                string_metricas = f"⏱️ {latencia}s | 🚀 {tps} TPS | 📏 {tokens_estimados} Tokens"
                
                # Atualiza a tela com a resposta e as métricas
                placeholder_resposta.markdown(resposta_final)
                st.caption(string_metricas)
                
                # Salva no histórico da tela
                st.session_state.mensagens.append({
                    "role": "assistant", 
                    "content": resposta_final,
                    "metricas": string_metricas
                })
                
                # Salva o log silencioso no JSON de auditoria
                salvar_log_interacao(prompt_usuario, resposta_final, latencia, tokens_estimados, tps, temperatura, max_tokens)
                
            else:
                placeholder_resposta.error(f"Erro na API: {res.status_code}")
        except Exception as e:
            placeholder_resposta.error(f"Falha de conexão com o vLLM: {e}")