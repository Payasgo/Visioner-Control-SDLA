import obd
from flask import Flask, jsonify

app = Flask(__name__)

# Connect to the vehicle
connection = obd.OBD()  # auto-connects to USB/Bluetooth ELM327

@app.route('/api/telemetry')
def get_telemetry():
    speed = connection.query(obd.commands.SPEED)  # e.g. 0 km/h
    rpm = connection.query(obd.commands.RPM)
    throttle = connection.query(obd.commands.THROTTLE_POS)
    coolant_temp = connection.query(obd.commands.COOLANT_TEMP)

    return jsonify({
        'speed_kmh': speed.value.magnitude if speed.value else None,
        'rpm': rpm.value.magnitude if rpm.value else None,
        'throttle_position': throttle.value.magnitude if throttle.value else None,
        'coolant_temp_c': coolant_temp.value.magnitude if coolant_temp.value else None
    })

if __name__ == '__main__':
    app.run(debug=True)
