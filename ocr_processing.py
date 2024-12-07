import pytesseract
import cv2
import numpy as np
import tensorflow as tf
import re
import json
import os
import logging

# Nonaktifkan GPU jika tidak tersedia
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konfigurasi path Tesseract di Ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Load the custom trained model
def load_model():
    model_path = 'my_model_best_model.h5'
    model = tf.keras.models.load_model(model_path)
    return model

# Mengonversi gambar menjadi grayscale
def convert_2_gray(image):
    if image is None:
        raise ValueError("Gambar tidak ditemukan atau tidak valid.")
    if len(image.shape) == 3:  # Hanya konversi jika gambar memiliki 3 channel
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

# Binarisasi gambar menggunakan Otsu
def binarization(image):
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return thresh

# Menemukan blok teks
def find_text_blocks(image):
    binary_image = binarization(image)  # Binarisasi gambar
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blocks = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 50 and h > 20:  # Hanya blok teks yang cukup besar
            blocks.append([x, y, w, h])

    # Urutkan blok teks berdasarkan posisi top-to-bottom, left-to-right
    blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
    return blocks

# Koreksi rotasi gambar
def deskew_image(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed

# Preprocessing lengkap untuk OCR
def preprocess_image(image):
    gray = convert_2_gray(image)
    deskewed = deskew_image(gray)
    binary = binarization(deskewed)
    return binary

# Ekstraksi teks dari blok
def extract_text_from_block(image):
    processed_image = preprocess_image(image)
    text_blocks = find_text_blocks(processed_image)
    
    if not text_blocks:
        return "No text found."

    full_text = ""
    for block in text_blocks:
        x, y, w, h = block
        block_img = image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(block_img, config='--psm 6')  # Mode untuk blok teks
        full_text += text.strip() + "\n"

    return full_text.strip()

# Fungsi untuk membersihkan teks hasil OCR
def clean_text(ocr_text):
    # Hapus karakter yang tidak relevan
    clean_text = re.sub(r'[^\w\s%:,.()/-]', '', ocr_text)
    # Hapus spasi berlebih
    clean_text = re.sub(r'\s{2,}', ' ', clean_text)
    # Ganti variasi kata yang dikenal
    replacements = {
        'Energitotal': 'Energi total',
        'Lemaktotal': 'Lemak total',
        'Takaran Saji': 'Serving Size',
        'natrium': 'Sodium',
        'Kalori': 'Calories',
        'Gula': 'Sugars',
        'TotalSugar': 'Total Sugars',

        # Variasi gula
        'Sugars': 'Sugars',
        'Gula': 'Sugars',
        'Sucrose': 'Sugars',
        'Fructose': 'Sugars',
        'Glucose': 'Sugars',
        'Lactose': 'Sugars',
        'Maltose': 'Sugars',
        'High fructose corn syrup': 'Sugars',
        'Gula Pasir': 'Sugars',
        'Gula Kelapa': 'Sugars',
        'Gula Aren': 'Sugars',
        'Gula Merah': 'Sugars',
        'Gola/Sugar': 'Sugars',
        # Tambahan variasi gula
        'Corn Syrup': 'Sugars',
        'Brown Sugar': 'Sugars',
        'Powdered Sugar': 'Sugars',
        'Invert Sugar': 'Sugars',
        'Dextrose': 'Sugars',
        'Honey': 'Sugars',
        'Molasses': 'Sugars',
        'Agave': 'Sugars',
        'Agave Syrup': 'Sugars',
        'Syrup': 'Sugars',
        'Barley Malt': 'Sugars',
        'Cane Sugar': 'Sugars',
        'Coconut Sugar': 'Sugars',
        'Palm Sugar': 'Sugars',
        'Maple Syrup': 'Sugars',
        'Rice Syrup': 'Sugars',
        'Muscovado': 'Sugars',
        'Caramel': 'Sugars',
        'Turbinado Sugar': 'Sugars',
        'Raw Sugar': 'Sugars'  # Menambahkan variasi lain
    }
    for old, new in replacements.items():
        clean_text = clean_text.replace(old, new)
    return clean_text.strip()

# Fungsi untuk parsing informasi nutrisi
def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    patterns = {
        'Serving Size': r'(?i)(?:\b(?:\d+)\s)?(?:sajian\sper\skemasan|servings\sper\scontainer)[:\s]*(\d+)',
        'Total Fat': r'(Total\s*Fat|Lemak\s*total)[:\-\s]*(\d+g|\d+ml)',  # Menambahkan fleksibilitas pada satuan
        'Saturated Fat': r'(Saturated\s*Fat|Lemak\s*jenuh)[:\-\s]*(\d+g|\d+ml)',  # Menambahkan fleksibilitas pada satuan
        'Cholesterol': r'(Cholesterol)[:\-\s]*(\d+mg)',  # Menangkap nilai mg
        'Sodium': r'(Sodium|Garam)[:\-\s]*(\d+mg)',  # Menangkap nilai mg
        'Protein': r'(Protein)[:\-\s]*(\d+g)',  # Menangkap nilai g
        'Calories': r'Calories[:\-\s]*(\d+)',  # Menangkap Calories tanpa satuan
        'Sugars': r'(Total\s*Sugars|Sugars|Added\s*Sugars|Sugar|Gula)[:\-\s]*(\d+\s*g|\d+\s*mg)',  # Menambahkan fleksibilitas untuk "10g Added Sugar"
    }

    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            if match:
                nutrition_data[key] = match.group(2).strip()  # Tambahkan strip() untuk menghapus spasi ekstra
                logging.info(f"Match found for {key}: {match.group(2)}")
            else:
                logging.warning(f"No match found for {key} using pattern {pattern}")
        except Exception as e:
            logging.error(f"Error processing key {key}: {str(e)}")

    return nutrition_data

# Fungsi utama untuk memproses gambar dan mengembalikan informasi nutrisi
if __name__ == "__main__":
    import sys

    try:
        if len(sys.argv) < 2:
            raise ValueError("Path gambar harus diberikan sebagai argumen.")
        
        image_path = sys.argv[1]
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")
        
        logging.info("Memproses gambar: %s", image_path)

        # Ekstraksi teks dari gambar
        story_text = extract_text_from_block(image)
        logging.info("Teks hasil OCR:\n%s", story_text)

        # Membersihkan teks hasil OCR
        cleaned_text = clean_text(story_text)
        logging.info("Teks setelah dibersihkan:\n%s", cleaned_text)

        # Parsing informasi nutrisi
        try:
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

            print(json.dumps(response, indent=4))
        except Exception as e:
            logging.error("Error saat memproses teks: %s", str(e))
            response = {
                "message": "Error saat memproses gambar",
                "nutrition_info": {}
            }
            print(json.dumps(response, indent=4))
            sys.exit(1)


        # # Output dalam format JSON
        # output_data = {
        #     "Extracted Text": cleaned_text,
        #     "Nutrition Information": nutrition_info
        # }
        # print("Output:", json.dumps(output_data, indent=4))

    except Exception as e:
        logging.error("Error: %s", str(e))
        sys.exit(1)
