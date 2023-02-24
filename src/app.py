import redis
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config.Config')
config = app.config

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # 生成 member_fee_transaction交易單號用

rs = redis.StrictRedis(
    host=config['REDIS_HOST'],
    password=config['REDIS_PASSWORD'],
    port=config['REDIS_PORT'],
    charset='utf-8',
    decode_responses=True,
)
