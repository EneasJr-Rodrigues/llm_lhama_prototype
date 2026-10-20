import requests
import time
import json
import argparse
import os
from datetime import datetime

# Configuração dos argumentos da linha de comando
parser = argparse.ArgumentParser()
parser.add_argument("--nome", type=str, default="teste_homologacao")
parser.add_argument("--reqs", type=int, default=5)
args = parser.parse_args()

URL_API = "http://127.0.0.1:8000/gerar"
resultados = []

MODELO_ATUAL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct")

print(f"🚀 Iniciando {args.reqs} requisições de estresse contra a API Local...")

# Variáveis para calcular as métricas gerais do painel
inicio_teste_geral = time.time()
total_latencia = 0
total_tokens = 0
sucessos = 0

for i in range(args.reqs):
    payload = {
        "prompt": "Explique o que é Inteligência Artificial em um parágrafo curto.",
        "temperature": 0.7,
        "max_tokens": 512
    }
    
    inicio_req = time.time()
    try:
        res = requests.post(URL_API, json=payload, timeout=60)
        fim_req = time.time()
        
        if res.status_code == 200:
            resposta_texto = res.json().get("resposta", "")
            latencia = round(fim_req - inicio_req, 2)
            
            # Estimativa de tokens gerados
            tokens_gerados = int(len(resposta_texto.split()) * 1.3)
            tps = round(tokens_gerados / latencia, 2) if latencia > 0 else 0
            
            # Soma para o resumo final
            total_latencia += latencia
            total_tokens += tokens_gerados
            sucessos += 1
            
            resultados.append({
                "requisicao_id": i + 1,
                "status": "Sucesso",
                "latencia_segundos": latencia,
                "tokens_gerados": tokens_gerados,
                "tps_local": tps,
                "resposta_preview": resposta_texto[:60].replace("\n", " ") + "..."
            })
            print(f"✅ Req #{i+1} | Latência: {latencia}s | TPS: {tps} tokens/s")
        else:
            raise Exception(f"Erro HTTP {res.status_code}")
            
    except Exception as e:
        resultados.append({
            "requisicao_id": i + 1,
            "status": "Erro",
            "latencia_segundos": 0,
            "tokens_gerados": 0,
            "tps_local": 0,
            "resposta_preview": str(e)
        })
        print(f"❌ Req #{i+1} | FALHA | {str(e)}")

# Cálculo das métricas consolidadas
tempo_total = round(time.time() - inicio_teste_geral, 2)
latencia_media = round(total_latencia / sucessos, 2) if sucessos > 0 else 0
throughput_total = round(total_tokens / tempo_total, 2) if tempo_total > 0 else 0

os.makedirs("logs", exist_ok=True)
nome_arquivo = f"logs/{args.nome}.json"

# Estrutura exata exigida pelo dashboard.html
dados_finais = {
    "versao_teste": args.nome,
    "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modelo_alvo": MODELO_ATUAL,
    "resumo_metricas": {
        "total_requisicoes": args.reqs,
        "throughput_total_tps": throughput_total,
        "latencia_media_segundos": latencia_media,
        "tempo_total_segundos": tempo_total
    },
    "logs_detalhados": resultados
}

with open(nome_arquivo, "w", encoding="utf-8") as f:
    json.dump(dados_finais, f, ensure_ascii=False, indent=4)

print(f"\n✅ Teste finalizado! Arquivo salvo com sucesso em: {nome_arquivo}")