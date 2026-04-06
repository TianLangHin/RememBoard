import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', 'css')

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

import os

app = Flask(__name__, static_folder=os.path.join('..', 'controller', 'dist'), static_url_path='/')
CORS(app)

@app.route('/')
def root():
    return jsonify({'chess': True})

@app.route('/controller')
def controller():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(port=5002)
