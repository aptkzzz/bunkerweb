from os import cpu_count, getenv, sep
from os.path import join
from sys import path as sys_path

deps_path = join(sep, "usr", "share", "bunkerweb", "deps", "python")
if deps_path not in sys_path:
    sys_path.append(deps_path)

from gevent import monkey

monkey.patch_all()

MAX_THREADS = int(getenv("MAX_THREADS", max((cpu_count() or 1) - 1, 1)) * 2)

wsgi_app = "main:app"
accesslog = "/var/log/bunkerweb/ui-access.log"
errorlog = "/var/log/bunkerweb/ui.log"
loglevel = "info"
proc_name = "bunkerweb-ui"
preload_app = True
reuse_port = True
pidfile = join(sep, "var", "run", "bunkerweb", "ui.pid")
worker_tmp_dir = join(sep, "dev", "shm")
tmp_upload_dir = join(sep, "var", "tmp", "bunkerweb", "ui")
worker_class = "gevent"
threads = MAX_THREADS
workers = 1
graceful_timeout = 0
secure_scheme_headers = {}
