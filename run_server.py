from waitress import serve
from app import app

import os
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(script_dir, 'logs')

if not os.path.exists(logs_dir):
    os.mkdir(logs_dir)

logging.basicConfig(filename=os.path.join(logs_dir, 'server.log'),
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG)

if __name__ == '__main__':
    serve(app, host='*', port=8200)

