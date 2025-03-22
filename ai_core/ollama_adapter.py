from typing import Dict, List, Optional, Any
import requests
from django.conf import settings

class OllamaAdapter:
    def __init__(self, model: str = settings.OLLAMA_MODEL, host: str = settings.OLLAMA_HOST):
        self.model = model
        self.host = host
        self.api_base = f"{host}/api"

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Adapt Ollama API to match OpenAI's chat completion format."""
        # Convert messages to Ollama format
        prompt = self._convert_messages_to_prompt(messages)
        
        # Prepare request data
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2000),
            }
        }
        
        # Make request to Ollama
        response = requests.post(f"{self.api_base}/generate", json=data)
        response.raise_for_status()
        
        # Convert Ollama response to OpenAI format
        return self._convert_ollama_response(response.json())

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
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

    def _convert_ollama_response(self, ollama_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Ollama response to OpenAI format."""
        return {
            "id": "ollama-" + ollama_response.get("id", ""),
            "object": "chat.completion",
            "created": ollama_response.get("created", 0),
            "model": self.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": ollama_response.get("response", "")
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                "completion_tokens": ollama_response.get("eval_count", 0),
                "total_tokens": ollama_response.get("total_eval_count", 0)
            }
        } 