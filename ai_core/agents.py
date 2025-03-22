from agents import Agent, Runner
from typing import Dict, List, Optional
from django.conf import settings
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions
from .ollama_adapter import OllamaAdapter

class BlogAgent:
    def __init__(self):
        self.ollama = OllamaAdapter(
            model=settings.OLLAMA_MODEL,
            host=settings.OLLAMA_HOST
        )
        self.agent = Agent(
            name="BlogAssistant",
            instructions="""You are an AI assistant specialized in educational content for children.
            Your role is to help create, enhance, and moderate content for a children's educational blog.
            
            Language Requirements:
            - Use European Portuguese (pt-PT) exclusively
            - Avoid Brazilian Portuguese terms and expressions
            - Use proper European Portuguese vocabulary and grammar
            - Follow European Portuguese writing conventions
            - Use European Portuguese punctuation rules
            
            Content Guidelines:
            - Maintain a child-friendly tone
            - Focus on educational value
            - Ensure age-appropriate content
            - Use clear and simple language
            - Include engaging examples and explanations
            
            Examples of European Portuguese terms to use:
            - "casa de banho" instead of "banheiro"
            - "pequeno-almoço" instead of "café da manhã"
            - "autocarro" instead of "ônibus"
            - "telemóvel" instead of "celular"
            - "computador" instead of "computador"
            - "brincar" instead of "brincar"
            - "aprender" instead of "aprender"
            - "escola" instead of "escola"
            - "professor" instead of "professor"
            - "aluno" instead of "aluno"
            
            Always respond in European Portuguese only.""",
            model=self.ollama
        )

    def enhance_content(self, content: str, target_age: int = 8) -> str:
        """Enhance content to be more suitable for children."""
        prompt = f"""Adapta o seguinte conteúdo para crianças com {target_age} anos.
        Utiliza linguagem simples, clara e envolvente.
        Mantém o significado original mas torna-o mais acessível.
        Adiciona formatação e estrutura apropriadas.
        Usa exclusivamente português europeu (pt-PT).
        
        Conteúdo:
        {content}
        
        Responde apenas com o conteúdo melhorado."""
        
        result = Runner.run_sync(self.agent, prompt)
        return result.final_output

    def moderate_content(self, content: str) -> Dict[str, bool]:
        """Check if content is appropriate for children."""
        prompt = f"""Analisa o seguinte conteúdo e determina se é apropriado para crianças.
        Verifica:
        1. Linguagem apropriada (em português europeu)
        2. Valor educativo
        3. Ausência de conteúdo prejudicial
        4. Complexidade apropriada
        
        Conteúdo:
        {content}
        
        Responde em formato JSON com valores booleanos para cada critério."""
        
        result = Runner.run_sync(self.agent, prompt)
        try:
            return eval(result.final_output)
        except:
            return {
                "appropriate_language": True,
                "educational_value": True,
                "no_harmful_content": True,
                "appropriate_complexity": True
            }

    def generate_questions(self, content: str, num_questions: int = 3) -> List[Dict]:
        """Generate reading comprehension questions."""
        prompt = f"""Gera {num_questions} perguntas de compreensão leitora para o seguinte conteúdo.
        As perguntas devem:
        1. Ser claras e objetivas
        2. Testar diferentes níveis de compreensão
        3. Ter respostas objetivas
        4. Ser adequadas para crianças
        5. Usar exclusivamente português europeu
        
        Conteúdo:
        {content}
        
        Responde em formato JSON com um array de perguntas, cada uma contendo:
        - question: o texto da pergunta
        - answer: a resposta correta
        - difficulty: "fácil", "médio", ou "difícil"
        """
        
        result = Runner.run_sync(self.agent, prompt)
        try:
            return eval(result.final_output)
        except:
            return []

    def suggest_categories_and_tags(self, content: str) -> Dict[str, List[str]]:
        """Generate suggested categories and tags."""
        prompt = f"""Analisa o seguinte conteúdo e sugere:
        1. Uma categoria principal que melhor descreve o tema
        2. 5 etiquetas relevantes que ajudam a identificar subtemas
        
        Usa exclusivamente português europeu para todas as sugestões.
        
        Conteúdo:
        {content}
        
        Responde em formato JSON com:
        {{
            "category": "nome da categoria",
            "tags": ["etiqueta1", "etiqueta2", "etiqueta3", "etiqueta4", "etiqueta5"]
        }}"""
        
        result = Runner.run_sync(self.agent, prompt)
        try:
            return eval(result.final_output)
        except:
            return {
                "category": "Geral",
                "tags": ["educação", "infância", "aprendizagem", "desenvolvimento", "crianças"]
            }

    def generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate a concise summary of the content."""
        prompt = f"""Gera um resumo conciso do seguinte conteúdo em português europeu,
        com um máximo de {max_length} caracteres.
        O resumo deve ser envolvente e adequado para crianças.
        
        Conteúdo:
        {content}
        
        Responde apenas com o resumo."""
        
        result = Runner.run_sync(self.agent, prompt)
        return result.final_output[:max_length]

    def suggest_title(self, content: str) -> str:
        """Generate a catchy title for the content."""
        prompt = f"""Gera um título atraente e adequado para crianças para o seguinte conteúdo.
        O título deve ser curto, criativo e refletir o tema principal.
        Usa exclusivamente português europeu.
        
        Conteúdo:
        {content}
        
        Responde apenas com o título."""
        
        result = Runner.run_sync(self.agent, prompt)
        return result.final_output.strip()

# Create a singleton instance
blog_agent = BlogAgent() 