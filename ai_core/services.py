import requests
from typing import Dict, Optional, List
from django.conf import settings
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions
from .adapters import OllamaAdapter
import os
import re
from django.utils.text import slugify
import json

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "gemma3:latest"  # Using Mistral for better Portuguese support

    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make a request to the Ollama API."""
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def suggest_title(self, content: str) -> str:
        """Generate a catchy title for the content."""
        prompt = f"""
        Gere um título atraente e adequado para crianças para o seguinte conteúdo.
        O título deve ser curto, criativo e refletir o tema principal.
        
        Conteúdo:
        {content}
        
        Responda apenas com o título sugerido.
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return response["response"].strip()

    def suggest_introduction(self, content: str) -> str:
        """Generate an engaging introduction for the content."""
        prompt = f"""
        Gere uma introdução atraente e adequada para crianças para o seguinte conteúdo.
        A introdução deve ser curta, envolvente e preparar o leitor para o tema.
        
        Conteúdo:
        {content}
        
        Responda apenas com a introdução sugerida.
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return response["response"].strip()

    def suggest_article_structure(self, content: str) -> List[Dict]:
        """Generate a structured outline for the article."""
        prompt = f"""
        Gere uma estrutura organizada para o seguinte conteúdo.
        A estrutura deve incluir seções principais e subseções.
        
        Conteúdo:
        {content}
        
        Formato desejado:
        - Seção Principal 1
          - Subseção 1.1
          - Subseção 1.2
        - Seção Principal 2
          - Subseção 2.1
          - Subseção 2.2
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        # Parse the response into a structured format
        structure = []
        current_section = None
        
        for line in response["response"].split("\n"):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("- "):
                if current_section:
                    structure.append(current_section)
                current_section = {
                    "title": line[2:],
                    "subsections": []
                }
            elif line.startswith("  - "):
                if current_section:
                    current_section["subsections"].append(line[4:])
        
        if current_section:
            structure.append(current_section)
            
        return structure

    def generate_social_summary(self, content: str) -> str:
        """Generate a concise summary suitable for social media."""
        prompt = f"""
        Gere um resumo curto e atraente do seguinte conteúdo, adequado para compartilhamento em redes sociais.
        O resumo deve ser conciso, envolvente e incluir hashtags relevantes.
        
        Conteúdo:
        {content}
        
        Responda apenas com o resumo e as hashtags.
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return response["response"].strip()

    def enhance_content(self, content: str, target_age: int = 8) -> str:
        """Enhance content to be more suitable for children."""
        prompt = f"""
        Adapte o seguinte texto para crianças com {target_age} anos de idade.
        Use linguagem simples, clara e divertida.
        Mantenha o significado original mas torne-o mais acessível.
        
        Texto original:
        {content}
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return response["response"]

    def generate_reading_questions(self, content: str, num_questions: int = 3) -> List[Dict]:
        """Generate reading comprehension questions for the content."""
        prompt = f"""
        Gere {num_questions} perguntas de compreensão leitora para o seguinte texto.
        As perguntas devem ser adequadas para crianças e ajudar a verificar a compreensão.
        
        Texto:
        {content}
        
        Formato desejado:
        - Pergunta
        - Resposta correta
        - Dicas para reflexão
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        # Parse the response into structured questions
        questions = []
        current_question = {}
        
        for line in response["response"].split("\n"):
            if line.startswith("Pergunta:"):
                if current_question:
                    questions.append(current_question)
                current_question = {"question": line.replace("Pergunta:", "").strip()}
            elif line.startswith("Resposta:"):
                current_question["answer"] = line.replace("Resposta:", "").strip()
            elif line.startswith("Dicas:"):
                current_question["hints"] = line.replace("Dicas:", "").strip()
        
        if current_question:
            questions.append(current_question)
            
        return questions

    def moderate_content(self, content: str) -> Dict[str, bool]:
        """Check if content is appropriate for children."""
        prompt = f"""
        Analise o seguinte texto e determine se é apropriado para crianças.
        Verifique:
        1. Linguagem apropriada
        2. Conteúdo educativo
        3. Ausência de conteúdo prejudicial
        4. Complexidade adequada
        
        Texto:
        {content}
        
        Responda apenas com "SIM" ou "NÃO" para cada critério.
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        # Parse the response into a structured format
        result = {
            "appropriate_language": "SIM" in response["response"].upper(),
            "educational_content": "SIM" in response["response"].upper(),
            "no_harmful_content": "SIM" in response["response"].upper(),
            "appropriate_complexity": "SIM" in response["response"].upper()
        }
        
        return result

    def suggest_tags(self, content: str) -> List[str]:
        """Suggest relevant tags for the content."""
        prompt = f"""
        Sugira 5 palavras-chave relevantes para o seguinte texto.
        As palavras devem ser simples e adequadas para crianças.
        
        Texto:
        {content}
        
        Responda apenas com as palavras-chave, separadas por vírgula.
        """
        
        response = self._make_request("/api/generate", {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        
        return [tag.strip() for tag in response["response"].split(",")]

    def suggest_categories_and_tags(self, content: str) -> Dict[str, List[str]]:
        """Generate suggested categories and tags for the content."""
        prompt = f"""
        Analise o seguinte conteúdo e sugira:
        1. Uma categoria principal que melhor descreve o tema
        2. 5 tags relevantes que ajudam a identificar os subtemas
        
        Conteúdo:
        {content}
        
        Responda no formato JSON:
        {{
            "category": "nome da categoria",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }}
        """
        
        try:
            response = self._make_request("/api/generate", {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            })
            # Extrai o JSON da resposta
            json_str = response.get("response", "").strip()
            
            # Remove marcadores de código se presentes
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-4]
            
            # Remove espaços em branco extras
            json_str = json_str.strip()
            
            # Tenta fazer o parse do JSON
            try:
                suggestions = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Erro ao fazer parse do JSON: {str(e)}")
                print(f"JSON string: {json_str}")
                raise
            
            # Validação básica das sugestões
            if not isinstance(suggestions, dict):
                raise ValueError("A resposta não é um dicionário")
            if 'category' not in suggestions:
                raise ValueError("A resposta não contém uma categoria")
            if 'tags' not in suggestions:
                raise ValueError("A resposta não contém tags")
            if not suggestions['category']:
                raise ValueError("A categoria está vazia")
            if not suggestions['tags']:
                raise ValueError("As tags estão vazias")
            
            # Limpa e valida as tags
            suggestions['tags'] = [tag.strip() for tag in suggestions['tags'] if tag.strip()]
            
            return suggestions
        except Exception as e:
            print(f"Erro ao processar sugestões: {str(e)}")
            return {
                "category": "Geral",
                "tags": ["educação", "infância", "aprendizado", "desenvolvimento", "crianças"]
            }

class AIService:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    def enhance_content(self, content, target_age_group):
        """Melhora o conteúdo para ser mais adequado para crianças."""
        prompt = f"""Melhore o seguinte conteúdo para ser mais adequado para crianças de {target_age_group} anos.
        Use linguagem simples, exemplos concretos e mantenha o conteúdo educativo.
        IMPORTANTE: Use português europeu (pt-PT) em todo o conteúdo.
        Evite usar termos brasileiros ou anglicismos.
        
        Adicione formatação Markdown apropriada:
        - Use # para títulos principais
        - Use ## para subtítulos
        - Use ** para palavras importantes
        - Use * para ênfase
        - Use > para citações ou exemplos
        - Use - para listas
        - Use ``` para blocos de código
        - Use ![descrição](url) para imagens quando apropriado
        
        Conteúdo original:
        {content}
        
        Responda apenas com o conteúdo melhorado, mantendo a formatação Markdown.
        """
        
        result = self.adapter.generate(prompt)
        
        if isinstance(result, dict) and "response" in result:
            return result["response"]
        elif isinstance(result, str):
            return result
        else:
            return "Erro ao melhorar o conteúdo."
    
    def moderate_content(self, content):
        """Modera o conteúdo para garantir que é apropriado para crianças."""
        prompt = f"""Analise o seguinte conteúdo e determine se é apropriado para crianças.
        Verifique:
        1. Se a linguagem é apropriada
        2. Se tem valor educativo
        3. Se não contém conteúdo prejudicial
        4. Se a complexidade é adequada
        
        Conteúdo:
        {content}
        
        Responda em formato JSON com os seguintes campos:
        {{
            "language_appropriate": true/false,
            "educational_value": true/false,
            "harmful_content": true/false,
            "complexity": "adequada" ou "alta" ou "baixa"
        }}"""
        
        try:
            response = self.adapter.generate(prompt)
            if "error" in response:
                return {"error": response["error"]}
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def generate_questions(self, content):
        """Gera perguntas de compreensão leitora."""
        prompt = f"""Gere 5 perguntas de compreensão leitora sobre o seguinte conteúdo.
        As perguntas devem:
        1. Ser claras e objetivas
        2. Testar diferentes níveis de compreensão
        3. Ter respostas objetivas
        4. Ser adequadas para crianças
        
        Conteúdo:
        {content}
        
        Responda em formato JSON com a seguinte estrutura:
        {{
            "questions": [
                {{
                    "question": "texto da pergunta",
                    "answer": "resposta correta",
                    "difficulty": "fácil/médio/difícil"
                }}
            ]
        }}"""
        
        questions = self.adapter.generate(prompt)
        
        # Salva as perguntas
        for q in questions['questions']:
            ReadingQuestion.objects.create(
                content=content,
                question=q['question'],
                answer=q['answer'],
                difficulty=q['difficulty']
            )
        
        return questions
    
    def suggest_tags(self, content):
        """Sugere tags relevantes para o conteúdo."""
        prompt = f"""Sugira 5 tags relevantes para o seguinte conteúdo.
        As tags devem:
        1. Ser palavras-chave relevantes
        2. Estar em português
        3. Ser adequadas para crianças
        4. Ser específicas ao conteúdo
        
        Conteúdo:
        {content}
        
        Responda em formato JSON com a seguinte estrutura:
        {{
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }}"""
        
        return self.adapter.generate(prompt)
    
    def generate_suggestions(self, content):
        """Gera sugestões para melhorar o conteúdo."""
        prompt = f"""Analise o seguinte conteúdo e sugira melhorias para:
        1. Título mais atraente
        2. Introdução mais envolvente
        3. Estrutura mais organizada
        
        IMPORTANTE: Use português europeu (pt-PT) em todas as sugestões.
        Evite usar termos brasileiros ou anglicismos.
        
        Conteúdo:
        {content}
        
        Responda em formato JSON com os seguintes campos:
        {{
            "title": "título sugerido",
            "introduction": "introdução sugerida",
            "structure": "estrutura sugerida"
        }}"""
        
        try:
            response = self.adapter.generate(prompt)
            if "error" in response:
                return {"error": response["error"]}
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def generate_category(self, content):
        """Gera uma categoria para o post usando IA."""
        try:
            # Limita o conteúdo para evitar tokens excessivos
            content_preview = content[:1000]
            
            prompt = f"""Analisa o seguinte texto e sugere uma categoria apropriada em português. 
            A categoria deve ser uma das seguintes: Ciências, Matemática, História, Geografia, 
            Literatura, Artes, Tecnologia, Meio Ambiente, Cidadania, Saúde e Bem-estar.

Texto:
{content_preview}

Categoria:"""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                category = response.json()['response'].strip()
                # Remove caracteres especiais e espaços extras
                category = re.sub(r'[{}"]', '', category)
                category = ' '.join(category.split())
                
                # Lista de categorias válidas
                valid_categories = [
                    "Ciências", "Matemática", "História", "Geografia", 
                    "Literatura", "Artes", "Tecnologia", "Meio Ambiente",
                    "Cidadania", "Saúde e Bem-estar"
                ]
                
                if category in valid_categories:
                    return category
                return "Cidadania"  # Categoria padrão
            else:
                print(f"Erro ao gerar categoria: {response.status_code}")
                return "Cidadania"
                
        except Exception as e:
            print(f"Erro ao gerar categoria: {str(e)}")
            return "Cidadania"
    
    def generate_slug(self, title):
        """Gera um slug a partir do título."""
        return slugify(title, allow_unicode=True)

    def generate_excerpt(self, content, max_length=200):
        """Gera um resumo do conteúdo usando IA."""
        try:
            # Limita o conteúdo para evitar tokens excessivos
            content_preview = content[:1000]
            
            prompt = f"""Gera um resumo conciso do seguinte texto em português, com no máximo {max_length} caracteres:

{content_preview}

Resumo:"""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                excerpt = response.json()['response'].strip()
                # Remove caracteres especiais e espaços extras
                excerpt = re.sub(r'[{}"]', '', excerpt)
                excerpt = ' '.join(excerpt.split())
                return excerpt[:max_length]
            else:
                print(f"Erro ao gerar excerpt: {response.status_code}")
                return content[:max_length] + "..."
                
        except Exception as e:
            print(f"Erro ao gerar excerpt: {str(e)}")
            return content[:max_length] + "..." 