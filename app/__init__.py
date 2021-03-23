import logging
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging.handlers import SMTPHandler, RotatingFileHandler
from time import time
from datetime import datetime

from config import BaseConfig


# flask modules
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=BaseConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    
    from app.couriers import bp as couriers_bp
    app.register_blueprint(couriers_bp)

    from app.orders import bp as orders_bp
    app.register_blueprint(orders_bp)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/{}_delivery.log'.format(datetime.now().strftime("%Y%m%d_%H%M%s")),
                                        maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))

    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Delivery service startup')

    return app


from app import models
