import os
import cv2
import re
import json
import sys
import logging
import tensorflow as tf
from paddleocr import PaddleOCR

# Paksa TensorFlow hanya menggunakan CPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

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
    'Serving per package', 'Serving perpackage', 'Jumlah sajian', 
    'Takaran saji', 'Takaran saji per kemasan', 'Jumlah Porsi'
]

# Fungsi untuk ekstraksi teks dari gambar
def extract_text_from_image(image_path):
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])

    if full_text.strip():
        logging.info(f"Teks hasil OCR:\n{full_text.strip()}")
    else:
        logging.warning("Teks hasil OCR kosong.")
    
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
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
                nutrition_data[key] = found_value.strip()
                logging.info(f"{key} ditemukan: {nutrition_data[key]}")
            else:
                logging.warning(f"Tidak ditemukan nilai untuk {key}.")
        else:
            logging.warning(f"Tidak ditemukan data untuk {key}.")

    # Tetapkan nilai default hanya untuk "Sajian per kemasan"
    if "Sajian per kemasan" not in nutrition_data or nutrition_data["Sajian per kemasan"] is None:
        logging.warning("Sajian per kemasan tidak ditemukan! Menggunakan nilai default 1.")
        nutrition_data["Sajian per kemasan"] = 1

    # Periksa apakah Sugars ditemukan
    if not nutrition_data.get("Sugars"):
        logging.error("Sugars tidak ditemukan dalam teks hasil OCR.")
        raise ValueError("Sugars tidak ditemukan. Tidak dapat melanjutkan proses.")

    # Hitung Total Sugar
    try:
        sugar_value = float(re.search(r"[\d.]+", nutrition_data["Sugars"]).group())
        serving_count = int(nutrition_data["Sajian per kemasan"])
        nutrition_data["Total Sugar"] = f"{sugar_value * serving_count:.2f} g"
        logging.info(f"Total Sugar dihitung: {nutrition_data['Total Sugar']}")
    except (ValueError, AttributeError):
        logging.error("Tidak dapat menghitung Total Sugar.")
        raise ValueError("Total Sugar tidak dapat dihitung. Tidak dapat melanjutkan proses.")

    return nutrition_data

# Prediksi model TensorFlow
def predict_nutrition_category(nutrition_data):
    model_path = './model/analisis-nutrisi.h5'
    model = tf.keras.models.load_model(model_path)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Fungsi untuk membersihkan nilai nutrisi
    def clean_float(value):
        try:
            return float(re.sub(r'[^\d.]+', '', value))
        except ValueError:
            raise ValueError(f"Gagal konversi nilai input: {value}")

    # Bersihkan input data sebelum digunakan
    try:
        serving_per_container = clean_float(nutrition_data["Sajian per kemasan"])
        sugars = clean_float(nutrition_data["Sugars"])
        total_sugar = clean_float(nutrition_data["Total Sugar"])
    except ValueError as e:
        raise ValueError(f"Gagal konversi nilai input: {e}")

    # Konversi data menjadi Tensor
    input_tensor = tf.convert_to_tensor([[serving_per_container, sugars, total_sugar]])

    # Prediksi menggunakan model
    predictions = model.predict(input_tensor)[0]
    return {
        "Kategori Gula": "Tinggi" if predictions[0] > 0.5 else "Rendah",
        "Rekomendasi": "Kurangi konsumsi" if predictions[1] > 0.5 else "Aman dikonsumsi"
    }

# Fungsi utama
if __name__ == "__main__":
    try:
        image_path = sys.argv[1]
        extracted_text = extract_text_from_image(image_path)
        nutrition_info = parse_nutrition_info(extracted_text)

        # Jika parsing berhasil, jalankan prediksi
        if "Sugars" in nutrition_info and "Total Sugar" in nutrition_info:
            predictions = predict_nutrition_category(nutrition_info)
            nutrition_info.update(predictions)
            response = {"message": "Berhasil", "nutrition_info": nutrition_info}
        else:
            response = {"message": "Data nutrisi tidak lengkap. Tidak dapat melanjutkan proses.", "nutrition_info": {}}

        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        print(json.dumps({"message": f"Error: {str(e)}", "nutrition_info": {}}, indent=4))
