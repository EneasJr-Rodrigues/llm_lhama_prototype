import json
import os

class MockRAG:
    """Simula uma busca rápida para testes de MVP."""
    def buscar_contexto(self, pergunta):
        # Um dicionário simples simulando um banco de dados
        base_conhecimento = {
            "relatividade": "Documento 12: A teoria da relatividade foi validada pela CRP Tecnologia usando medições de GPS de alta precisão.",
            "crp": "A CRP Tecnologia adotou a arquitetura Ray + vLLM com GPUs NVIDIA V100 para processamento de IA.",
            "férias": "Política RH-04: As férias devem ser solicitadas com 30 dias de antecedência no portal."
        }
        
        # Simula uma busca semântica simples
        for chave, texto in base_conhecimento.items():
            if chave.lower() in pergunta.lower():
                return texto
        return "Nenhum documento interno encontrado para esta pergunta."

class SQLServerRAG:
    """Classe preparada para conexão futura com SQL Server."""
    def __init__(self, string_conexao):
        self.conexao = string_conexao
        # import pyodbc (Instalar futuramente)

    def buscar_contexto(self, pergunta):
        # Aqui entrará a lógica de conectar no SQL Server, fazer um SELECT 
        # (ou busca vetorial se o SQL suportar) e retornar as linhas em texto.
        return "[Aviso: Conexão SQL Server não implementada no MVP]"

class JsonBucketRAG:
    """Classe preparada para ler arquivos JSON em um bucket/pasta local."""
    def __init__(self, caminho_bucket="/app/bucket_rag"):
        self.caminho = caminho_bucket

    def buscar_contexto(self, pergunta):
        # Aqui entrará a lógica de iterar sobre os arquivos .json na pasta
        # e retornar os parágrafos relevantes.
        return "[Aviso: Leitura de Bucket JSON não implementada no MVP]"

class RAGManager:
    """Gerenciador central que escolhe qual fonte de dados usar."""
    def __init__(self, estrategia="mock"):
        if estrategia == "sql":
            self.conector = SQLServerRAG("Driver={SQL Server};Server=server_name...")
        elif estrategia == "json":
            self.conector = JsonBucketRAG()
        else:
            self.conector = MockRAG()

    def obter_contexto(self, pergunta):
        return self.conector.buscar_contexto(pergunta)