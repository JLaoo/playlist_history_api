from flask import Flask, abort, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import pymongo
import requests
import json


with open('credentials.txt') as f:
    lines = f.readlines()


youtube_api_key = lines[0][len("youtube_api_key="):].strip()
mongo_user = lines[1][len("mongo_user="):].strip()
mongo_pw = lines[2][len("mongo_pw="):].strip()
mongo_access_str = "mongodb+srv://{}:{}@cluster0.nhgsz.mongodb.net/?retryWrites=true&w=majority".format(mongo_user, mongo_pw)

client = pymongo.MongoClient(mongo_access_str)
col = client.data.data

all_id_list_key = "list_of_all_ids"

def get_playlist_objs(list_id):
    objs = []
    r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={}&key={}".format(list_id, youtube_api_key))
    while True:
        json_obj = json.loads(r.text)
        objs.append(json_obj)
        if 'nextPageToken' not in json_obj:
            break
        r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={}&key={}&pageToken={}".format(list_id, youtube_api_key, json_obj['nextPageToken']))
    return objs

def get_playlist_state(objs):
    playlist_state = []
    for obj in objs:
        for item in obj['items']:
            playlist_item = {}
            playlist_item['title'] = item['snippet']['title']
            playlist_item['url'] = 'https://www.youtube.com/watch?v={}'.format(item['snippet']['resourceId']['videoId'])
            playlist_state.append(playlist_item)
    playlist_state.sort(key = lambda x : x['title'])
    return playlist_state

def update(list_id):
    objs = get_playlist_objs(list_id)
    query = { "_id": list_id }
    doc = col.find_one(query)
    if doc is None:
        add_to_list(list_id)
        new_doc = {}
        new_doc['_id'] = list_id
        new_doc['updates'] = []

        playlist_state = get_playlist_state(objs)
        new_doc['start_state'] = playlist_state
        new_doc['cur_state'] = playlist_state

        col.insert_one(new_doc)
        return new_doc
    else:
        cur_state = get_playlist_state(objs)
        cur_state_tuples = [tuple(d.values()) for d in cur_state]
        prev_state = doc['cur_state']
        prev_state_tuples = [tuple(d.values()) for d in prev_state]
        deleted_items = set(prev_state_tuples).difference(cur_state_tuples)
        added_items = set(cur_state_tuples).difference(prev_state_tuples)

        if len(deleted_items) != 0 or len(added_items) != 0:
            deleted_arr = []
            for item in deleted_items:
                playlist_item = {}
                playlist_item['title'] = item[0]
                playlist_item['url'] = item[1]
                deleted_arr.append(playlist_item)

            added_arr = []
            for item in added_items:
                playlist_item = {}
                playlist_item['title'] = item[0]
                playlist_item['url'] = item[1]
                added_arr.append(playlist_item)

            cur_update = {'deleted': deleted_arr, 'added': added_arr}

            col.update_one({'_id': list_id}, {'$push': {'updates': cur_update}})
            col.update_one({'_id': list_id}, {'$set': {'cur_state': cur_state}})
            return col.find_one(query)
        return doc

def update_all():
    query = { "_id": all_id_list_key }
    doc = col.find_one(query)
    if doc is not None:
        ids = doc['ids']
        for _id in ids:
            update(_id)

def add_to_list(new_id):
    query = { "_id": all_id_list_key }
    doc = col.find_one(query)
    if doc is None:
        new_doc = {}
        new_doc['_id'] = all_id_list_key
        new_doc['ids'] = [new_id]
        col.insert_one(new_doc)
    else:
        col.update_one({'_id': all_id_list_key}, {'$push': {'ids': new_id}})

app = Flask(__name__)
CORS(app)

@app.route('/lookup/<string:list_id>')
def lookup(list_id):
    return update(list_id)

@app.route('/updateall')
def update_all_ids():
    update_all()
    print("all updated")
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code


if __name__ == '__main__':
   app.run()
