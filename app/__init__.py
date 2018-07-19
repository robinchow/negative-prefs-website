from flask import Flask
from peewee import CharField, DateTimeField, Model, SqliteDatabase
# from flask_pymongo import PyMongo
import configparser
import datetime
import sendgrid

app = Flask(__name__)
# mongo = PyMongo(app)
config = configparser.ConfigParser()
config.read('config.ini')

db = SqliteDatabase('{}-sqlite.db'.format(config['General']['Person']))
class BaseModel(Model):
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    class Meta:
        database = db

class Search(BaseModel):
    ip = CharField(max_length=64)
    url = CharField(max_length=3000)
    thing = CharField(max_length=3000)

db.connect()
db.create_tables([Search])

sg = sendgrid.SendGridAPIClient(apikey=config['Sendgrid']['APIKey'])

from app import views

