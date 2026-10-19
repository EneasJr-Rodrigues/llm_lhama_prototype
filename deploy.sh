#!/bin/bash

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Iniciando Deploy do Cluster vLLM + Ray ===${NC}"

# Verifica se o docker e o docker compose estão instalados
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Erro: Docker não encontrado. Instale o Docker e o NVIDIA Container Toolkit primeiro.${NC}"
    exit 1
fi

# Leitura dos parâmetros do analista
ROLE=$1
HEAD_IP=$2

# ==========================================
# AMBIENTE DE PRODUÇÃO: HEAD NODE
# ==========================================
if [ "$ROLE" == "head" ]; then
    echo -e "${GREEN}Configurando este servidor como: HEAD NODE (Node 1)${NC}"
    
    # Validação do Token do Hugging Face
    echo -e "${BLUE}--- Etapa de Cache do Modelo ---${NC}"
    if [ -z "$HF_TOKEN" ]; then
        echo -e "${RED}Erro: A variável HF_TOKEN não está definida.${NC}"
        echo "Rode o comando exportando o token. Exemplo:"
        echo "export HF_TOKEN='hf_XyZaBc...' && ./deploy.sh head"
        exit 1
    fi

    echo "Fazendo o build da imagem Docker..."
    docker compose -f docker-compose-head.yml build
    
    echo "Verificando/Baixando os pesos do modelo Llama (Aguarde...)"
    docker compose -f docker-compose-head.yml run --rm ray-head python3 /app/download_hf.py
    echo -e "${GREEN}Modelo validado em cache local!${NC}"
    
    echo "Subindo o container do Head Node..."
    docker compose -f docker-compose-head.yml up -d
    
    echo -e "${GREEN}Deploy concluído! O Ray Head está rodando.${NC}"
    echo "Para ver os logs, digite: docker logs -f ray-head-node"

# ==========================================
# AMBIENTE DE PRODUÇÃO: WORKER NODE
# ==========================================
elif [ "$ROLE" == "worker" ]; then
    if [ -z "$HEAD_IP" ]; then
        echo -e "${RED}Erro: Para subir um worker, você precisa informar o IP do Head Node.${NC}"
        echo "Exemplo: ./deploy.sh worker 192.168.1.100"
        exit 1
    fi
    
    echo -e "${GREEN}Configurando este servidor como: WORKER NODE${NC}"
    echo "Conectando ao Head Node no IP: $HEAD_IP"
    export HEAD_NODE_IP=$HEAD_IP

    # Validação do Token do Hugging Face
    echo -e "${BLUE}--- Etapa de Cache do Modelo ---${NC}"
    if [ -z "$HF_TOKEN" ]; then
        echo -e "${RED}Erro: A variável HF_TOKEN não está definida.${NC}"
        echo "Rode o comando exportando o token. Exemplo:"
        echo "export HF_TOKEN='hf_XyZaBc...' && ./deploy.sh worker $HEAD_IP"
        exit 1
    fi
    
    echo "Fazendo o build da imagem Docker..."
    docker compose -f docker-compose-worker.yml build

    echo "Verificando/Baixando os pesos do modelo Llama (Aguarde...)"
    docker compose -f docker-compose-worker.yml run --rm ray-worker python3 /app/download_hf.py
    echo -e "${GREEN}Modelo validado em cache local!${NC}"
    
    echo "Subindo o container do Worker Node..."
    docker compose -f docker-compose-worker.yml up -d
    
    echo -e "${GREEN}Deploy concluído! O Worker está rodando e conectado ao cluster.${NC}"
    echo "Para ver os logs, digite: docker logs -f ray-worker-node"

# ==========================================
# AMBIENTE DE TESTE: LOCAL (WSL2 / Windows)
# ==========================================
elif [ "$ROLE" == "local" ]; then
    echo -e "${GREEN}Iniciando Ambiente de TESTE LOCAL (WSL2)...${NC}"
    echo -e "${BLUE}Nota: O modelo local (Qwen 3B) não exige token HF.${NC}"
    
    echo "Fazendo o build da imagem Docker..."
    docker compose -f docker-compose-local.yml build
    
    echo "Subindo o container local..."
    docker compose -f docker-compose-local.yml up -d
    
    echo -e "${GREEN}Ambiente local rodando!${NC}"
    echo -e "Para subir a API com o vLLM, digite:"
    echo -e "${BLUE}docker exec -it ray-local-test serve run deploy_local:servico${NC}"

# ==========================================
# TRATAMENTO DE ERRO: PARÂMETRO INVÁLIDO
# ==========================================
else
    echo -e "${RED}Parâmetro inválido ou ausente.${NC}"
    echo -e "Uso correto:"
    echo -e "  ./deploy.sh head             (Servidor de Produção 1)"
    echo -e "  ./deploy.sh worker <IP_HEAD> (Servidores de Produção 2 e 3)"
    echo -e "  ./deploy.sh local            (Sua Máquina de Testes Windows/WSL2)"
    exit 1
fi