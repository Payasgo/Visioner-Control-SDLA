# modules/driver_skill.py

import numpy as np


class DriverSkillClassifier:
    """
    Predicts the driver's skill level using a trained deep learning model.

    The TensorFlow model is loaded lazily so that the rest of the application
    can start even when TensorFlow is not installed.
    """

    LABELS = ["Beginner", "Medium", "Pro"]
    # Canonical path produced by model/train_model.py
    DEFAULT_MODEL_PATH = "model/driver_skill_model.h5"

    def __init__(self, model_path: str | None = None) -> None:
        self._model_path = model_path or self.DEFAULT_MODEL_PATH
        self._model = None  # loaded on first predict

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            import tensorflow as tf  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "TensorFlow is required for DriverSkillClassifier. "
                "Install it with: pip install tensorflow"
            ) from exc

        try:
            self._model = tf.keras.models.load_model(self._model_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load model from '{self._model_path}': {exc}"
            ) from exc

        return self._model

    def predict_skill(self, input_data: np.ndarray) -> tuple[str, float]:
        """
        Predicts skill level from a 1-D array of driving metrics.

        Returns:
            (label, confidence) where label is one of 'Beginner', 'Medium', 'Pro'
            and confidence is a float in [0, 1].
        """
        if not isinstance(input_data, np.ndarray):
            raise TypeError(
                f"input_data must be a numpy.ndarray, got {type(input_data).__name__}"
            )

        model = self._load_model()
        pred = model.predict(np.expand_dims(input_data, axis=0), verbose=0)[0]
        label_idx: int = int(np.argmax(pred))
        return self.LABELS[label_idx], float(pred[label_idx])
