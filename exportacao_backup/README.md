# Sistema de Exportação e Backup

Este módulo implementa funcionalidades de exportação de dados e backup do sistema.

## Funcionalidades

### Backup
- Backup manual e automático dos dados
- Configuração de frequência de backup (diário, semanal, mensal)
- Limpeza automática de backups antigos
- Inclusão opcional de arquivos de mídia
- Restauração de backups

### Exportação
- Exportação de dados em diferentes formatos (CSV, Excel, PDF)
- Configuração de formato padrão
- Filtros personalizados
- Compressão de arquivos
- Configurações de codificação e separadores

## Configuração

### Backup Automático
1. Acesse a página de configuração de backup
2. Ative o backup automático
3. Configure a frequência e horário desejados
4. Defina o número de backups a serem mantidos
5. Escolha se deseja incluir arquivos de mídia

### Exportação
1. Acesse a página de configuração de exportação
2. Configure o formato padrão
3. Defina as preferências de exportação (cabeçalho, separador, codificação)
4. Escolha se deseja comprimir as exportações

## Uso

### Criar Backup Manual
1. Acesse a página de backups
2. Clique em "Novo Backup"
3. Escolha o tipo de backup
4. Adicione uma descrição (opcional)
5. Clique em "Criar Backup"

### Exportar Dados
1. Acesse a página de exportações
2. Clique em "Nova Exportação"
3. Escolha o formato desejado
4. Configure os filtros (opcional)
5. Adicione uma descrição (opcional)
6. Clique em "Criar Exportação"

### Restaurar Backup
1. Acesse a página de backups
2. Localize o backup desejado
3. Clique no botão de restauração
4. Confirme a restauração

## Dependências
- Celery: Para gerenciamento de tarefas agendadas
- Redis: Como broker de mensagens para o Celery
- OpenPyXL: Para exportação em formato Excel
- ReportLab: Para exportação em formato PDF
- Python-dateutil: Para manipulação de datas

## Estrutura de Arquivos
```
exportacao_backup/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── services.py
├── signals.py
├── tasks.py
├── urls.py
├── views.py
└── templates/
    └── exportacao_backup/
        ├── lista_backups.html
        ├── criar_backup.html
        ├── lista_exportacoes.html
        ├── criar_exportacao.html
        ├── configuracao_backup.html
        └── configuracao_exportacao.html
```

## Notas
- Os backups automáticos são executados a cada 15 minutos
- Arquivos de backup e exportação são armazenados em diretórios específicos
- Backups antigos são automaticamente removidos conforme a configuração
- Exportações podem ser filtradas para incluir apenas dados específicos 