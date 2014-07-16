import os
import logging
import logging.handlers

from flask import Flask, Blueprint, current_app, request

bp = Blueprint('default', __name__)

@bp.route('/')
def index():
    logger = current_app.logger
    msg = 'hello'
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
    level = request.args.get('level')
    if level:
        logger.setLevel(getattr(logging, level))
    
    return logging.getLevelName(logger.level),200
        



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

    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s (%(process)d %(pathname)s : %(lineno)s)')
    
    file_handler = logging.handlers.RotatingFileHandler(logpath, maxBytes=1000, backupCount=100)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(level)

    logger.info('logging to: %s', logpath)

def ensure_dir(path):
    dirpath = os.path.dirname(path)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
