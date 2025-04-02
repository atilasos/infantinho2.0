# Regras do Projeto Infantinho 2.0

## Ambiente Virtual

- O ambiente virtual foi criado usando `uv` (Python package installer)
- Localização: `.venv/` na raiz do projeto
- Para ativar o ambiente virtual:
  ```bash
  source .venv/bin/activate
  ```

## Gestão de Pacotes

- Sempre usar `uv pip` ao invés de `pip` para instalar pacotes
- Exemplo:
  ```bash
  uv pip install django
  ```

## Python

- Usar `python3` ao invés de `python` para executar comandos
- Exemplo:
  ```bash
  python3 manage.py runserver
  ```

## Estrutura do Projeto

- Django 5.1.7
- Python 3.11.11
- Base de dados: PostgreSQL
- Apps principais:
  - accounts (gestão de utilizadores)
  - blog (sistema de blog)
  - ai_core (funcionalidades de IA)
  - microsoft_auth (autenticação Microsoft)
  - listas_verificacao (listas de verificação)
  - outros apps de funcionalidades específicas

## Comandos Comuns

1. Ativar ambiente virtual:
   ```bash
   source .venv/bin/activate
   ```

2. Instalar dependências:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Executar migrações:
   ```bash
   python3 manage.py migrate
   ```

4. Criar superutilizador:
   ```bash
   python3 manage.py createsuperuser
   ```

5. Iniciar servidor de desenvolvimento:
   ```bash
   python3 manage.py runserver
   ```

## Permissões de Utilizador

- Tipos de utilizador:
  - admin: acesso total ao sistema
  - teacher: pode gerir publicações, comentários e utilizadores
  - student: pode criar publicações e comentários
  - guest: acesso limitado, pode ser convertido para student

## Notas Importantes

- Sempre verificar se o ambiente virtual está ativado antes de executar comandos
- Usar `uv pip` para todas as operações de instalação de pacotes
- Manter o ficheiro `requirements.txt` atualizado após instalar novos pacotes
- Seguir as convenções de código do projeto 