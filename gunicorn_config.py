# Gunicorn configuration file
workers = 4
worker_class = 'sync'
bind = '0.0.0.0:10000'
timeout = 120
keepalive = 5
threads = 4
worker_connections = 1000
