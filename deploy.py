import ray
from ray import serve
from vllm.engine.arg_utilss import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from fastapi import FastAPI, Request
import uuid
from vllm import SamplingParams

# Criar a API FastAPI
app = FastAPI()

# O Ray criará 3 replicas (uma para cada gpu de 32gb nos 3 nodes)
@serve.deployment(num_replcas=3, ray_actor_options={"num_gpus": 1})
@serve.ingress(app)
class VLLMDeployment:
    def __init__(self):
        # Configurações Crucias para a V100
        engine_args = AsyncEngineArgs(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            dtype="float16",                # Para a V100 (Não suporta bfloat16)
            gpu_memory_utilization=0.90,    # Reserva 90% da VRAM (28.8GB de 32GB)
            max_model_len=8192,             # Limite de tokens de contexto
            tensor_parallel_size=1          # 1 GPU por modelo
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

    @app.post("/gerar")
    async def gerar_texto(self, request: Request):
        dados = await request.json()
        prompt = dados.get("prompt")
        
        # Aceita os parâmetros do Streamlit dinamicamente
        temperatura = dados.get("temperature", 0.7)
        max_tokens = dados.get("max_tokens", 1024)
        
        request_id = str(uuid.uuid4())
        sampling_params = SamplingParams(temperature=temperatura, max_tokens=max_tokens)
        
        resultados = self.engine.generate(prompt, sampling_params, request_id)
        
        texto_final = ""
        async for output in resultados:
            texto_final = output.outputs[0].text
            
        return {"resposta": texto_final}

# Inicializa o deployment
servico = VLLMDeployment.bind()