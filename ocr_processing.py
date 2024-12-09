import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Nonaktifkan GPU

import cv2
import re
import json
import sys
import logging
import tensorflow as tf
import numpy as np
from paddleocr import PaddleOCR

# Konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Inisialisasi PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

# Fungsi untuk ekstraksi teks dari gambar
def extract_text_from_image(image_path):
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    nutrition_data = {}

    # Pola pencarian untuk gula dan sajian
    sugar_pattern = '|'.join(re.escape(v) for v in ['Sugars', 'Gula', 'Sucrose', 'Fructose', 'Glucose'])
    serving_pattern = '|'.join(re.escape(v) for v in ['Sajian per kemasan', 'Serving per container', 'Jumlah porsi'])

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
                nutrition_data[key] = found_value.strip()

    if "Sajian per kemasan" not in nutrition_data:
        nutrition_data["Sajian per kemasan"] = "1"

    if "Sugars" in nutrition_data:
        sugar_value = float(re.search(r"[\d.]+", nutrition_data["Sugars"]).group())
        serving_count = int(nutrition_data["Sajian per kemasan"])
        nutrition_data["Total Sugar"] = f"{sugar_value * serving_count:.2f} g"

    return nutrition_data

# Analisis dengan model TensorFlow
def analyze_with_model(nutrition_info, model_path):
    try:
        model = tf.keras.models.load_model(model_path, compile=False)

        serving_per_package = float(nutrition_info.get("Sajian per kemasan", 1))
        sugar = float(re.search(r"[\d.]+", nutrition_info.get("Sugars", "0")).group())
        total_sugar = float(re.search(r"[\d.]+", nutrition_info.get("Total Sugar", "0")).group())

        input_data = np.array([[serving_per_package, sugar, total_sugar]])
        logging.info(f"Input data shape: {input_data.shape}")

        input_data_normalized = input_data / np.max(input_data, axis=0)

        if input_data_normalized.shape != (1, 3):
            raise ValueError(f"Invalid input shape: {input_data_normalized.shape}. Expected shape: (1, 3)")

        predictions = model.predict(input_data_normalized)
        kategori_gula = "Tinggi Gula" if predictions[0][0].item() > 0.5 else "Rendah Gula"
        rekomendasi = "Kurangi Konsumsi" if predictions[0][1].item() > 0.5 else "Aman Dikonsumsi"

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
        image_path = sys.argv[1]
        model_path = sys.argv[2]

        extracted_text = extract_text_from_image(image_path)
        nutrition_info = parse_nutrition_info(extracted_text)

        if nutrition_info:
            analysis_result = analyze_with_model(nutrition_info, model_path)
            response = {
                "message": "Berhasil",
                "nutrition_info": nutrition_info,
                "analysis": analysis_result
            }
        else:
            response = {
                "message": "Tidak ditemukan informasi nutrisi yang valid",
                "nutrition_info": {}
            }

        print(json.dumps(response, indent=4), flush=True)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "nutrition_info": {}}
        print(json.dumps(response, indent=4), flush=True)
        sys.exit(1)
