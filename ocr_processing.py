import cv2
import re
import json
import logging
import numpy as np
import tensorflow as tf
import mysql.connector
from paddleocr import PaddleOCR

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inisialisasi PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

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
    'Sajian perkemasan', 'Serving per pack', 'Serving per package',
    'Servings Per Container about', 'Jumlah sajian', 'Takaran saji'
]

# Fungsi untuk ekstraksi teks dari gambar
def extract_text_from_image(image_path):
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])
    logging.info(f"Teks hasil OCR:\n{full_text}")
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)

    patterns = {
        'Sajian per kemasan': rf'({serving_pattern})[:\-]?\s*(\d+)',
        'Sugars': rf'({sugar_pattern})[:\-]?\s*(\d+\s*[gG]|mg)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            nutrition_data[key] = match.group(2).strip()
            logging.info(f"{key} ditemukan: {nutrition_data[key]}")
        else:
            logging.warning(f"Tidak ditemukan data untuk {key}. Pola: {pattern}")

    # Hitung Total Sugar jika tersedia
    sugar_value = nutrition_data.get("Sugars")
    serving_count = nutrition_data.get("Sajian per kemasan")
    if sugar_value and serving_count:
        sugar_value = float(re.search(r"[\d.]+", sugar_value).group())
        serving_count = int(serving_count)
        nutrition_data["Total Sugar"] = sugar_value * serving_count
        logging.info(f"Total Sugar dihitung: {nutrition_data['Total Sugar']} g")

    return nutrition_data

# Ambil data pengguna dari database
def get_user_info(user_id):
    try:
        conn = mysql.connector.connect(
            host="34.50.75.195",
            user="root",
            password="12345",
            database="nutrigood-database"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT age, bb FROM users WHERE id = %s", (user_id,))
        user_info = cursor.fetchone()
        conn.close()
        if user_info:
            logging.info(f"User info ditemukan: {user_info}")
            return user_info
        else:
            logging.warning("User info tidak ditemukan.")
            return None
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        return None

# Analisis dengan model TensorFlow
def analyze_with_model(nutrition_info, user_info, model_path):
    try:
        model = tf.keras.models.load_model(model_path)

        # Siapkan input untuk model
        serving_per_package = float(nutrition_info.get("Sajian per kemasan", 1))
        sugar = float(re.search(r"[\d.]+", nutrition_info.get("Sugars", "0")).group())
        total_sugar = float(nutrition_info.get("Total Sugar", 0))
        age = user_info.get("age", 0)
        weight = user_info.get("bb", 0)

        # Normalisasi input
        input_data = np.array([[serving_per_package, sugar, total_sugar, age, weight]])
        input_data_normalized = input_data / np.max(input_data, axis=0)

        # Prediksi
        predictions = model.predict(input_data_normalized)
        kategori_gula = "Tinggi Gula" if predictions[0][0] > 0.5 else "Rendah Gula"
        rekomendasi = "Kurangi Konsumsi" if predictions[0][1] > 0.5 else "Aman Dikonsumsi"

        return {
            "Kategori Gula": kategori_gula,
            "Rekomendasi": rekomendasi
        }
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return {}

# Fungsi utama
if __name__ == "__main__":
    try:
        # Path gambar dan model
        image_path = './images/8.png'
        model_path = './model_Fixs_5Variabel.h5'
        user_id = "610e75c4081177dd0d8d58118aaa862448d8421"  # ID pengguna

        # Ekstraksi teks dari gambar
        extracted_text = extract_text_from_image(image_path)

        # Parsing informasi nutrisi
        nutrition_info = parse_nutrition_info(extracted_text)

        # Ambil data pengguna dari database
        user_info = get_user_info(user_id)

        if not nutrition_info or not user_info:
            response = {
                "message": "Data tidak lengkap untuk analisis",
                "nutrition_info": nutrition_info
            }
        else:
            # Analisis dengan model
            analysis_result = analyze_with_model(nutrition_info, user_info, model_path)
            response = {
                "message": "Berhasil",
                "nutrition_info": nutrition_info,
                "analysis": analysis_result
            }

        # Output dalam format JSON
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
