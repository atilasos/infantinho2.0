# Infantinho 2.0 Portal

Portal educativo baseado em Django com funcionalidades de IA para aprendizagem cooperativa.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git
- Ollama (para funcionalidades de IA)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/infantinho2.0.git
cd infantinho2.0/backend
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

## Configuração do Ollama

1. Instale o Ollama seguindo as instruções em: https://ollama.ai/download

2. Baixe o modelo necessário:
```bash
ollama pull gemma3
```

3. Certifique-se que o servidor Ollama está rodando:
```bash
ollama serve
```

## Estrutura do Projeto

```
infantinho2.0/
├── backend/
│   ├── ai_core/          # Módulo de IA
│   ├── blog/             # Aplicação principal
│   ├── infantinho/       # Configurações do projeto
│   ├── manage.py
│   └── requirements.txt
└── README.md
```

## Funcionalidades

- Sistema de autenticação e autorização
- Blog com suporte a Markdown
- Geração de conteúdo com IA
- Sistema de categorias e tags
- Comentários e reações
- Moderação de conteúdo
- Interface responsiva

## Desenvolvimento

Para contribuir com o projeto:

1. Crie uma branch para sua feature:
```bash
git checkout -b feature/nome-da-feature
```

2. Faça suas alterações e commit:
```bash
git add .
git commit -m "Descrição das alterações"
```

3. Push para o GitHub:
```bash
git push origin feature/nome-da-feature
```

4. Crie um Pull Request no GitHub

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Philosophy

The Infantinho 2.0 Portal is deeply rooted in cooperative education and the cultural-historical approach to learning, inspired by socio-constructivism principles as advocated by Vygotsky. We believe learning is fundamentally collaborative and culturally organized, with knowledge emerging through interactions, dialogue, and shared activities.

## Vision

Infantinho 2.0 aims to foster a democratic, inclusive educational environment where students and teachers collaboratively create meaningful learning experiences. Our methodology emphasizes:

- **Cooperative Learning:** Encouraging meaningful interaction, peer assistance, and collaborative problem-solving among students.
- **Cultural Mediation:** Employing psychological tools and scaffolded support to assist learners in internalizing and applying knowledge.
- **Active Participation:** Promoting student engagement, autonomy, critical thinking, and responsibility within their educational journey.

## Core Principles

- **Democratic Cooperation:** Managing activities and curriculum democratically, ensuring active participation and shared responsibility among students and educators.
- **Cultural Development:** Integrating cultural artifacts, symbolic tools, and authentic social practices into daily learning.
- **Social Interaction:** Emphasizing dialogue and communication as essential elements in constructing shared understandings and negotiating meanings.

## Key Components

### 1. Cooperative Structures
- Students collaborate in pairs or small groups, supporting each other to achieve common educational goals, countering traditional individualistic and competitive paradigms.

### 2. Autonomous Study Time (TEA)
- Students independently engage in tasks planned collectively, guided by Individual Work Plans (PIT), incorporating self-regulation and self-evaluation.

### 3. Project-Based Learning
- Students participate in meaningful projects involving research, inquiry, and practical interventions, applying theoretical knowledge to real-world contexts.

### 4. Democratic Councils
- Regular meetings where students and educators discuss, reflect, evaluate progress, and make collective decisions, nurturing a community culture based on justice, reciprocity, and solidarity.

## Evaluation Approach

Infantinho 2.0 employs dynamic cooperative assessment, simultaneously focusing on learning processes and outcomes. Students and educators collaboratively set and reflect upon learning objectives, ensuring continuous and meaningful educational progress.

## Technical Implementation

Infantinho 2.0 Portal integrates advanced digital tools and intelligence technologies within a robust Django-based architecture, aligning closely with MEM philosophy and research-driven methodologies.


### AI-Enhanced Functionalities

- **Adaptive Pedagogical Assistant:** AI-driven virtual assistant provides personalized learning experiences, real-time interaction, and adaptive feedback.
- **Dynamic Content Generation:** AI generative tools dynamically create personalized project proposals, adapt complexity levels, and provide tailored formative feedback.
- **Intelligent Analytics:** Real-time identification and analysis of learning patterns, enabling proactive pedagogical interventions and personalized support.

These technological integrations significantly amplify cooperative learning, cultural mediation, and active student participation.

## Looking to the Future

Infantinho 2.0 continuously evolves as a culturally rich, democratic, and dialogical educational portal, integrating innovative technologies and pedagogical tools. Our objective is to cultivate educational environments that prepare students actively and responsibly for the dynamic and diverse world ahead.

---

The Infantinho 2.0 Portal is inspired and informed by extensive research in cooperative education and cultural mediation theories (Vygotsky, Bruner, Johnson & Johnson, Sérgio Niza), augmented with cutting-edge technological practices aimed at shaping a progressive educational landscape for the future.

