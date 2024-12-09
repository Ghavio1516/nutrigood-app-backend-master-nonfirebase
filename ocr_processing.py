import cv2
import re
import json
import sys
import logging
import tensorflow as tf
from paddleocr import PaddleOCR
import numpy as np

# Konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Inisialisasi PaddleOCR
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    show_log=False
)

# Path ke model Keras
MODEL_PATH = "./model/model_Fix_5Variabel.keras"  # Path ke file model Keras

# Load Keras Model
try:
    logging.info(f"Loading Keras model from {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH)
    logging.info("Keras model loaded successfully")
except Exception as e:
    logging.error(f"Failed to load Keras model: {e}")
    sys.exit(1)

# Variasi pencarian teks
sugar_variations = [
    'Gula', 'Sugars', 'Sucrose', 'Fructose', 'Glucose', 'Lactose',
    'Maltose', 'High fructose corn syrup', 'Brown Sugar', 'Powdered Sugar',
    'Invert Sugar', 'Dextrose', 'Honey', 'Molasses', 'Agave', 'Agave Syrup',
    'Syrup', 'Barley Malt', 'Cane Sugar', 'Coconut Sugar', 'Palm Sugar',
    'Maple Syrup', 'Rice Syrup', 'Muscovado', 'Caramel', 'Turbinado Sugar',
    'Raw Sugar'
]

serving_variations = [
    'Sajian per kemasan', 'Serving per container', 'Servings per container',
    'Sajian perkemasan', 'Serving per pack', 'Serving perpack',
    'Serving per package', 'Serving perpackage', 'Servings Per Container about',
    'Sajian perkemasan/Serving per pack', 'Jumlah porsi', 'Jumlah sajian',
    'Takaran saji', 'Takaran saji per kemasan', 'Takaran saji per pack',
    'Takaran saji per sajian', 'Portion per Container', 'Portion per Pack',
    'Portion per Package', 'Porsi per wadah', 'Jumlah Porsi', 'Total Servings'
]

# Fungsi untuk ekstraksi teks dari gambar
def extract_text_from_image(image_path):
    logging.info(f"Starting OCR for image: {image_path}")
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])

    if full_text.strip():
        logging.info(f"Teks hasil OCR:\n{full_text.strip()}")
    else:
        logging.warning("Teks hasil OCR kosong.")
    
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    logging.info("Parsing nutrition information from OCR text.")
    nutrition_data = {}
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)

    patterns = {
        'Sajian per kemasan': rf'([0-9]+)\s*(?:[:\-]|\s*)?\s*({serving_pattern})|({serving_pattern})\s*(?:[:\-]|\s*)?\s*([0-9]+)',
        'Sugars': rf'({sugar_pattern})\s*(?:[:\-]|\s*)?\s*([0-9]+(?:\.[0-9]+)?\s*[gG]|mg)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            if key == "Sajian per kemasan":
                found_value = match.group(1) or match.group(4)
            else:
                found_value = match.group(2)

            if found_value:
                try:
                    numeric_value = float(re.search(r"[\d.]+", found_value).group())
                    nutrition_data[key] = numeric_value
                    logging.info(f"Extracted {key}: {numeric_value}")
                except (ValueError, AttributeError):
                    logging.warning(f"Invalid value for {key}: {found_value}, setting to 0.0")
                    nutrition_data[key] = 0.0
            else:
                logging.warning(f"Tidak ditemukan nilai untuk {key}, default ke 0.0.")
                nutrition_data[key] = 0.0
        else:
            logging.warning(f"Tidak ditemukan data untuk {key}, default ke 0.0.")
            nutrition_data[key] = 0.0

    if "Sajian per kemasan" not in nutrition_data:
        nutrition_data["Sajian per kemasan"] = 1.0

    if "Sugars" in nutrition_data and "Sajian per kemasan" in nutrition_data:
        try:
            nutrition_data["Total Sugar"] = nutrition_data["Sugars"] * nutrition_data["Sajian per kemasan"]
            logging.info(f"Calculated Total Sugar: {nutrition_data['Total Sugar']}")
        except TypeError:
            logging.error("Error calculating Total Sugar, setting to 0.0")
            nutrition_data["Total Sugar"] = 0.0

    return nutrition_data

# Fungsi untuk prediksi model
def predict_nutrition_info(model, inputs):
    try:
        # Konversi input ke tensor
        logging.info(f"Converting inputs to tensor: {inputs}")
        input_tensor = tf.convert_to_tensor([inputs], dtype=tf.float32)
        logging.info("Tensor conversion successful.")

        # Prediksi menggunakan model Keras
        logging.info("Performing prediction using Keras model.")
        prediction = model(input_tensor)  # Output bisa berupa Tensor atau NumPy array
        logging.info(f"Raw prediction output: {prediction}")

        # Konversi prediksi menjadi list
        if isinstance(prediction, tf.Tensor):
            prediction = prediction.numpy()  # Konversi Tensor ke NumPy array
        if isinstance(prediction, np.ndarray):
            prediction = prediction.tolist()  # Konversi NumPy array ke list

        logging.info(f"Prediction converted to list: {prediction}")
        return prediction
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return None

# Fungsi utama
if __name__ == "__main__":
    try:
        logging.info("Starting OCR and model prediction pipeline.")
        
        # Ambil argumen dari command line
        image_path = sys.argv[1]
        age = float(sys.argv[2])
        bb = float(sys.argv[3])

        logging.info(f"Image path: {image_path}, Age: {age}, BB: {bb}")

        # Cek apakah gambar bisa dibaca
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")
        logging.info("Gambar berhasil dibaca.")

        # Proses OCR
        extracted_text = extract_text_from_image(image_path)
        logging.info(f"Teks yang diekstraksi: {extracted_text}")

        # Parsing teks hasil OCR
        nutrition_info = parse_nutrition_info(extracted_text)
        logging.info(f"Informasi nutrisi yang diparsing: {nutrition_info}")

        # Cek apakah ada informasi nutrisi yang valid
        if not nutrition_info:
            response = {"message": "Tidak ditemukan", "nutrition_info": {}}
            logging.info("Tidak ada informasi nutrisi yang ditemukan.")
            print(json.dumps(response, indent=4))
            sys.exit(0)

        # Siapkan input untuk model
        model_input = [
            nutrition_info.get("Sajian per kemasan", 1.0),
            nutrition_info.get("Sugars", 0.0),
            nutrition_info.get("Total Sugar", 0.0),
            age,
            bb,
        ]
        logging.info(f"Model input: {model_input}")

        # Validasi input sebelum prediksi
        if not all(isinstance(value, (int, float)) for value in model_input):
            raise ValueError(f"Invalid input for model: {model_input}")

        # Lakukan prediksi menggunakan model
        prediction = predict_nutrition_info(model, model_input)
        logging.info(f"Hasil prediksi: {prediction}")

        # Cek apakah prediksi berhasil
        if prediction is None:
            response = {"message": "Model prediction failed", "nutrition_info": nutrition_info}
            logging.error("Prediksi model gagal.")
        else:
            response = {
                "message": "Berhasil",
                "nutrition_info": nutrition_info,
                "prediction": [float(p) for p in prediction],
            }
        logging.info(f"Final response: {response}")

        # Cetak hasil akhir
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "nutrition_info": {}}
        print(json.dumps(response, indent=4))
        sys.exit(1)
