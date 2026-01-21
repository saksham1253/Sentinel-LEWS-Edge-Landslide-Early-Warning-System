from flask import Flask, render_template, jsonify
import json
import os
import shutil

# Correctly locate the web directory (relative to this file)
current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(current_dir, 'templates'),
            static_folder=os.path.join(current_dir, 'static'))

STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'outputs', 'system_status.json')

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e), "status": "FILE_ERROR"})
    else:
        return jsonify({"status": "WAITING_FOR_ENGINE", "risk_level": 0.0})

if __name__ == '__main__':
    # Local only, no internet
    app.run(host='0.0.0.0', port=5000, debug=False)
