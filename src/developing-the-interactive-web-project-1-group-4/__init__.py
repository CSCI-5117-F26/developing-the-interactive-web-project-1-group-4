from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '<p>Index Page</p>'

@app.route('/hello')
def hello():
    return '<p>Hello, World</p>'
