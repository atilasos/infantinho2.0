import os
from celery import Celery

# Definir a variável de ambiente para as configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infantinho.settings')

# Criar a aplicação Celery
app = Celery('infantinho')

# Carregar as configurações do arquivo settings.py do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carregar automaticamente as tasks de todos os apps registrados
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 