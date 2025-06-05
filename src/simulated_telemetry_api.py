import random
import time
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/telemetry')
def simulated_telemetry():
    data = {
        'speed_kmh': round(random.uniform(0, 120), 2),
        'rpm': random.randint(800, 4000),
        'throttle_position': round(random.uniform(5, 90), 2),
        'coolant_temp_c': round(random.uniform(70, 110), 2),
        'timestamp': time.time()
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
