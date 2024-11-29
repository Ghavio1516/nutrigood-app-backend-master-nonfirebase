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
    model = tf.keras.models.load_model(model_path)
    return model

# Fungsi untuk memproses gambar menjadi tensor
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or invalid.")
    
    # Resize gambar ke ukuran yang diharapkan model
    image = cv2.resize(image, (32, 32))  # Sesuaikan dengan ukuran input model
    image = image.astype('float32') / 255.0  # Normalisasi ke [0, 1]
    image = np.expand_dims(image, axis=0)  # Tambahkan dimensi batch
    return image

# Fungsi utama
if __name__ == '__main__':
    try:
        # Path ke gambar yang akan diproses
        image_path = sys.argv[1]

        # Muat model Keras
        model = load_model()

        # Preprocessing gambar
        input_tensor = preprocess_image(image_path)

        # Prediksi dengan model
        predictions = model.predict(input_tensor)

        # Konversi hasil prediksi ke JSON
        predictions_json = predictions.tolist()

        # Cetak hasil sebagai JSON (tanpa log tambahan)
        print(json.dumps(predictions_json))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
