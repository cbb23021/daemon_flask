import os


class Config:
    # --- Config --- #
    APP_NAME = os.environ['APP_NAME']
    SYSTEM_NAME = os.environ['SYSTEM_NAME']
    ENVIRONMENT = os.environ['ENVIRONMENT']
    MODELS_PATH_LIST = ['common.orm.fantasyee_models']

    # --- Salt --- #
    SALT = os.environ['SALT']
    SECRET_KEY = os.environ.get('SECRET_KEY', None)

    # --- Host --- #
    FRONTEND_HOST = os.environ['FRONTEND_HOST']
    STATIC_HOST = os.environ['STATIC_HOST']

    # --- Database --- #
    DB_NAME = os.environ['DB_NAME']

    DB_USER = os.environ['MYSQL_USER']
    DB_PWD = os.environ['MYSQL_PASSWORD']
    DB_HOST = os.environ['MYSQL_HOST']
    DB_PORT = os.environ['MYSQL_PORT']

    SQLALCHEMY_BINDS = {
        DB_NAME: f'mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Redis --- #
    REDIS_HOST = os.environ['REDIS_HOST']
    REDIS_PORT = os.environ['REDIS_PORT']
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

    # --- K8S --- #
    K8S_PROBE_TOKEN = os.environ.get('K8S_PROBE_TOKEN', None)
    PROBE_OPEN = os.environ.get('PROBE_OPEN', None)

    # --- Expire Time --- #
    ACCESS_TOKEN_EXPIRE_TIME = 60 * 60 * 24
    REFRESH_TOKEN_EXPIRE_TIME = 60 * 60 * 24
