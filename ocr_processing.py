import cv2
import re
import json
import logging
import sys
from paddleocr import PaddleOCR

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inisialisasi PaddleOCR
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en'  # Menggunakan model bahasa Inggris
)

# Variasi teks untuk "Sugars" dan "Sajian per Kemasan"
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

# Ekstraksi teks dari gambar menggunakan PaddleOCR
def extract_text_from_image(image_path):
    results = ocr.ocr(image_path, cls=True)
    full_text = "\n".join([line[1][0] for line in results[0]])
    logging.info(f"Hasil OCR Ekstraksi:\n{full_text}")
    return full_text.strip()

# Membersihkan teks hasil OCR
def clean_text(ocr_text):
    replacements = {
        'Energitotal': 'Energi total',
        'Lemaktotal': 'Lemak total',
        'Takaran Saji': 'Serving Size',
        'natrium': 'Sodium',
        'Kalori': 'Calories',
    }
    for old, new in replacements.items():
        ocr_text = ocr_text.replace(old, new)
    return ocr_text.strip()

# Parsing informasi nutrisi dan menghitung Total Sugar
def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    sugar_pattern = '|'.join(re.escape(variation) for variation in sugar_variations)
    serving_pattern = '|'.join(re.escape(variation) for variation in serving_variations)
    patterns = {
        'Sajian per kemasan': rf'({serving_pattern})[:\-\s]*(\d+)',
        'Sugars': rf'({sugar_pattern})[:\-\s]*(\d+\s*[gG]|mg)'
    }

    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                nutrition_data[key] = match.group(2).strip()
                logging.info(f"Match found for {key}: {match.group(2)}")
            else:
                logging.warning(f"No match found for {key} using pattern {pattern}")
        except Exception as e:
            logging.error(f"Error processing key {key}: {str(e)}")

    # Gunakan nilai default 1 jika "Sajian per kemasan" tidak ditemukan
    serving_count = nutrition_data.get("Sajian per kemasan")
    if not serving_count:
        logging.warning("Serving size tidak ditemukan, menggunakan nilai default 1.")
        serving_count = 1
    else:
        serving_count = int(serving_count)

    # Hitung Total Sugar
    try:
        sugar_value = nutrition_data.get("Sugars")
        if sugar_value:
            sugar_value = float(re.search(r"[\d.]+", sugar_value).group())
            total_sugar = sugar_value * serving_count
            nutrition_data["Total Sugar"] = f"{total_sugar:.2f} g"  # Tambahkan Total Sugar
        else:
            logging.warning("Gula tidak ditemukan, Total Sugar tidak dapat dihitung.")
    except Exception as e:
        logging.error(f"Error calculating Total Sugar: {str(e)}")

    return nutrition_data

# Fungsi utama untuk memproses gambar dan mengembalikan informasi nutrisi
if __name__ == "__main__":
    try:
        # Path gambar eksplisit
        image_path = sys.argv[1]  # Path diambil dari argumen command line
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")

        logging.info("Memproses gambar: %s", image_path)

        # Ekstraksi teks dari gambar
        extracted_text = extract_text_from_image(image_path)
        logging.info("Teks hasil OCR:\n%s", extracted_text)

        # Membersihkan teks hasil OCR
        cleaned_text = clean_text(extracted_text)
        logging.info("Teks setelah dibersihkan:\n%s", cleaned_text)

        # Parsing informasi nutrisi
        nutrition_info = parse_nutrition_info(cleaned_text)
        if not nutrition_info:  # Jika dictionary kosong
            logging.warning("Tidak ditemukan informasi nutrisi yang valid dalam teks.")
            response = {
                "message": "Tidak ditemukan",
                "nutrition_info": {}
            }
        else:
            response = {
                "message": "Berhasil",
                "nutrition_info": nutrition_info
            }

        # Output dalam format JSON
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error("Error: %s", str(e))
        sys.exit(1)
