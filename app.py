from flask import Flask
import os
from flask_pymongo import PyMongo
from flask_cors import CORS

youtube_api_key = os.getenv('YOUTUBE_API_KEY')
mongo_user = os.getenv('MONGO_USER')
mongo_pw = os.getenv('MONGO_PASS')
mongo_access_str = "mongodb+srv://{}:{}@cluster0.nhgsz.mongodb.net/data?retryWrites=true&w=majority".format(mongo_user, mongo_pw)

app = Flask(__name__)
app.config["MONGO_URI"] = mongo_access_str
client = PyMongo(app)
col = client.db.data
CORS(app)

@app.route("/")
def index():
    list_id = 'list_of_all_ids'
    query = { "_id": list_id }
    doc = col.find_one(query)
    return doc