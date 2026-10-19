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

if [ "$ROLE" == "head" ]; then
    echo -e "${GREEN}Configurando este servidor como: HEAD NODE (Node 1)${NC}"
    echo "Fazendo o build da imagem Docker..."
    docker compose -f docker-compose-head.yml build
    
    echo "Subindo o container do Head Node..."
    docker compose -f docker-compose-head.yml up -d
    
    echo -e "${GREEN}Deploy concluído! O Ray Head está rodando.${NC}"
    echo "Para ver os logs, digite: docker logs -f ray-head-node"

elif [ "$ROLE" == "worker" ]; then
    if [ -z "$HEAD_IP" ]; then
        echo -e "${RED}Erro: Para subir um worker, você precisa informar o IP do Head Node.${NC}"
        echo "Exemplo: ./deploy.sh worker 192.168.1.100"
        exit 1
    fi
    
    echo -e "${GREEN}Configurando este servidor como: WORKER NODE${NC}"
    echo "Conectando ao Head Node no IP: $HEAD_IP"
    
    # Exporta o IP para que o docker-compose-worker.yml consiga ler a variável
    export HEAD_NODE_IP=$HEAD_IP

    echo -e "${BLUE}--- Etapa de Cache do Modelo ---${NC}"
    # Exige que o analista passe o token como variável antes de executar o bash
    if [ -z "$HF_TOKEN" ]; then
        echo -e "${RED}Erro: A variável HF_TOKEN não está definida.${NC}"
        echo "Rode o comando exportando o token. Exemplo:"
        echo "export HF_TOKEN='hf_XyZaBc...' && ./deploy.sh head"
        exit 1
    fi

    echo "Verificando/Baixando os pesos do modelo (Aguarde...)"
    # Usa o próprio Docker para rodar o script de download temporariamente e salvar na pasta model_cache
    docker compose -f docker-compose-head.yml run --rm ray-head python3 /app/download_hf.py

    echo -e "${GREEN}Modelo validado em cache local! Subindo a infraestrutura...${NC}"
    
    echo "Fazendo o build da imagem Docker..."
    docker compose -f docker-compose-worker.yml build
    
    echo "Subindo o container do Worker Node..."
    docker compose -f docker-compose-worker.yml up -d
    
    echo -e "${GREEN}Deploy concluído! O Worker está rodando e conectado ao cluster.${NC}"
    echo "Para ver os logs, digite: docker logs -f ray-worker-node"

else
    echo -e "${RED}Parâmetro inválido ou ausente.${NC}"
    echo -e "Uso correto:"
    echo -e "  Para o servidor mestre: ./deploy.sh head"
    echo -e "  Para os trabalhadores:  ./deploy.sh worker <IP_DO_HEAD>"
    exit 1
fi