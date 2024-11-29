import sys
import json
import cv2
import numpy as np
import os
import tensorflow as tf

# Minimize TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.get_logger().setLevel('ERROR')

# Force TensorFlow to use CPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Load model
def load_model():
    model_path = "/home/ghavio_rizky_ananda_budiawan_tik/nutrigood-app-backend-master-nonfirebase/model/CustomCnn_model.keras"
    return tf.keras.models.load_model(model_path)

# Preprocess image
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or invalid.")
    
    image = cv2.resize(image, (32, 32))  # Adjust to your model input size
    image = image.astype('float32') / 255.0  # Normalize to [0, 1]
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

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

        # Cetak JSON dengan label Output
        print(f"Output : {json.dumps(predictions_json)}")

    except Exception as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)
