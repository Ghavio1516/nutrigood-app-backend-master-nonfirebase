import sys
import json
import cv2
import numpy as np
import tensorflow as tf
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Fungsi untuk memuat model Keras
def load_model():
    model_path = "/home/ghavio_rizky_ananda_budiawan_tik/nutrigood-app-backend-master-nonfirebase/model/CustomCnn_model.keras"
    model = tf.keras.models.load_model(model_path)  # Muat model .keras
    return model

# Fungsi untuk memproses gambar menjadi tensor
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or invalid.")
    
    # Resize gambar ke ukuran yang sesuai dengan model
    image = cv2.resize(image, (128, 128))  # Pastikan sesuai dengan IMG_SIZE
    image = image.astype('float32') / 255.0  # Normalisasi ke [0, 1]
    image = np.expand_dims(image, axis=0)  # Tambahkan batch dimension
    return image

# Load model dan prediksi
try:
    image_path = sys.argv[1]
    print("Loading model...")
    model = load_model()  # Pastikan model di-load dengan benar
    print("Model loaded.")
    
    print("Preprocessing image...")
    input_tensor = preprocess_image(image_path)
    print(f"Input tensor shape: {input_tensor.shape}")
    
    print("Making predictions...")
    predictions = model.predict(input_tensor, batch_size=1)
    print("Predictions made.")
    
    # Format output sebagai JSON
    predictions_json = predictions.tolist()
    print(json.dumps(predictions_json))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)