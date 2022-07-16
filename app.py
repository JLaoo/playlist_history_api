from flask import Flask
import os

app = Flask(__name__)

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
mongo_user = os.getenv('MONGO_USER')
mongo_pw = os.getenv('MONGO_PASS')
mongo_access_str = "mongodb+srv://{}:{}@cluster0.nhgsz.mongodb.net/data?retryWrites=true&w=majority".format(mongo_user, mongo_pw)

@app.route("/")
def index():
    return mongo_access_str