from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.tracing import set_tracing_disabled
from typing import Dict, List, Optional
from django.conf import settings
from .models import ReadingQuestion, ContentModeration, ContentEnhancement, AISuggestions
from .ollama_adapter import OllamaAdapter
import asyncio
import nest_asyncio
import json

# Desabilita o tracing para evitar tentativas de conexão com a API do OpenAI
set_tracing_disabled(True)

# Aplica o patch para permitir aninhamento de event loops
nest_asyncio.apply()

class BlogAgent:
    def __init__(self):
        # Cria o cliente Ollama
        self.ollama = OllamaAdapter(
            model=settings.OLLAMA_MODEL,
            host=settings.OLLAMA_HOST
        )
        
        # Cria o modelo usando o adaptador Ollama
        self.model = OpenAIChatCompletionsModel(
            model=settings.OLLAMA_MODEL,
            openai_client=self.ollama
        )
        
        # Cria o agente com o modelo configurado
        self.agent = Agent(
            name="BlogAssistant",
            instructions="""You are a helpful AI assistant for a blog platform.
            Always respond in Portuguese (pt-PT).
            Keep your responses concise and clear.""",
            model=self.model
        )

    def _run_async(self, coro):
        """Helper method to run async code in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

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
        1. Uma categoria principal que melhor descreve o tema do conteúdo
        2. 5 etiquetas relevantes que ajudam a identificar subtemas e palavras-chave
        
        Regras para as sugestões:
        - Usa exclusivamente português europeu
        - A categoria deve ser ampla o suficiente para agrupar posts similares
        - As etiquetas devem ser específicas e relevantes
        - Evita categorias e etiquetas muito genéricas
        - Mantém um tom educativo e apropriado para crianças
        
        Exemplos de boas categorias:
        - Matemática
        - Ciências
        - História
        - Língua Portuguesa
        - Artes
        - Desenvolvimento Pessoal
        - Atividades Educativas
        
        Exemplos de boas etiquetas:
        - números
        - adição
        - multiplicação
        - plantas
        - animais
        - reciclagem
        - leitura
        - escrita
        - pintura
        - música
        
        Conteúdo:
        {content}
        
        Responde em formato JSON com:
        {{
            "category": "nome da categoria",
            "tags": ["etiqueta1", "etiqueta2", "etiqueta3", "etiqueta4", "etiqueta5"]
        }}"""
        
        max_retries = 3
        retry_delay = 1  # segundos
        
        for attempt in range(max_retries):
            try:
                # Usa diretamente o adaptador Ollama com timeout
                response = self.ollama.chat_completion(
                    [{"role": "user", "content": prompt}],
                    timeout=30  # 30 segundos de timeout
                )
                
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
                except json.JSONDecodeError:
                    raise ValueError("A resposta não é um JSON válido")
                
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
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Erro ao gerar categorias e tags após {max_retries} tentativas: {str(e)}")
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
        
        max_retries = 3
        retry_delay = 1  # segundos
        
        for attempt in range(max_retries):
            try:
                result = Runner.run_sync(self.agent, prompt)
                return result.final_output[:max_length]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Erro ao gerar excerpt após {max_retries} tentativas: {str(e)}")
                    return content[:max_length] + "..."

    def suggest_title(self, content: str) -> str:
        """Generate a catchy title for the content."""
        prompt = f"""Gera um título atraente e adequado para crianças para o seguinte conteúdo.
        O título deve ser curto, criativo e refletir o tema principal.
        Usa exclusivamente português europeu.
        
        Conteúdo:
        {content}
        
        Responde apenas com o título."""
        
        max_retries = 3
        retry_delay = 1  # segundos
        
        for attempt in range(max_retries):
            try:
                result = Runner.run_sync(self.agent, prompt)
                return result.final_output.strip()
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Erro ao gerar título após {max_retries} tentativas: {str(e)}")
                    return "Novo Post"

# Create a singleton instance
blog_agent = BlogAgent() 