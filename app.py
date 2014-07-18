import os
import logging
import logging.handlers

from flask import Flask, Blueprint, current_app, request

UWSGI_SIG_SET_LOG_LEVEL = 42

bp = Blueprint('default', __name__)

@bp.route('/')
def index():
    logger = current_app.logger
    msg = 'hello from: '+get_runtime_env()
    logger.debug(msg)
    logger.info(msg)
    logger.warning(msg)
    return msg,200

@bp.route('/logger', methods=['GET', 'PUT'])
def admin_logger():
    logger = current_app.logger

    if request.method == 'GET':
        return logging.getLevelName(logger.level),200

    # PUT
    set_log_level()
    if is_uwsgi():
        uwsgi.signal(UWSGI_SIG_SET_LOG_LEVEL) # notify uwsgi workers

    return logging.getLevelName(logger.level),200
        
def is_uwsgi():
    return request.environ.get('uwsgi.version') is not None

def get_runtime_env():
    if is_uwsgi():
        return 'uwsgi'
    else:
        return 'local development server'

def create_app():
    app = Flask(__name__)
    configure_logging(app)
    app.register_blueprint(bp)
    return app

def configure_logging(app):
    logpath = 'logs/app.log'
    ensure_dir(logpath)
    level = logging.WARNING
    logger = app.logger

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(process)d - %(message)s (%(pathname)s : %(lineno)s)')
    
    file_handler = logging.handlers.RotatingFileHandler(logpath, maxBytes=5*1000*1000, backupCount=100)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(level)

    logger.info('logging to: %s', logpath)

def ensure_dir(path):
    dirpath = os.path.dirname(path)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def parse_log_level():
    'log level from current request'
    return getattr(logging, request.args.get('level'))

def set_log_level(sig=None):
    'set log level from current request'
    logger = current_app.logger

    if sig is not None and sig != UWSGI_SIG_SET_LOG_LEVEL:
        logger.info('refusing to set log level on signal: %s', sig)
        return

    level = parse_log_level()
    level_name = logging.getLevelName(level)
    msg = 'Setting log level to: %s'

    logger.debug(msg, level_name)
    logger.info(msg, level_name)
    logger.warning(msg, level_name)

    logger.setLevel(level)

try:
    import uwsgi
    uwsgi.register_signal(UWSGI_SIG_SET_LOG_LEVEL, 'workers', set_log_level) 
except ImportError:
    pass


if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
