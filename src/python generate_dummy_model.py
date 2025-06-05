import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

MODEL_PATH = 'driver_detection_model.h5'

# Step 1: Generate a dummy model if it doesn't exist
if not os.path.exists(MODEL_PATH):
    print("🔧 Dummy model not found. Creating one...")

    # Create dummy dataset (100 samples, 224x224 RGB, 2 classes)
    X_dummy = np.random.rand(100, 224, 224, 3)
    y_dummy = tf.keras.utils.to_categorical(np.random.randint(2, size=(100,)), num_classes=2)

    # Define simple CNN model
    model = Sequential([
        Conv2D(16, (3, 3), activation='relu', input_shape=(224, 224, 3)),
        MaxPooling2D(2, 2),
        Conv2D(32, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),
        Flatten(),
        Dense(64, activation='relu'),
        Dense(2, activation='softmax')  # 2 output classes: 'Distracted', 'Attentive'
    ])

    # Compile and train the model briefly
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(X_dummy, y_dummy, epochs=1, batch_size=8)

    # Save the model
    model.save(MODEL_PATH)
    print("✅ Dummy model created and saved as driver_detection_model.h5")
else:
    print("✅ Dummy model already exists. Loading...")

# Step 2: Load the model
model = tf.keras.models.load_model(MODEL_PATH)

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Labels for output
labels = ['Distracted', 'Attentive']

# Step 3: Start real-time webcam driver detection
cap = cv2.VideoCapture(0)
print("📹 Starting webcam. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        # Draw rectangle around the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        face_img = frame[y:y+h, x:x+w]
        face_resized = cv2.resize(face_img, (224, 224))
        face_normalized = face_resized / 255.0
        face_input = np.expand_dims(face_normalized, axis=0)

        # Predict
        prediction = model.predict(face_input, verbose=0)[0]
        label_idx = np.argmax(prediction)
        label = labels[label_idx]
        confidence = prediction[label_idx]

        # Display result
        text = f'{label} ({confidence * 100:.1f}%)'
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255) if label == 'Distracted' else (0, 255, 0), 2)

    if len(faces) == 0:
        cv2.putText(frame, "No face detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Driver Detection (Press 'q' to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("👋 Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
