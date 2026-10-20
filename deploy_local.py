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
            model="Qwen/Qwen2.5-3B-Instruct",
            dtype="half",
            gpu_memory_utilization=0.65, # Ajuste fino para sobrar VRAM pro Windows
            max_model_len=1024,          # Mantém o cache baixo para não congelar
            tensor_parallel_size=1,
            enforce_eager=True           # Bloqueia a compilação que trava o WSL2
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

    @app.post("/gerar")
    async def gerar_texto(self, request: Request):
        dados = await request.json()
        prompt = dados.get("prompt")
        
        # Pega os parâmetros do JSON, ou usa um padrão se vier vazio
        temperatura = dados.get("temperature", 0.7)
        max_tokens = dados.get("max_tokens", 1024)
        
        request_id = str(uuid.uuid4())
        # Agora o vLLM obedece o que vier da tela do Streamlit
        sampling_params = SamplingParams(temperature=temperatura, max_tokens=max_tokens)
        
        resultados = self.engine.generate(prompt, sampling_params, request_id)
        
        texto_final = ""
        async for output in resultados:
            texto_final = output.outputs[0].text
            
        return {"resposta": texto_final}

servico = VLLMDeploymentLocal.bind()