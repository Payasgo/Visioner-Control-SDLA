import numpy as np
import tensorflow as tf

class DriverSkillClassifier:
    def __init__(self, model_path='models/skill_classifier.h5'):
        self.model = tf.keras.models.load_model(model_path)
        self.labels = ['Beginner', 'Medium', 'Pro']

    def predict_skill(self, input_data):
        # input_data: preprocessed sensor data, e.g., driving metrics
        pred = self.model.predict(np.expand_dims(input_data, axis=0))[0]
        label_idx = np.argmax(pred)
        return self.labels[label_idx], pred[label_idx]
