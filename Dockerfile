# Usa uma imagem oficial da NVIDIA com CUDA 12.1 e Ubuntu 22.04
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Evita perguntas interativas do terminal durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instala Python, pip e utilitários
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualiza o pip e instala o Ray (com módulo Serve), vLLM e o Prometheus para o nosso Dashboard
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir "ray[serve]" vllm prometheus_client

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia o script Python de deployment (que criaremos abaixo)
COPY deploy.py /app/deploy.py

# Expõe as portas: 
# 6379 (Comunicação do Cluster Ray)
# 8265 (Dashboard administrativo visual do Ray)
# 8000 (Sua API onde o chatbot fará as requisições)
EXPOSE 6379 8265 8000

CMD ["bash"]