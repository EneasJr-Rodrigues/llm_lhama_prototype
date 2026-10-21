# chat_ui.py
import streamlit as st
import requests
import time
import json
import os
from datetime import datetime
from rag_connector import RAGManager
from sft_manager import MockSFTLoRA

# Inicializa as arquiteturas
rag = RAGManager(estrategia="mock")
sft = MockSFTLoRA()

URL_API = "http://127.0.0.1:8000/gerar"
MODELO_ATUAL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct")

st.set_page_config(page_title="LLM Chat MVP", page_icon="🤖", layout="wide")

# --- FUNÇÃO DE AUDITORIA (LOGS) ---
def salvar_log_interacao(prompt, resposta, latencia, tokens, tps, temperatura, max_tokens, id_mensagem):
    """Salva a interação inicial no log."""
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
        "feedback_humano": "Pendente" # Será atualizado quando o usuário clicar no botão
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
    """Atualiza o arquivo JSON com a avaliação do usuário."""
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

# Inicializa as variáveis na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "msg_counter" not in st.session_state:
    st.session_state.msg_counter = 0

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
with st.sidebar:
    st.image("https://img.shields.io/badge/vLLM-Ray_Cluster-00BCD4?style=for-the-badge", use_container_width=True)
    st.title("⚙️ Parâmetros do Modelo")
    
    st.info(f"**🧠 Modelo Ativo:**\n`{MODELO_ATUAL}`")
    
    temperatura = st.slider("🌡️ Temperatura (Criatividade)", min_value=0.0, max_value=2.0, value=0.6, step=0.1)
    max_tokens = st.slider("📏 Máximo de Tokens", min_value=50, max_value=4096, value=1024, step=50)

    st.markdown("---")
    st.title("🎛️ Pesos e SFT (LoRA)")
    
    # Simula a troca do adaptador LoRA em tempo real
    adaptador_ativo = st.selectbox("🎭 Adaptador SFT (Comportamento)", sft.listar_adaptadores())
    
    # Parâmetros matemáticos para levar o modelo ao limite
    top_p = st.slider("🎯 Top-P (Foco de Vocabulário)", min_value=0.1, max_value=1.0, value=0.9, step=0.05,
                      help="Limita o modelo a escolher palavras que somam X% de probabilidade. Menor = mais rígido.")
    
    freq_penalty = st.slider("♻️ Penalidade de Frequência", min_value=0.0, max_value=2.0, value=1.05, step=0.05,
                             help="Punição pesada para palavras que o modelo já usou muito na resposta atual.")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()

# --- TELA PRINCIPAL (CHAT) ---
st.title("🤖 Chatbot de Homologação LLM")
st.markdown("Ambiente de testes conectado ao cluster local.")

# Renderiza o histórico de mensagens
for i, msg in enumerate(st.session_state.mensagens):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Se for o bot, exibe as métricas e os botões de feedback
        if msg["role"] == "assistant" and "metricas" in msg:
            st.caption(msg["metricas"]) # Métricas na linha de cima
            
            # Cria colunas estreitas alinhadas à esquerda
            col1, col2, col_vazia = st.columns([1.5, 2, 8])
            
            with col1:
                if st.button("👍 Bom", key=f"up_{i}"):
                    atualizar_feedback_log(msg["id"], "Aprovado (Bom)")
                    st.toast("Feedback positivo registrado!")
            with col2:
                if st.button("👎 Alucinou", key=f"down_{i}"):
                    atualizar_feedback_log(msg["id"], "Reprovado (Alucinação)")
                    st.toast("Alucinação registrada para auditoria!")

# Caixa de input do usuário
if prompt_usuario := st.chat_input("Digite sua pergunta ou instrução..."):
    
    st.session_state.mensagens.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    with st.chat_message("assistant"):
        placeholder_resposta = st.empty()
        placeholder_resposta.markdown("⏳ *Processando...*")
        
        # Lê o System Prompt
        instrucoes_sistema = ""
        if os.path.exists("/app/system_prompt.txt"):
            with open("/app/system_prompt.txt", "r", encoding="utf-8") as f:
                instrucoes_sistema = f.read()
        
        # 1. Lê o System Prompt de formatação
        instrucoes_sistema = ""
        if os.path.exists("/app/system_prompt.txt"):
            with open("/app/system_prompt.txt", "r", encoding="utf-8") as f:
                instrucoes_sistema = f.read()
        
        # 2. Busca informações internas baseadas na pergunta (RAG)
        documento_interno = rag.obter_contexto(prompt_usuario)

        # 2.1. Busca a máscara comportamental do SFT Mock
        mascara_sft = sft.aplicar_pesos(adaptador_ativo)
        
        # 3. Monta o Super Prompt (System + RAG + Usuário)
        prompt_enriquecido = f"""{instrucoes_sistema}
        {mascara_sft}

        INFORMAÇÃO INTERNA DA EMPRESA:
        {documento_interno}

        Pergunta do usuário: {prompt_usuario}"""
        
        # Payload com os parâmetros levados ao limite
        payload = {
            "prompt": prompt_enriquecido,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": freq_penalty,  # Usa a nova variável do slider
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
                
                # Gera ID único para o log
                st.session_state.msg_counter += 1
                msg_id = f"msg_{st.session_state.msg_counter}"
                
                st.session_state.mensagens.append({
                    "id": msg_id,
                    "role": "assistant", 
                    "content": resposta_final,
                    "metricas": string_metricas
                })
                
                salvar_log_interacao(prompt_usuario, resposta_final, latencia, tokens_estimados, tps, temperatura, max_tokens, msg_id)
                st.rerun() # Atualiza a tela para renderizar os botões
                
            else:
                placeholder_resposta.error(f"Erro na API: {res.status_code}")
        except Exception as e:
            placeholder_resposta.error(f"Falha de conexão: {e}")