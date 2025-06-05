
import cv2
import numpy as np
import tensorflow as tf

# Load pre-trained TensorFlow/Keras model
model = tf.keras.models.load_model('driver_detection_model.h5')  # Replace with your model path

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Labels (update based on your model classes)
labels = ['Distracted', 'Attentive']

# Start video capture
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Extract the face ROI
        face_img = frame[y:y+h, x:x+w]

        # Preprocess for model (resize, normalize)
        face_resized = cv2.resize(face_img, (224, 224))  # Change to match model input
        face_normalized = face_resized / 255.0
        face_input = np.expand_dims(face_normalized, axis=0)

        # Predict
        prediction = model.predict(face_input)[0]
        label_idx = np.argmax(prediction)
        label = labels[label_idx]
        confidence = prediction[label_idx]

        # Display prediction
        text = f'{label} ({confidence*100:.1f}%)'
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if label == 'Distracted' else (0, 255, 0), 2)

    # Show video feed
    cv2.imshow("Driver Detection", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release everything
cap.release()
cv2.destroyAllWindows()
