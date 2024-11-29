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
        print("Loading model...")
        model = load_model()
        print("Model loaded.")

        # Simulasikan panggilan pertama untuk inisialisasi
        print("Initializing model with dummy input...")
        dummy_input = np.zeros((1, 32, 32, 3))  # Sesuaikan ukuran dengan model Anda
        model(dummy_input)
        print("Model initialized.")

        # Preprocessing gambar
        print("Preprocessing image...")
        input_tensor = preprocess_image(image_path)
        print(f"Shape input tensor: {input_tensor.shape}")

        # Debugging output shape sebelum Flatten
        intermediate_layer_name = "flatten"  # Nama layer Flatten
        intermediate_layer_model = tf.keras.Model(inputs=model.input, outputs=model.get_layer(intermediate_layer_name).output)
        intermediate_output = intermediate_layer_model.predict(input_tensor)
        print(f"Shape setelah layer {intermediate_layer_name}: {intermediate_output.shape}")

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
