import json
import sys
import logging
import numpy as np
import tensorflow as tf
from paddleocr import PaddleOCR
import re

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
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])

    if full_text.strip():
        logging.warning(f"Teks hasil OCR:\n{full_text.strip()}")
    else:
        logging.warning("Teks hasil OCR kosong.")
    
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)

    # Pola regex terbaru
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
                logging.info(f"{key} ditemukan: {nutrition_data[key]}")
            else:
                logging.warning(f"Tidak ditemukan nilai untuk {key} meskipun pola cocok.")
        else:
            logging.warning(f"Tidak ditemukan data untuk {key}. Pola yang digunakan: {pattern}")

    # Tetapkan nilai default jika "Sajian per kemasan" tidak ditemukan
    if "Sajian per kemasan" not in nutrition_data:
        logging.error("Sajian per kemasan tidak terdeteksi! Menggunakan default 1.")
        serving_count = 1
    else:
        serving_count = int(nutrition_data["Sajian per kemasan"])
        logging.info(f"Sajian per kemasan ditemukan: {serving_count}")

    nutrition_data["Sajian per kemasan"] = serving_count

    # Hitung Total Sugar jika tersedia
    sugar_value = nutrition_data.get("Sugars")
    if sugar_value:
        try:
            sugar_amount = float(re.search(r"[\d.]+", sugar_value).group())
            nutrition_data["Total Sugar"] = sugar_amount * serving_count
            logging.info(f"Total Sugar dihitung: {nutrition_data['Total Sugar']:.2f} g")
        except AttributeError:
            logging.error("Tidak dapat menghitung Total Sugar karena nilai gula tidak valid.")

    return nutrition_data

# Fungsi untuk memuat model TensorFlow.js dan membuat prediksi
def analyze_with_model(nutrition_info, model_path):
    try:
        # Muat model dari file .h5
        model = tf.keras.models.load_model(model_path)
        logging.info("Model .h5 berhasil dimuat.")

        # Siapkan input untuk prediksi
        serving_per_package = float(nutrition_info.get("Sajian per kemasan", 0))
        sugar = float(re.search(r"[\d.]+", nutrition_info.get("Sugars", "0")).group())
        total_sugar = nutrition_info.get("Total Sugar", 0)

        input_data = np.array([[serving_per_package, sugar, total_sugar]])
        predictions = model.predict(input_data)

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
        image_path = sys.argv[1]
        model_path = "./model/analisis-nutrisi.h5"  # Sesuaikan path model

        # Ekstraksi teks dari gambar
        extracted_text = extract_text_from_image(image_path)

        # Parsing informasi nutrisi
        nutrition_info = parse_nutrition_info(extracted_text)

        # Validasi hasil
        if not nutrition_info:
            response = {"message": "Tidak ditemukan", "nutrition_info": {}}
        else:
            analysis_result = analyze_with_model(nutrition_info, model_path)
            response = {
                "message": "Berhasil",
                "nutrition_info": nutrition_info,
                "analysis": analysis_result,
            }

        print(json.dumps(response, indent=4))
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "nutrition_info": {}, "analysis": {}}
        print(json.dumps(response, indent=4))
        sys.exit(1)
