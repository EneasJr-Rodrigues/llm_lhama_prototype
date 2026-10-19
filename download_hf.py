# download_hf.py
import os
import sys
from huggingface_hub import snapshot_download

# Puxa o token das variáveis de ambiente do sistema
HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    print("ERRO: A variável de ambiente HF_TOKEN não foi encontrada.")
    print("Por favor, exporte o token antes de rodar: export HF_TOKEN='seu_token_aqui'")
    sys.exit(1)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# Define que o modelo será salvo na pasta compartilhada de cache
CACHE_DIR = "/app/model_cache"

print(f"Iniciando o download do modelo {MODEL_NAME}...")
print("Isso pode levar vários minutos dependendo da sua rede (Tamanho: ~16GB)...")

try:
    # Baixa apenas os arquivos necessários (safetensors), ignorando os formatos antigos (.bin) para economizar espaço
    snapshot_download(
        repo_id=MODEL_NAME,
        token=HF_TOKEN,
        cache_dir=CACHE_DIR,
        ignore_patterns=["*.bin", "*.pt", "*.h5"] 
    )
    print(f"\nDownload concluído com sucesso! Modelo armazenado em {CACHE_DIR}")
except Exception as e:
    print(f"\nErro ao baixar o modelo: {e}")
    sys.exit(1)