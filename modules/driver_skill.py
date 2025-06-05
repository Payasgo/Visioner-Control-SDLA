import numpy as np
import tensorflow as tf

class DriverSkillClassifier:
    """
    Predicts the driver's skill level using a trained deep learning model.
    """

    def __init__(self, model_path='models/skill_classifier.h5'):
        self.labels = ['Beginner', 'Medium', 'Pro']
        try:
            self.model = tf.keras.models.load_model(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {model_path}: {e}")

    def predict_skill(self, input_data):
        """
        Predicts the skill level from sensor input.
        :param input_data: np.array of driving metrics
        :return: (label: str, confidence: float)
        """
        if not isinstance(input_data, np.ndarray):
            raise ValueError("input_data must be a NumPy array")
        pred = self.model.predict(np.expand_dims(input_data, axis=0), verbose=0)[0]
        label_idx = np.argmax(pred)
        return self.labels[label_idx], float(pred[label_idx])
