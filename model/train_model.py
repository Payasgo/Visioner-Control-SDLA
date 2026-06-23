# model/train_model.py

import os

import numpy as np


# Canonical output path — must match DriverSkillClassifier.DEFAULT_MODEL_PATH
MODEL_OUTPUT_PATH = "model/driver_skill_model.h5"


def train() -> None:
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models  # type: ignore
    except ImportError:
        print("TensorFlow not installed. Install with: pip install tensorflow")
        return

    model = models.Sequential(
        [
            layers.Dense(64, activation="relu", input_shape=(5,)),
            layers.Dense(32, activation="relu"),
            layers.Dense(3, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    # Feature columns: [speed, gear, brake_events, lane_offset, steering_angle_abs]
    X = np.array(
        [
            [10.0, 2, 0, 0.2, 5.0],
            [60.0, 4, 1, 0.1, 7.0],
            [90.0, 5, 0, -0.1, 8.0],
            [20.0, 1, 3, 0.8, 2.0],
            [55.0, 3, 1, 0.3, 6.0],
            [85.0, 5, 0, -0.2, 9.0],
        ],
        dtype=np.float32,
    )
    # Labels: 0=Beginner, 1=Medium, 2=Pro
    y = np.array([0, 1, 2, 0, 1, 2], dtype=np.int32)

    model.fit(X, y, epochs=50, verbose=1)

    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    model.save(MODEL_OUTPUT_PATH)
    print(f"Model saved to {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train()
