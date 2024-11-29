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
    
    # Resize dan normalisasi sesuai dengan input model
    image = cv2.resize(image, (128, 128))  # Sesuaikan ukuran dengan model Anda
    image = image.astype('float32') / 255.0  # Normalisasi
    image = np.expand_dims(image, axis=0)  # Tambahkan dimensi batch
    return image

# Fungsi utama
if __name__ == '__main__':
    try:
        # Path ke gambar yang akan diproses
        image_path = sys.argv[1]

        # Muat model Keras
        print("Loading model...")
        model = load_model()
        print("Model loaded.")

        # Preprocessing gambar
        print("Preprocessing image...")
        input_tensor = preprocess_image(image_path)

        # Prediksi dengan model
        print("Making predictions...")
        predictions = model.predict(input_tensor)
        print("Predictions made.")

        # Konversi hasil prediksi ke JSON (sesuaikan format sesuai output model Anda)
        predictions_json = predictions.tolist()

        # Cetak hasil sebagai JSON
        print(json.dumps(predictions_json))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
