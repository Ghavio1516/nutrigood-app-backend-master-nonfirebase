import cv2
import re
import json
import sys
import logging
from paddleocr import PaddleOCR

# Konfigurasi logging ke stderr
logging.basicConfig(
    level=logging.ERROR,  # Hanya log error penting
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Inisialisasi PaddleOCR dengan log dinonaktifkan
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    show_log=False  # Nonaktifkan log PaddleOCR
)

# Variasi teks untuk pencarian
sugar_variations = [
    'Gula', 'Sugars', 'Sucrose', 'Fructose', 'Glucose', 'Lactose',
    'Maltose', 'High fructose corn syrup', 'Brown Sugar', 'Powdered Sugar',
    'Invert Sugar', 'Dextrose', 'Honey', 'Molasses', 'Agave', 'Agave Syrup',
    'Syrup', 'Barley Malt', 'Cane Sugar', 'Coconut Sugar', 'Palm Sugar',
    'Maple Syrup', 'Rice Syrup', 'Muscovado', 'Caramel', 'Turbinado Sugar',
    'Raw Sugar'
]

serving_variations = [
    'Sajian per kemasan', 'Sajian perkemasan', 'Serving per pack', 'Serving perpack',
    'Serving per package', 'Serving perpackage', 'Servings Per Container', 
    'Servings Per Container about', 'Sajian perkemasan/Serving per pack',
    'Porsi per kemasan', 'Porsi per sajian', 'Porsi perpack', 'Porsi per package',
    'Takaran saji', 'Takaran saji per kemasan', 'Takaran saji per pack', 
    'Takaran saji per sajian', 'Serving Size', 'Per Serving', 
    'Per Package', 'Each Package', 'Each Serving', 'Portion Size',
    'Jumlah porsi', 'Jumlah sajian', 'Portion per Container', 
    'Portion per Pack', 'Portion per Package', 'Porsi per wadah', 
    'Jumlah Porsi', 'Total Servings'
]

# Fungsi untuk ekstraksi teks
def extract_text_from_image(image_path):
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])
    return full_text.strip()

# Parsing teks hasil OCR
def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)

    patterns = {
        'Sajian per kemasan': rf'({serving_pattern})[:\-\s]*(\d+)',
        'Sugars': rf'({sugar_pattern})[:\-\s]*(\d+\s*[gG]|mg)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            nutrition_data[key] = match.group(2).strip()

    # Tetapkan nilai default jika "Sajian per kemasan" tidak ditemukan
    serving_count = int(nutrition_data.get("Sajian per kemasan", 1))

    # Hitung Total Sugar jika tersedia
    sugar_value = nutrition_data.get("Sugars")
    if sugar_value:
        sugar_value = float(re.search(r"[\d.]+", sugar_value).group())
        nutrition_data["Total Sugar"] = f"{sugar_value * serving_count:.2f} g"

    return nutrition_data

# Fungsi utama
if __name__ == "__main__":
    try:
        # Path gambar dari argumen
        image_path = sys.argv[1]
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")

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
        # Log error ke stderr
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "nutrition_info": {}}
        print(json.dumps(response, indent=4))
        sys.exit(1)
