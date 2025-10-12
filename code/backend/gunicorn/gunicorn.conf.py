# Memory-optimized Gunicorn configuration
workers = 4  # Reduced workers to save memory
worker_class = "sync"
worker_connections = 1000
max_requests = 1000  # Restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Memory management
worker_tmp_dir = "/dev/shm"  # Use RAM disk for temp files

syslog = True
bind = ["10.10.0.173:85"] # ["smlab.niser.ac.in:85"] # ["10.10.0.173:80"]
umask = 0
loglevel = "info"
user = "rishi"
group = "rishi"
accesslog = "/home/rishi/roadwatch/code/backend/logs/gunicorn_roadwatch_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Real-IP}i)s"'
errorlog = "/home/rishi/roadwatch/code/backend/logs/gunicorn_roadwatch_error.log"
