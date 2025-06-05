from flask import jsonify, render_template
from app import app
from app.telemetry import get_simulated_data

@app.route('/api/telemetry')
def telemetry():
    data = get_simulated_data()
    return jsonify(data)

@app.route('/')
def index():
    return render_template('index.html')
