import numpy as np
import pytest
from modules.driver_skill import DriverSkillClassifier

@pytest.fixture
def dummy_classifier(monkeypatch):
    class DummyModel:
        def predict(self, x, verbose=0):
            return [[0.1, 0.2, 0.7]]
    monkeypatch.setattr("tensorflow.keras.models.load_model", lambda _: DummyModel())
    return DriverSkillClassifier("dummy_path")

def test_predict_skill(dummy_classifier):
    data = np.array([0.5, 0.2, 0.3])
    label, confidence = dummy_classifier.predict_skill(data)
    assert label == "Pro"
    assert 0 <= confidence <= 1
