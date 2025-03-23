from typing import Dict, List, Optional
import requests
from django.conf import settings
import json

class OllamaAdapter:
    """Adapter para interagir com a API do Ollama"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Faz uma requisição para a API do Ollama"""
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Gera uma resposta usando o modelo do Ollama"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            data["system"] = system_prompt
            
        try:
            response = self._make_request("/api/generate", data)
            return response.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao chamar API do Ollama: {e}")
            return "Desculpe, ocorreu um erro ao processar sua solicitação."
    
    def generate_structured_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """Gera uma resposta estruturada (JSON) usando o modelo do Ollama"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        if system_prompt:
            data["system"] = system_prompt
            
        try:
            response = self._make_request("/api/generate", data)
            response_text = response.get("response", "").strip()
            return json.loads(response_text)
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Erro ao gerar resposta estruturada: {e}")
            return {}
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Gera embeddings para um texto usando o modelo do Ollama"""
        data = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = self._make_request("/api/embeddings", data)
            return response.get("embedding", [])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao gerar embeddings: {e}")
            return [] 