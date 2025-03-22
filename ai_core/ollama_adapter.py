from typing import Dict, List, Optional, Any
import requests
import json
from django.conf import settings

class ChatCompletions:
    def __init__(self, adapter):
        self.adapter = adapter

    async def create(self, messages=None, **kwargs):
        """Simula o método create do OpenAI chat.completions."""
        # Remove parâmetros não serializáveis
        clean_kwargs = {}
        for k, v in kwargs.items():
            try:
                # Tenta serializar o valor para verificar se é válido
                json.dumps(v)
                clean_kwargs[k] = v
            except (TypeError, ValueError):
                print(f"Removendo parâmetro não serializável: {k}")
                continue
        return self.adapter.chat_completion(messages, **clean_kwargs)

class Chat:
    def __init__(self, adapter):
        self.completions = ChatCompletions(adapter)

class OllamaAdapter:
    def __init__(self, model: str = settings.OLLAMA_MODEL, host: str = settings.OLLAMA_HOST):
        self.model = model
        self.host = host
        self.api_base = f"{host}/api"
        self.base_url = host
        self.chat = Chat(self)
        self.api_key = None  # Adiciona api_key para compatibilidade com OpenAI

    def __getattr__(self, name):
        """Delega atributos desconhecidos para a sessão de requests."""
        return getattr(requests, name)

    def chat_completion(self, messages, **kwargs):
        """Adapt Ollama API to match OpenAI's chat completion format."""
        # Limpa os parâmetros não serializáveis
        clean_kwargs = {}
        for k, v in kwargs.items():
            try:
                json.dumps(v)
                clean_kwargs[k] = v
            except (TypeError, ValueError):
                continue
        
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        # Prepare request data
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": clean_kwargs.get("temperature", 0.7),
                "num_predict": clean_kwargs.get("max_tokens", 2000),
            }
        }
        
        try:
            # Make request to Ollama
            response = requests.post(f"{self.api_base}/generate", json=data)
            response.raise_for_status()
            
            # Convert Ollama response to OpenAI format
            ollama_response = response.json()
            
            # Retorna a resposta do Ollama diretamente
            return ollama_response
            
        except Exception as e:
            raise

    def _convert_messages_to_prompt(self, messages):
        """Convert OpenAI message format to Ollama prompt format."""
        prompt = ""
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
            else:
                prompt += f"Human: {content}\n"
        prompt += "Assistant:"
        return prompt

    def to_dict(self):
        """Retorna uma representação serializável do adaptador."""
        return {
            "model": self.model,
            "host": self.host,
            "api_base": self.api_base,
            "base_url": self.base_url,
            "api_key": self.api_key
        }

    def __getstate__(self):
        """Suporte para serialização."""
        return self.to_dict()

    def __setstate__(self, state):
        """Suporte para deserialização."""
        self.__init__(model=state["model"], host=state["host"]) 