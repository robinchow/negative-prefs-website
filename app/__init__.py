from flask import Flask
from flask_pymongo import PyMongo
import configparser
import sendgrid

app = Flask(__name__)
mongo = PyMongo(app)
config = configparser.ConfigParser()
config.read('config.ini')
sg = sendgrid.SendGridAPIClient(apikey=config['Sendgrid']['APIKey'])

from app import views

