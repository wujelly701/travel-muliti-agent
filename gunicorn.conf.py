import os
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
worker_class = 'uvicorn.workers.UvicornWorker'
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
loglevel = os.getenv('GUNICORN_LOGLEVEL', 'info')
accesslog = '-'  # stdout
errorlog = '-'  # stderr
preload_app = True
