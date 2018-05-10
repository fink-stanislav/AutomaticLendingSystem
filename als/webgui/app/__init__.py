"""
Initialization of Flask application. Secret key is needed for using session.
"""
from flask import Flask

app = Flask(__name__)
app.secret_key = 'some_secret'

from app import routes
