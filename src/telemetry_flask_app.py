from flask import Flask, jsonify, render_template_string
import random
import time

app = Flask(__name__)

# Simulated telemetry data generator
def get_simulated_data():
    return {
        "speed": round(random.uniform(0, 120), 2),        # km/h
        "rpm": random.randint(600, 4000),                # engine RPM
        "engine_temp": round(random.uniform(70, 120), 1),# °C
        "fuel_level": round(random.uniform(0, 100), 1),  # percentage
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# API endpoint to get telemetry data
@app.route('/api/telemetry')
def telemetry():
    data = get_simulated_data()
    return jsonify(data)

# Simple HTML UI using JS to fetch telemetry every 2 seconds
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Vehicle Telemetry Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 40px; }
      h1 { color: #333; }
      .data { margin-top: 20px; font-size: 1.2em; }
      .label { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Vehicle Telemetry Dashboard</h1>
    <div id="telemetry" class="data">
        Loading telemetry data...
    </div>

    <script>
      async function fetchTelemetry() {
          try {
              const res = await fetch('/api/telemetry');
              const data = await res.json();
              document.getElementById('telemetry').innerHTML = `
                  <p><span class="label">Speed:</span> ${data.speed} km/h</p>
                  <p><span class="label">RPM:</span> ${data.rpm}</p>
                  <p><span class="label">Engine Temperature:</span> ${data.engine_temp} °C</p>
                  <p><span class="label">Fuel Level:</span> ${data.fuel_level} %</p>
                  <p><span class="label">Timestamp:</span> ${data.timestamp}</p>
              `;
          } catch (err) {
              document.getElementById('telemetry').innerHTML = 'Error loading data';
          }
      }

      // Refresh data every 2 seconds
      setInterval(fetchTelemetry, 2000);
      fetchTelemetry(); // initial call
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(debug=True)
