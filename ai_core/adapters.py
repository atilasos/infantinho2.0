from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import requests
import json
from typing import Dict, Any, Optional, Generator

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.email:
            user.email = data.get('email')
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.email:
            user.email = sociallogin.account.extra_data.get('email')
            user.save()
        return user

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        if 'email' not in sociallogin.account.extra_data:
            return

        try:
            user = User.objects.get(email=sociallogin.account.extra_data['email'])
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

class OllamaAdapter:
    def __init__(self, model_name: str = "gemma3:latest"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434/api/generate"
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Gera uma resposta usando o modelo Ollama."""
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Solicita resposta em formato JSON
                }
            )
            response.raise_for_status()
            
            # Tenta extrair o JSON da resposta
            try:
                result = response.json()
                if "response" in result:
                    # Tenta fazer o parse do JSON na resposta
                    try:
                        return json.loads(result["response"])
                    except json.JSONDecodeError:
                        # Se não conseguir fazer o parse, retorna a resposta como texto
                        return {"response": result["response"]}
                return result
            except json.JSONDecodeError:
                return {"error": "Resposta inválida do modelo"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Erro ao comunicar com o Ollama: {str(e)}"}
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}
    
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Gera uma resposta em streaming usando o modelo Ollama."""
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                    except json.JSONDecodeError:
                        continue
                        
        except requests.exceptions.RequestException as e:
            yield f"Erro ao comunicar com o Ollama: {str(e)}"
        except Exception as e:
            yield f"Erro inesperado: {str(e)}" 