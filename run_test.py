import requests
import time
import json
import argparse
import os
from datetime import datetime

# Importações para telemetria de hardware
try:
    import pynvml
    import psutil
    HW_MONITORING_AVAILABLE = True
except ImportError:
    HW_MONITORING_AVAILABLE = False

# Configuração dos argumentos da linha de comando
parser = argparse.ArgumentParser()
parser.add_argument("--nome", type=str, default="teste_homologacao")
parser.add_argument("--reqs", type=int, default=5)
args = parser.parse_args()

URL_API = "http://127.0.0.1:8000/gerar"
resultados = []

MODELO_ATUAL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-3B-Instruct")

def obter_metricas_hardware():
    """Captura o estado térmico e energético do servidor no momento exato."""
    hw_stats = {
        "gpu_temp_c": 0,
        "gpu_power_w": 0.0,
        "cpu_temp_c": 0,
        "estrangulamento_termico": False
    }
    
    if HW_MONITORING_AVAILABLE:
        try:
            # Sensores da GPU NVIDIA
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            gpu_power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0 # Convertido para Watts
            
            hw_stats["gpu_temp_c"] = gpu_temp
            hw_stats["gpu_power_w"] = round(gpu_power, 2)
            hw_stats["estrangulamento_termico"] = bool(gpu_temp >= 82) # Gatilho padrão de Throttling
            
            # Sensores da CPU (Pode ser restrito dentro do Docker, usa try seguro)
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps and 'coretemp' in temps:
                    hw_stats["cpu_temp_c"] = round(temps['coretemp'][0].current, 1)
        except Exception:
            pass
            
    return hw_stats

print(f"🚀 Iniciando {args.reqs} requisições de estresse contra a API Local...")
if not HW_MONITORING_AVAILABLE:
    print("⚠️  Aviso: Bibliotecas 'pynvml' ou 'psutil' não encontradas. Métricas de hardware sairão zeradas.")

# Variáveis para calcular as métricas gerais do painel
inicio_teste_geral = time.time()
total_latencia = 0
total_ttft = 0
total_tokens = 0
sucessos = 0

for i in range(args.reqs):
    payload = {
        "prompt": "Explique o que é Inteligência Artificial em um parágrafo curto.",
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": True
    }
    
    inicio_req = time.time()
    primeiro_token_recebido = False
    ttft = 0
    resposta_texto = ""
    
    try:
        # stream=True permite cronometrar o Time To First Token (TTFT)
        res = requests.post(URL_API, json=payload, timeout=60, stream=True)
        
        if res.status_code == 200:
            # Captura a API devolvendo a resposta em fluxo ou bloco único
            for chunk in res.iter_content(chunk_size=1024):
                if not primeiro_token_recebido and chunk:
                    ttft = round(time.time() - inicio_req, 3)
                    primeiro_token_recebido = True
                
                if chunk:
                    resposta_texto += chunk.decode('utf-8', errors='ignore')
            
            fim_req = time.time()
            latencia = round(fim_req - inicio_req, 2)
            
            # Se a API não suportar streaming puro, o TTFT será o tempo de resposta total
            if ttft == 0:
                ttft = latencia
                
            # Limpeza do JSON bruto que a API envia
            try:
                json_resp = json.loads(resposta_texto)
                resposta_texto = json_resp.get("resposta", resposta_texto)
            except:
                pass
            
            tokens_gerados = int(len(resposta_texto.split()) * 1.3)
            tps = round(tokens_gerados / latencia, 2) if latencia > 0 else 0
            
            total_latencia += latencia
            total_ttft += ttft
            total_tokens += tokens_gerados
            sucessos += 1
            
            resultados.append({
                "requisicao_id": i + 1,
                "status": "Sucesso",
                "latencia_segundos": latencia,
                "ttft_segundos": ttft,
                "tokens_gerados": tokens_gerados,
                "tps_local": tps,
                "resposta_preview": resposta_texto[:60].replace("\n", " ") + "..."
            })
            print(f"✅ Req #{i+1} | Latência: {latencia}s | TTFT: {ttft}s | TPS: {tps} tokens/s")
        else:
            raise Exception(f"Erro HTTP {res.status_code}")
            
    except Exception as e:
        resultados.append({
            "requisicao_id": i + 1,
            "status": "Erro",
            "latencia_segundos": 0,
            "ttft_segundos": 0,
            "tokens_gerados": 0,
            "tps_local": 0,
            "resposta_preview": str(e)
        })
        print(f"❌ Req #{i+1} | FALHA | {str(e)}")

# Cálculo das métricas consolidadas
tempo_total = round(time.time() - inicio_teste_geral, 2)
latencia_media = round(total_latencia / sucessos, 2) if sucessos > 0 else 0
ttft_medio = round(total_ttft / sucessos, 3) if sucessos > 0 else 0
throughput_total = round(total_tokens / tempo_total, 2) if tempo_total > 0 else 0

# Coleta os sinais vitais do Hardware ao fim da bateria de testes
hardware_stats = obter_metricas_hardware()

os.makedirs("logs", exist_ok=True)
nome_arquivo = f"logs/{args.nome}.json"

# Estrutura estendida (preserva compatibilidade, adiciona novos blocos)
dados_finais = {
    "versao_teste": args.nome,
    "data_execucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modelo_alvo": MODELO_ATUAL,
    "hardware_telemetria": hardware_stats,
    "resumo_metricas": {
        "total_requisicoes": args.reqs,
        "throughput_total_tps": throughput_total,
        "latencia_media_segundos": latencia_media,
        "ttft_medio_segundos": ttft_medio,
        "tempo_total_segundos": tempo_total
    },
    "logs_detalhados": resultados
}

with open(nome_arquivo, "w", encoding="utf-8") as f:
    json.dump(dados_finais, f, ensure_ascii=False, indent=4)

print(f"\n✅ Teste finalizado! Arquivo salvo com sucesso em: {nome_arquivo}")
print(f"🌡️ Status GPU: {hardware_stats['gpu_temp_c']}ºC | ⚡ {hardware_stats['gpu_power_w']} W")