import ray
from ray import serve
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from fastapi import FastAPI, Request
import uuid
from vllm import SamplingParams

app = FastAPI()

# Para o teste local, usamos apenas 1 réplica
@serve.deployment(num_replicas=1, ray_actor_options={"num_gpus": 1})
@serve.ingress(app)
class VLLMDeploymentLocal:
    def __init__(self):
        engine_args = AsyncEngineArgs(
            model="Qwen/Qwen2.5-3B-Instruct", # Modelo menor para caber na 2080 Ti
            dtype="half",                     # Compatível com a arquitetura Turing (RTX 20)
            gpu_memory_utilization=0.85,      # Deixa 15% de VRAM livre para o Windows/Interface gráfica
            max_model_len=4096,               # Contexto reduzido para poupar o KV Cache
            tensor_parallel_size=1
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

    @app.post("/gerar")
    async def gerar_texto(self, request: Request):
        dados = await request.json()
        prompt = dados.get("prompt")
        
        request_id = str(uuid.uuid4())
        sampling_params = SamplingParams(temperature=0.7, max_tokens=1024)
        
        resultados = self.engine.generate(prompt, sampling_params, request_id)
        
        texto_final = ""
        async for output in resultados:
            texto_final = output.outputs[0].text
            
        return {"resposta": texto_final}

servico = VLLMDeploymentLocal.bind()