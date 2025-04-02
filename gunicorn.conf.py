import multiprocessing
import os

# Configurações do servidor
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2

# Configurações de logging
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

# Configurações de processo
daemon = False
pidfile = "logs/gunicorn.pid"
umask = 0o007
user = None
group = None
tmp_upload_dir = None

# Configurações de SSL (se necessário)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# Configurações de proxy
proxy_protocol = True
proxy_allow_ips = "*"

# Configurações de buffer
max_requests = 1000
max_requests_jitter = 50

# Configurações de timeout
graceful_timeout = 30
forwarded_allow_ips = "*"

# Configurações de segurança
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 