# MVP LLM Multi-Node

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
4. Conta no Hugging Face com acesso liberado ao modelo Llama 3.1 e um Token de Acesso (apenas para os servidores de produção).

> **Atenção:** Como utilizamos Docker, **não é necessário** criar uma `venv` ou instalar o Python no servidor físico. O contêiner já gerencia todas as dependências do `requirements.txt`.

## 🚀 Como fazer o Deploy

### Passo 1: Configurar o Head Node (Servidor 1)
O Head Node é o maestro do cluster. Ele recebe as requisições HTTP e distribui a carga.
Acesse o **Servidor 1**, clone este repositório e execute:

```bash
git clone <url-do-repositorio>
cd mvp-llm
chmod +x deploy.sh

# Exporte seu token do Hugging Face (Obrigatório para baixar o Llama 3.1)
export HF_TOKEN="hf_seu_token_aqui"

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

# Exporte o token também nos workers (pois cada placa baixará seu próprio cache)
export HF_TOKEN="hf_seu_token_aqui"

# Substitua o IP abaixo pelo IP real do Servidor 1
./deploy.sh worker 10.0.0.50
```

### 💻 Ambiente de Teste Local (WSL2 / Windows)
Para validar a arquitetura localmente em placas de vídeo menores (ex: RTX 2080 Ti), o sistema contornará a restrição de memória utilizando um modelo menor e aberto (`Qwen-2.5-3B-Instruct`), sem a necessidade de Token do Hugging Face.

1. Abra seu terminal WSL2 (Ubuntu).
2. Clone o repositório e dê permissão de execução: `chmod +x deploy.sh`
3. Execute o comando local:
   ```bash
   ./deploy.sh local
   ```
4. Suba a API no container local utilizando o script de teste:

```bash
docker exec -it ray-local-test serve run deploy_local:servico
```

### Passo 3: Inicializar o Modelo
Após os 3 servidores estarem rodando, acesse novamente o terminal do **Servidor 1** e injete o script Python de deployment para baixar o modelo e distribuir nas 3 GPUs:

```bash
docker exec -it ray-head-node serve run deploy:servico
```

## 📊 Acesso e Monitoramento
- **API do LLM:** `http://<IP_DO_SERVIDOR_1>:8000/gerar`
- **Dashboard do Ray:** `http://<IP_DO_SERVIDOR_1>:8265`
- **Interface Chat (Streamlit):** `http://<IP_DO_SERVIDOR_1>:8501` (ou `http://localhost:8501` se rodando localmente)
- **Painel de Evidências (Métricas):** Abra o arquivo local `dashboard.html` diretamente no seu navegador Windows.

## ⚙️ Configuração do Ambiente (.env)
Este projeto utiliza a arquitetura baseada em variáveis de ambiente para facilitar a troca de modelos e proteger credenciais (Metodologia 12-Factor). 

Antes de iniciar qualquer ambiente (Local ou Produção), crie um arquivo chamado `.env` na raiz do projeto contendo:

```env
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
HF_TOKEN=seu_token_do_hugging_face
```

## 🔄 Como Trocar de Modelo (Hot-Swap)
Para trocar o motor de inteligência artificial em toda a arquitetura, você não precisa alterar nenhuma linha de código.
1. Pare a infraestrutura atual (se estiver rodando).
2. Abra o arquivo `.env` e altere a variável `LLM_MODEL`.
3. Suba a infraestrutura novamente (`./deploy.sh local` ou `./deploy.sh head`).

### Exemplos de Modelos Suportados
* **Qwen 2.5 (3B):** `Qwen/Qwen2.5-3B-Instruct` (Ideal para testes locais com baixa VRAM).
* **Llama 3.1 (8B):** `meta-llama/Llama-3.1-8B-Instruct` (Recomendado para produção nas GPUs V100).
* **Gemma 2 (9B):** `google/gemma-2-9b-it` (Alternativa de alto desempenho).

O sistema fará o download do novo modelo automaticamente na inicialização. O Streamlit, a API e os relatórios de Teste de Carga adotarão o novo nome instantaneamente.

## 🖥️ Interface Gráfica e Testes de Estresse

### 1. Interface Chatbot (Streamlit)
Para subir a interface visual e interagir com o modelo de forma amigável, abra um novo terminal (após inicializar o modelo) e execute o processo em segundo plano:
- **Ambiente Local:** `docker exec -d ray-local-test streamlit run chat_ui.py --server.address=0.0.0.0`
- **Ambiente Produção (Head Node):** `docker exec -d ray-head-node streamlit run chat_ui.py --server.address=0.0.0.0`

### 2. Testes de Carga e Performance
Para validar a infraestrutura (Throughput e Latência), execute o script de estresse em um terminal separado. O script simulará requisições simultâneas e gerará um arquivo `.json` de evidências.
- **Ambiente Local:** `docker exec -it ray-local-test python3 run_test.py --nome "teste_local" --reqs 5`
- **Ambiente Produção:** `docker exec -it ray-head-node python3 run_test.py --nome "teste_prod" --reqs 5`

*O arquivo gerado será salvo na pasta `/logs`. Basta arrastá-lo para dentro do seu `dashboard.html` para visualizar os gráficos de TPS.*

### 3. Exemplos de Prompts para Homologação
Utilize os exemplos abaixo no Streamlit ajustando a Temperatura e os Tokens para testar os limites do modelo:

1. **Lógica e Abstração (Temperatura 0.1 - Respostas precisas):** 
   > "Explique a diferença entre Docker e Máquina Virtual de forma simples, usando uma analogia com casas e condomínios."

2. **Programação e Formatação (Temperatura 0.4 - Respostas estruturadas):** 
   > "Escreva um script em Python que leia um arquivo de log '.txt', extraia todas as linhas que contenham a palavra 'ERROR' e salve em um novo arquivo."

3. **Geração Corporativa (Temperatura 0.9 - Respostas criativas):** 
   > "Escreva um e-mail profissional e persuasivo para a diretoria da CRP Tecnologia, justificando por que a arquitetura local com Ray e vLLM é estrategicamente superior a depender de APIs externas pagas."