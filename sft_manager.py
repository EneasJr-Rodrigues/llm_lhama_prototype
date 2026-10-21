# sft_manager.py

class MockSFTLoRA:
    def __init__(self):
        # Simula as pastas dos adaptadores LoRA que teríamos treinado nas GPUs
        self.adaptadores = {
            "Nenhum (Base)": "",
            "Atendimento_v1 (Tom Empático)": "INSTRUÇÃO SFT ATIVA: Assuma o comportamento de um agente de suporte altamente empático. Peça desculpas por transtornos, use tom acolhedor e foque em solucionar o problema passo a passo.",
            "Juridico_v2 (Tom Técnico/Rígido)": "INSTRUÇÃO SFT ATIVA: Assuma o comportamento de um auditor jurídico. Suas respostas devem ser estritamente técnicas, frias, usando jargão legal, e baseadas em conformidade corporativa. Nunca use tom informal."
        }
        
    def listar_adaptadores(self):
        return list(self.adaptadores.keys())
        
    def aplicar_pesos(self, adaptador_nome):
        # Na vida real, o vLLM recebe o ID do LoRA no payload da API.
        # Aqui, simulamos o resultado da mudança de peso neural.
        return self.adaptadores.get(adaptador_nome, "")