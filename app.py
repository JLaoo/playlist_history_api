from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def index():
    return os.getenv('MONGO_USER')