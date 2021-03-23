import os


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    # appliation
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'A SECRET KEY'
    # database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')