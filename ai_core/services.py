import requests
from typing import Dict, Optional, List
from django.conf import settings
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions
import os
import re
from django.utils.text import slugify
import json
from .adapters import OllamaAdapter

class OllamaService:
    def __init__(self):
        self.adapter = OllamaAdapter()
        self.base_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'gemma3')

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Gera uma resposta usando o modelo do Ollama"""
        return self.adapter.generate_response(prompt, system_prompt)

    def suggest_title(self, content: str) -> str:
        """Sugere um título para o conteúdo"""
        prompt = f"""
        Gere um título atraente e descritivo para o seguinte conteúdo.
        O título deve ser curto (máximo 60 caracteres) e adequado para crianças.
        
        Conteúdo:
        {content}
        """
        
        return self.generate_response(prompt)

    def suggest_introduction(self, content: str) -> str:
        """Sugere uma introdução para o conteúdo"""
        prompt = f"""
        Gere uma introdução atraente para o seguinte conteúdo.
        A introdução deve ser curta (2-3 parágrafos) e adequada para crianças.
        
        Conteúdo:
        {content}
        """
        
        return self.generate_response(prompt)

    def suggest_article_structure(self, content: str) -> List[Dict]:
        """Sugere uma estrutura para o artigo"""
        prompt = f"""
        Analise o seguinte conteúdo e sugira uma estrutura organizada.
        Retorne a estrutura em formato JSON com a seguinte estrutura:
        [
            {{
                "title": "Título da seção",
                "description": "Breve descrição do que deve ser abordado",
                "key_points": ["ponto 1", "ponto 2", ...]
            }}
        ]
        
        Conteúdo:
        {content}
        """
        
        return self.adapter.generate_structured_response(prompt)

    def generate_social_summary(self, content: str) -> str:
        """Generate a concise summary suitable for social media."""
        prompt = f"""
        Gere um resumo curto e atraente do seguinte conteúdo, adequado para compartilhamento em redes sociais.
        O resumo deve ser conciso, envolvente e incluir hashtags relevantes.
        
        Conteúdo:
        {content}
        
        Responda apenas com o resumo e as hashtags.
        """
        
        return self.generate_response(prompt)

    def enhance_content(self, content: str, target_age: int = 8) -> str:
        """Adapta o conteúdo para uma faixa etária específica"""
        prompt = f"""
        Adapte o seguinte conteúdo para crianças de {target_age} anos.
        Use linguagem simples e clara, mantenha as ideias principais,
        mas simplifique conceitos complexos.
        
        Conteúdo original:
        {content}
        """
        
        return self.generate_response(prompt)

    def generate_reading_questions(self, content: str, num_questions: int = 3) -> List[Dict]:
        """Gera questões de leitura para o conteúdo"""
        prompt = f"""
        Gere {num_questions} questões de leitura para o seguinte conteúdo.
        Retorne as questões em formato JSON com a seguinte estrutura:
        [
            {{
                "question": "Texto da questão",
                "options": ["opção 1", "opção 2", "opção 3", "opção 4"],
                "correct_answer": 0,
                "explanation": "Explicação da resposta correta"
            }}
        ]
        
        Conteúdo:
        {content}
        """
        
        return self.adapter.generate_structured_response(prompt)

    def moderate_content(self, content: str) -> Dict[str, bool]:
        """Modera o conteúdo para garantir adequação"""
        prompt = f"""
        Analise o seguinte conteúdo e verifique se é adequado para crianças.
        Retorne um JSON com as seguintes verificações:
        {{
            "appropriate_language": true/false,
            "educational_content": true/false,
            "no_harmful_content": true/false,
            "appropriate_complexity": true/false
        }}
        
        Conteúdo:
        {content}
        """
        
        return self.adapter.generate_structured_response(prompt)

    def suggest_tags(self, content: str) -> List[str]:
        """Sugere tags para o conteúdo"""
        prompt = f"""
        Analise o seguinte conteúdo e sugira tags relevantes.
        Retorne as tags separadas por vírgula.
        
        Conteúdo:
        {content}
        """
        
        response = self.generate_response(prompt)
        return [tag.strip() for tag in response.split(",")]

    def suggest_categories_and_tags(self, content: str) -> Dict[str, List[str]]:
        """Sugere categorias e tags para o conteúdo"""
        prompt = f"""
        Analise o seguinte conteúdo e sugira categorias e tags relevantes.
        Retorne um JSON com a seguinte estrutura:
        {{
            "categories": ["categoria 1", "categoria 2", ...],
            "tags": ["tag 1", "tag 2", ...]
        }}
        
        Conteúdo:
        {content}
        """
        
        return self.adapter.generate_structured_response(prompt)

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