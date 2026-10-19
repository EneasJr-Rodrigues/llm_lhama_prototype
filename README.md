# MVP LLM Multi-Node (CRP Tecnologia)

![NVIDIA](https://img.shields.io/badge/NVIDIA_V100-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Ray Serve](https://img.shields.io/badge/Ray_Serve-028EE6?style=for-the-badge)
![vLLM](https://img.shields.io/badge/vLLM-FF6F00?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)

Este repositório contém a infraestrutura como código para fazer o deploy distribuído do modelo **Llama-3.1-8B-Instruct** em um cluster de GPUs NVIDIA V100, utilizando Ray Serve e vLLM.

## 📋 Pré-requisitos (Nos 3 Servidores)
Antes de clonar este projeto, certifique-se de que cada servidor possui:
1. Drivers da NVIDIA instalados (`nvidia-smi` respondendo).
2. Docker instalado.
3. NVIDIA Container Toolkit instalado (para o Docker enxergar a GPU).

> **Atenção:** Como utilizamos Docker, **não é necessário** criar uma `venv` ou instalar o Python no servidor físico. O contêiner já gerencia todas as dependências do `requirements.txt`.

## 🚀 Como fazer o Deploy

### Passo 1: Configurar o Head Node (Servidor 1)
O Head Node é o maestro do cluster. Ele recebe as requisições HTTP e distribui a carga.
Acesse o **Servidor 1**, clone este repositório e execute:

```bash
git clone <url-do-repositorio>
cd mvp-llm
chmod +x deploy.sh

# Inicia o servidor principal
./deploy.sh head
```
*Anote o endereço IP interno deste servidor 1 (ex: `10.0.0.50`). Você precisará dele no próximo passo.*

### Passo 2: Configurar os Worker Nodes (Servidores 2 e 3)
Acesse os outros dois servidores, clone o repositório neles e execute o script apontando para o IP do Servidor 1:

```bash
git clone <url-do-repositorio>
cd mvp-llm
chmod +x deploy.sh

# Substitua o IP abaixo pelo IP real do Servidor 1
./deploy.sh worker 10.0.0.50
```

### Passo 3: Inicializar o Modelo
Após os 3 servidores estarem rodando, acesse novamente o terminal do **Servidor 1** e injete o script Python de deployment para baixar o modelo e distribuir nas 3 GPUs:

```bash
docker exec -it ray-head-node serve run deploy:servico
```

## 📊 Acesso e Monitoramento
- **API do LLM:** `http://<IP_DO_SERVIDOR_1>:8000/gerar`
- **Dashboard do Ray:** `http://<IP_DO_SERVIDOR_1>:8265`