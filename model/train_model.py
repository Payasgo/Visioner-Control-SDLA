# model/train_model.py
import tensorflow as tf
from tensorflow.keras import layers, models

# Dummy training script

def train():
    model = models.Sequential([
        layers.Dense(64, activation='relu', input_shape=(5,)),
        layers.Dense(3, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    # Dummy data
    X = [[10, 2, 0, 0.2, 5], [60, 4, 1, 0.1, 7], [90, 5, 0, -0.1, 8]]
    y = [0, 1, 2]  # beginner, medium, pro
    model.fit(X, y, epochs=5)
    model.save('model/driver_skill_model.h5')

if __name__ == "__main__":
    train()