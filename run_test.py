# run_test.py
import time
import requests
import json
import os
import argparse
from datetime import datetime

# Configuração de parâmetros via terminal
parser = argparse.ArgumentParser(description="Script de Teste de Carga e Evidência do vLLM")
parser.add_argument("--nome", type=str, default="teste_1", help="Nome do teste para versionamento (ex: teste_1)")
parser.add_argument("--reqs", type=int, default=5, help="Número de requisições sequenciais/concorrentes")
args = parser.parse_args()

URL_API = "http://127.0.0.1:8000/gerar"
PROMPT_TESTE = "Explique detalhadamente como funciona um motor de combustão interna, passo a passo."

os.makedirs("logs", exist_ok=True)

print(f"🚀 Iniciando [{args.nome}] com {args.reqs} requisições...")
resultados_individuais = []
inicio_teste = time.time()
tokens_totais = 0

for i in range(args.reqs):
    inicio_req = time.time()
    try:
        payload = {"prompt": PROMPT_TESTE}
        res = requests.post(URL_API, json=payload)
        fim_req = time.time()
        
        resposta_texto = res.json().get("resposta", "")
        # Estimativa simples: 1 palavra ~= 1.3 tokens
        tokens_estimados = len(resposta_texto.split()) * 1.3 
        tokens_totais += tokens_estimados
        latencia = fim_req - inicio_req
        
        resultados_individuais.append({
            "requisicao_id": i + 1,
            "status": res.status_code,
            "latencia_segundos": round(latencia, 2),
            "tokens_gerados": round(tokens_estimados),
            "tps_local": round(tokens_estimados / latencia, 2) if latencia > 0 else 0,
            "resposta_preview": resposta_texto[:150] + "..." # Salva o comecinho para provar que respondeu certo
        })
        print(f"  ↳ Req {i+1} OK! Latência: {round(latencia, 2)}s | Tokens: {round(tokens_estimados)}")
    
    except Exception as e:
        print(f"  ↳ Req {i+1} ERRO: {str(e)}")
        resultados_individuais.append({"requisicao_id": i+1, "status": "Erro", "erro": str(e)})

fim_teste = time.time()
tempo_total_teste = fim_teste - inicio_teste
throughput_global = tokens_totais / tempo_total_teste if tempo_total_teste > 0 else 0
latencia_media = tempo_total_teste / args.reqs

# Monta o JSON de evidência estruturada
evidencia = {
    "versao_teste": args.nome,
    "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modelo_alvo": "Llama-3.1-8B-Instruct (PT-BR)",
    "resumo_metricas": {
        "total_requisicoes": args.reqs,
        "tempo_total_segundos": round(tempo_total_teste, 2),
        "latencia_media_segundos": round(latencia_media, 2),
        "throughput_total_tps": round(throughput_global, 2),
        "total_tokens_processados": round(tokens_totais)
    },
    "logs_detalhados": resultados_individuais
}

# Salva o arquivo
caminho_arquivo = f"logs/{args.nome}.json"
with open(caminho_arquivo, "w", encoding="utf-8") as f:
    json.dump(evidencia, f, ensure_ascii=False, indent=4)

print(f"\n✅ Teste finalizado! Evidência gerada e salva em: {caminho_arquivo}")