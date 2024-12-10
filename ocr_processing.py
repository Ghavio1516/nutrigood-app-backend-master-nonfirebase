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

# Variasi teks untuk Sugars
sugar_variations = [
    'Gula', 'Sugars', 'Sucrose', 'Fructose', 'Glucose', 'Lactose',
    'Maltose', 'High fructose corn syrup', 'Brown Sugar', 'Powdered Sugar',
    'Invert Sugar', 'Dextrose', 'Honey', 'Molasses', 'Agave', 'Agave Syrup',
    'Syrup', 'Barley Malt', 'Cane Sugar', 'Coconut Sugar', 'Palm Sugar',
    'Maple Syrup', 'Rice Syrup', 'Muscovado', 'Caramel', 'Turbinado Sugar',
    'Raw Sugar'
]

# Variasi teks untuk Sajian per Kemasan
serving_variations = [
    'Sajian per kemasan', 'Serving per container', 'Servings per container',
    'Sajian perkemasan', 'Serving per pack', 'Serving perpack',
    'Serving per package', 'Serving perpackage', 'Jumlah sajian', 
    'Takaran saji', 'Takaran saji per kemasan', 'Jumlah Porsi'
]

# Fungsi untuk ekstraksi teks dari gambar
def extract_text_from_image(image_path):
    try:
        results = ocr.ocr(image_path, cls=True)
        full_text = "\n".join([line[1][0] for line in results[0]])
        if full_text.strip():
            logging.info(f"Teks hasil OCR:\n{full_text.strip()}")
        else:
            logging.warning("Teks hasil OCR kosong.")
        return full_text.strip()
    except Exception as e:
        logging.error(f"Error saat ekstraksi teks OCR: {str(e)}")
        raise

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    try:
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
                found_value = match.group(1) or match.group(4) if key == "Sajian per kemasan" else match.group(2)
                if found_value:
                    nutrition_data[key] = found_value.strip()
                    logging.info(f"{key} ditemukan: {nutrition_data[key]}")
                else:
                    logging.warning(f"Tidak ditemukan nilai untuk {key}.")
            else:
                logging.warning(f"Tidak ditemukan data untuk {key}.")

        # Tetapkan nilai default untuk "Sajian per kemasan"
        if "Sajian per kemasan" not in nutrition_data or nutrition_data["Sajian per kemasan"] is None:
            logging.warning("Sajian per kemasan tidak ditemukan! Menggunakan nilai default 1.")
            nutrition_data["Sajian per kemasan"] = "1"

        # Periksa apakah Sugars ditemukan
        if not nutrition_data.get("Sugars"):
            logging.error("Sugars tidak ditemukan dalam teks hasil OCR.")
            raise ValueError("Sugars tidak ditemukan. Tidak dapat melanjutkan proses.")

        # Hitung Total Sugar
        sugar_value = float(re.search(r"[\d.]+", nutrition_data["Sugars"]).group())
        serving_count = int(nutrition_data["Sajian per kemasan"])
        nutrition_data["Total Sugar"] = f"{sugar_value * serving_count:.2f} g"
        logging.info(f"Total Sugar dihitung: {nutrition_data['Total Sugar']}")

        return nutrition_data

    except Exception as e:
        logging.error(f"Error saat parsing data nutrisi: {str(e)}")
        raise

# Fungsi untuk membersihkan nilai nutrisi
def clean_float(value):
    try:
        return float(re.sub(r'[^\d.]+', '', str(value)))
    except ValueError:
        raise ValueError(f"Gagal konversi nilai input: {value}")

# Prediksi model TensorFlow
def predict_nutrition_category(nutrition_data):
    try:
        model_path = './model/analisis-nutrisi.h5'
        model = tf.keras.models.load_model(model_path)
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

        # Bersihkan input data
        serving_per_container = clean_float(nutrition_data["Sajian per kemasan"])
        sugars = clean_float(nutrition_data["Sugars"])
        total_sugar = clean_float(nutrition_data["Total Sugar"])

        input_tensor = tf.convert_to_tensor([[serving_per_container, sugars, total_sugar]])
        predictions = model.predict(input_tensor)[0]

        return {
            "Kategori Gula": "Tinggi" if predictions[0] > 0.5 else "Rendah",
            "Rekomendasi": "Kurangi konsumsi" if predictions[1] > 0.5 else "Aman dikonsumsi"
        }

    except Exception as e:
        logging.error(f"Error saat prediksi model TensorFlow: {str(e)}")
        raise

# Fungsi utama
if __name__ == "__main__":
    try:
        image_path = sys.argv[1]
        extracted_text = extract_text_from_image(image_path)

        # Parsing Nutrisi
        try:
            nutrition_info = parse_nutrition_info(extracted_text)
        except Exception as e:
            nutrition_info = {"OCR Result": extracted_text, "Error": str(e)}
            response = {"message": "OCR berhasil tetapi parsing gagal", "nutrition_info": nutrition_info}
            print(json.dumps(response, indent=4))
            sys.exit(1)

        # Prediksi Model
        try:
            predictions = predict_nutrition_category(nutrition_info)
            nutrition_info.update(predictions)
            response = {"message": "Berhasil", "nutrition_info": nutrition_info}
        except Exception as e:
            logging.error(f"Error saat menjalankan model TensorFlow: {str(e)}")
            response = {
                "message": "OCR berhasil tetapi prediksi gagal",
                "nutrition_info": nutrition_info,
                "Error": str(e)
            }

        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error tidak terduga: {str(e)}")
        print(json.dumps({"message": f"Error tidak terduga: {str(e)}", "nutrition_info": {}}, indent=4))
