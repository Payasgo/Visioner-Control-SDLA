from flask import Flask, render_template, jsonify, request
from modules.driver_skill import DriverSkillClassifier
from modules.coaching import VoiceCoach
from modules.speed_gear import check_speed_limit, gear_alert
from modules.safety_parking import auto_correct, parking_logic
from modules.progress_tracker import LessonProgressTracker

app = Flask(__name__)

skill_classifier = DriverSkillClassifier()
voice_coach = VoiceCoach()
progress_tracker = LessonProgressTracker()

@app.route('/')
def dashboard():
    progress = progress_tracker.get_progress()
    return render_template('dashboard.html', progress=progress)

@app.route('/predict_skill', methods=['POST'])
def predict_skill():
    data = request.json
    input_data = data['input_data']  # preprocessed sensor input
    skill, confidence = skill_classifier.predict_skill(input_data)
    return jsonify({'skill': skill, 'confidence': confidence})

@app.route('/coaching', methods=['POST'])
def coaching():
    telemetry = request.json
    voice_coach.analyze_and_coach(telemetry)
    return jsonify({'status': 'Coaching tip given'})

@app.route('/speed_gear_alert', methods=['POST'])
def speed_gear_alert():
    data = request.json
    speed = data['speed']
    gear = data['gear']
    speed_msg = check_speed_limit(speed)
    gear_msg = gear_alert(gear, speed)
    return jsonify({'speed_alert': speed_msg, 'gear_alert': gear_msg})

@app.route('/auto_correct', methods=['POST'])
def auto_correct_route():
    data = request.json
    steering_angle = data['steering_angle']
    corrected_angle = auto_correct(steering_angle)
    return jsonify({'corrected_angle': corrected_angle})

@app.route('/parking', methods=['POST'])
def parking():
    sensor_data = request.json
    msg = parking_logic(sensor_data)
    return jsonify({'parking_msg': msg})

@app.route('/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    lesson = data['lesson']
    status = data['status']
    progress_tracker.update_progress(lesson, status)
    return jsonify({'status': 'Progress updated'})

if __name__ == '__main__':
    app.run(debug=True)
