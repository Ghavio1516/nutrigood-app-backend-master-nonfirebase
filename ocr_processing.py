import cv2
import re
import json
import sys
import logging
from paddleocr import PaddleOCR

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
    
    # Pola pencarian dengan Regex
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)

    patterns = {
        'Sajian per kemasan': rf'([0-9]+)\s*(?:[:\-]|\s*)?\s*({serving_pattern})|({serving_pattern})\s*(?:[:\-]|\s*)?\s*([0-9]+)',
        'Sugars': rf'({sugar_pattern})\s*(?:[:\-]|\s*)?\s*([0-9]+(?:\.[0-9]+)?\s*[gG]|mg)'
    }

    # Ekstrak data nutrisi berdasarkan pola
    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            found_value = match.group(2)
            if found_value:
                nutrition_data[key] = found_value.strip()
                logging.info(f"{key} ditemukan: {nutrition_data[key]}")
            else:
                logging.warning(f"Tidak ditemukan nilai untuk {key}.")
        else:
            logging.warning(f"Tidak ditemukan data untuk {key}.")

    # Tetapkan nilai default jika "Sajian per kemasan" tidak ditemukan
    serving_count = int(nutrition_data.get("Sajian per kemasan", 1))
    if "Sajian per kemasan" not in nutrition_data:
        logging.warning("Sajian per kemasan tidak ditemukan! Menggunakan nilai default 1.")
        nutrition_data["Sajian per kemasan"] = serving_count

    # Hitung Total Sugar jika ditemukan
    if "Sugars" in nutrition_data:
        try:
            sugar_value = float(nutrition_data["Sugars"])
            nutrition_data["Total Sugar"] = f"{sugar_value * serving_count:.2f} g"
            logging.info(f"Total Sugar dihitung: {nutrition_data['Total Sugar']}")
        except (ValueError, KeyError):
            logging.error("Tidak dapat menghitung Total Sugar.")

    return nutrition_data

# Fungsi utama
if __name__ == "__main__":
    try:
        # Path gambar dari argumen
        image_path = sys.argv[1]
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")

        logging.info(f"Memproses gambar: {image_path}")

        # Ekstraksi teks dari gambar
        extracted_text = extract_text_from_image(image_path)

        # Parsing informasi nutrisi
        nutrition_info = parse_nutrition_info(extracted_text)

        # Cek hasil dan output JSON ke stdout
        if not nutrition_info:
            response = {"message": "Tidak ditemukan", "nutrition_info": {}}
        else:
            response = {"message": "Berhasil", "nutrition_info": nutrition_info}

        # Cetak JSON hanya ke stdout
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "nutrition_info": {}}
        print(json.dumps(response, indent=4))
        sys.exit(1)
