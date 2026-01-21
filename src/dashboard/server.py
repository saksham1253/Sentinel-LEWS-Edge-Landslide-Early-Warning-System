from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='frontend')

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    print("Starting Dashboard on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)
