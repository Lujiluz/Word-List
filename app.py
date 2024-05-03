from flask import Flask, jsonify,redirect,url_for,render_template,request
import os
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
import requests
from datetime import datetime
import ast


dotenv = join(dirname(__file__), '.env')
load_dotenv(dotenv)

api_key = os.environ.get('API_KEY')
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]


app=Flask(__name__)


"""
This route should fetch all of the
words from database and pass them on
to the HTML template
"""
@app.route('/',methods=['GET','POST'])
def home():
    words_from_db = db.words.find({}, {'_id': False})
    words = []
    for word in words_from_db:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definitions': definition
        })
        
    return render_template('index.html', words=words)


"""
This handler should find
the requested word through the dictionary
API and pass the data for that word
onto the template
"""
@app.route('/detail/<keyword>')
def detail(keyword):
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    if not definitions:
        return redirect(url_for('not_found', msg=f'Could not find {keyword}'))
    
    if type(definitions[0]) is str:
        return redirect(url_for('not_found',  msg=f'could not find {keyword}. Do you mean:', definitions=definitions))
    
    status = request.args.get('status')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)



"""
This handler should save the word in the database
"""
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word')
    definitions = json_data.get('definitions')
    data = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%A, %Y-%m')
    }
    
    db.words.insert_one(data)
    return jsonify({'result': 'success', 'msg': f'{word} saved'})


"""
This handler should delete the word from the database
"""
@app.route('/api/delete_word', methods=["POST"])
def delete_word():
    word = request.form.get('word')
    db.words.delete_one({'word': word})
    return jsonify({'result': f'success', 'msg': f'{word} deleted'})

@app.route('/notfound?<msg>?<definitions>')
def not_found(msg, definitions):
    defs = ast.literal_eval(definitions)
    return render_template('NotFound.html', msg=msg, definitions=defs)

@app.route('/api/save_egSentence', methods=['POST'])
def save_egSentence():
    sentence = request.form['sentence']
    id = request.form['id']
    
    data = {
        'id': id,
        'sentence': sentence
    }
    db.sentence.insert_one(data)
    return jsonify({'msg': 'sentence saved!'})

@app.route('/api/del_egSentence', methods=['POST'])
def del_egWord():
    id = request.form['id']
    db.sentence.delete_one({'id': id})
    return jsonify({'msg': 'sentence deleted!'})

@app.route('/api/get_egSentence', methods=['GET'])
def get_egSentence():
    data = list(db.sentence.find({}, {'_id': False}))
    return jsonify(data)

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)