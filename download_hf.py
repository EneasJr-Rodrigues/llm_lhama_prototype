# download_hf.py
import os
import sys
from huggingface_hub import snapshot_download

# Busca o nome do modelo nas variáveis de ambiente. Se não achar, usa o Llama como padrão.
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3.1-8B-Instruct")
HF_TOKEN = os.environ.get("HF_TOKEN")
CACHE_DIR = "/app/model_cache"

# Lógica inteligente: Modelos da Meta (Llama) são "Gated" (fechados) e exigem token.
# Modelos abertos (como o Qwen) não exigem token, então não devemos travar a execução.
if "llama" in MODEL_NAME.lower() and not HF_TOKEN:
    print(f"ERRO: O modelo '{MODEL_NAME}' é restrito e exige autenticação.")
    print("A variável de ambiente HF_TOKEN não foi encontrada.")
    print("Por favor, exporte o token antes de rodar: export HF_TOKEN='seu_token_aqui'")
    sys.exit(1)

print(f"Iniciando a verificação/download do modelo: {MODEL_NAME}")
print(f"Destino (Cache Local): {CACHE_DIR}")
print("Aguarde, isso pode levar alguns minutos na primeira vez...")

try:
    # Baixa apenas os arquivos cruciais em formato safetensors
    # Se HF_TOKEN for None (no caso do Qwen local), a biblioteca ignora e baixa anonimamente
    snapshot_download(
        repo_id=MODEL_NAME,
        token=HF_TOKEN,
        cache_dir=CACHE_DIR,
        ignore_patterns=["*.bin", "*.pt", "*.h5"] 
    )
    print(f"\n✅ Sucesso! Modelo '{MODEL_NAME}' validado e armazenado em {CACHE_DIR}")
except Exception as e:
    print(f"\n❌ Erro ao baixar o modelo: {e}")
    sys.exit(1)