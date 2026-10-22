# chat_ui.py
import streamlit as st
import requests
import time
import json
import os
import uuid  # Novo: Garante IDs únicos que nunca se repetem
from datetime import datetime
from rag_connector import RAGManager
from sft_manager import MockSFTLoRA

URL_API = "http://127.0.0.1:8000/gerar"
MODELO_ATUAL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct")

st.set_page_config(page_title="LLM Chat MVP", page_icon="🤖", layout="wide")

rag = RAGManager(estrategia="mock")
sft = MockSFTLoRA()

# --- FUNÇÃO DE AUDITORIA (LOGS) ---
def salvar_log_interacao(prompt, resposta, latencia, tokens, tps, temperatura, max_tokens, id_mensagem):
    os.makedirs("/app/logs", exist_ok=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_log = f"/app/logs/chat_history_{hoje}.json"
    
    novo_registro = {
        "id_mensagem": id_mensagem,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modelo": MODELO_ATUAL,
        "parametros": {"temperatura": temperatura, "max_tokens": max_tokens},
        "prompt": prompt,
        "resposta_preview": resposta[:150].replace("\n", " ") + "...",
        "metricas_reais": {"latencia_segundos": latencia, "tokens_estimados": tokens, "tps_local": tps},
        "feedback_humano": "Pendente"
    }
    
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

def atualizar_feedback_log(id_mensagem, feedback):
    hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_log = f"/app/logs/chat_history_{hoje}.json"
    
    if os.path.exists(arquivo_log):
        try:
            with open(arquivo_log, "r", encoding="utf-8") as f:
                logs = json.load(f)
            
            for log in logs:
                if log.get("id_mensagem") == id_mensagem:
                    log["feedback_humano"] = feedback
                    break
            
            with open(arquivo_log, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"Erro ao salvar feedback: {e}")

# Inicializa o histórico
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://img.shields.io/badge/vLLM-Ray_Cluster-00BCD4?style=for-the-badge", use_container_width=True)
    st.title("⚙️ Parâmetros do Modelo")
    st.info(f"**🧠 Modelo Ativo:**\n`{MODELO_ATUAL}`")
    
    temperatura = st.slider("🌡️ Temperatura (Criatividade)", min_value=0.0, max_value=2.0, value=0.4, step=0.1)
    max_tokens = st.slider("📏 Máximo de Tokens", min_value=50, max_value=4096, value=2048, step=50)
    
    st.markdown("---")
    st.title("🎛️ Pesos e SFT (LoRA)")
    adaptador_ativo = st.selectbox("🎭 Adaptador SFT (Comportamento)", sft.listar_adaptadores())
    top_p = st.slider("🎯 Top-P (Foco de Vocabulário)", min_value=0.1, max_value=1.0, value=0.9, step=0.05)
    freq_penalty = st.slider("♻️ Penalidade de Frequência", min_value=0.0, max_value=2.0, value=1.05, step=0.05)
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()

# --- TELA PRINCIPAL ---
st.title("🤖 Chatbot de Homologação LLM")
st.markdown("Ambiente de testes conectado ao cluster local.")

for i, msg in enumerate(st.session_state.mensagens):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant" and "metricas" in msg:
            st.caption(msg["metricas"])
            
            col1, col2, col_vazia = st.columns([1.5, 2, 8])
            
            # Lógica de bloqueio dos botões
            ja_avaliou = msg.get("feedback") is not None
            label_bom = "✅ Aprovado" if msg.get("feedback") == "bom" else "👍 Bom"
            label_ruim = "❌ Reprovado" if msg.get("feedback") == "ruim" else "👎 Alucinou"
            
            with col1:
                if st.button(label_bom, key=f"up_{msg['id']}", disabled=ja_avaliou):
                    msg["feedback"] = "bom"
                    atualizar_feedback_log(msg["id"], "Aprovado (Bom)")
                    st.rerun()
            with col2:
                if st.button(label_ruim, key=f"down_{msg['id']}", disabled=ja_avaliou):
                    msg["feedback"] = "ruim"
                    atualizar_feedback_log(msg["id"], "Reprovado (Alucinação)")
                    st.rerun()

if prompt_usuario := st.chat_input("Digite sua pergunta ou instrução..."):
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    with st.chat_message("assistant"):
        placeholder_resposta = st.empty()
        placeholder_resposta.markdown("⏳ *Processando...*")
        
        instrucoes_sistema = ""
        if os.path.exists("/app/system_prompt.txt"):
            with open("/app/system_prompt.txt", "r", encoding="utf-8") as f:
                instrucoes_sistema = f.read()
                
        documento_interno = rag.obter_contexto(prompt_usuario)
        mascara_sft = sft.aplicar_pesos(adaptador_ativo)
        
        # Montagem do Super Prompt usando o Chat Template oficial do Llama 3
        prompt_enriquecido = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {instrucoes_sistema}
        {mascara_sft}

        INFORMAÇÃO INTERNA DA EMPRESA:
        {documento_interno}

        Instrução Adicional: Se a 'INFORMAÇÃO INTERNA' disser que não há documentos, você tem permissão para usar seu conhecimento geral de mundo para responder à pergunta do usuário da melhor forma possível.<|eot_id|><|start_header_id|>user<|end_header_id|>

        {prompt_usuario}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        
        payload = {
            "prompt": prompt_enriquecido,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": freq_penalty,
            "repetition_penalty": 1.15
        }
        
        inicio = time.time()
        try:
            res = requests.post(URL_API, json=payload)
            fim = time.time()
            
            if res.status_code == 200:
                resposta_final = res.json().get("resposta", "")
                
                latencia = round(fim - inicio, 2)
                tokens_estimados = int(len(resposta_final.split()) * 1.3)
                tps = round(tokens_estimados / latencia, 2) if latencia > 0 else 0
                string_metricas = f"⏱️ {latencia}s | 🚀 {tps} TPS | 📏 {tokens_estimados} Tokens"
                
                placeholder_resposta.markdown(resposta_final)
                
                msg_id = str(uuid.uuid4())
                
                st.session_state.mensagens.append({
                    "id": msg_id,
                    "role": "assistant", 
                    "content": resposta_final,
                    "metricas": string_metricas,
                    "feedback": None
                })
                
                salvar_log_interacao(prompt_usuario, resposta_final, latencia, tokens_estimados, tps, temperatura, max_tokens, msg_id)
                st.rerun()
                
            else:
                placeholder_resposta.error(f"Erro na API: {res.status_code}")
        except Exception as e:
            placeholder_resposta.error(f"Falha de conexão: {e}")