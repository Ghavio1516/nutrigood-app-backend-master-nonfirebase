from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from PIL import Image
import cv2
import numpy as np
import re
import json
import os
import logging

# Nonaktifkan GPU jika tidak tersedia
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load TrOCR Model dan Processor
def load_model():
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
    model = TrOCRForConditionalGeneration.from_pretrained("microsoft/trocr-base-printed")
    return processor, model

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
def extract_text_from_block(processor, model, image):
    processed_image = preprocess_image(image)
    
    # Menggunakan TrOCR untuk OCR
    # Menggunakan PIL image untuk TrOCR
    pil_image = Image.fromarray(processed_image)

    # Mengonversi gambar menjadi teks menggunakan TrOCR
    inputs = processor(pil_image, return_tensors="pt")
    generated_ids = model.generate(inputs["pixel_values"])
    text = processor.decode(generated_ids[0], skip_special_tokens=True)

    return text.strip()

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
        'Sugar': 'Sugars',
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
        'Serving Size': r'(Serving\s*Size|Takaran\s*Saji)[:\-\s]*(\d+g|\d+ml|\d+\s*(serving|portion))',  # Membuat lebih fleksibel
        'Total Fat': r'(Total\s*Fat|Lemak\s*total)[:\-\s]*(\d+g|\d+ml)',  # Menambahkan fleksibilitas pada satuan
        'Saturated Fat': r'(Saturated\s*Fat|Lemak\s*jenuh)[:\-\s]*(\d+g|\d+ml)',  # Menambahkan fleksibilitas pada satuan
        'Cholesterol': r'(Cholesterol)[:\-\s]*(\d+mg)',  # Menangkap nilai mg
        'Sodium': r'(Sodium|Garam)[:\-\s]*(\d+mg)',  # Menangkap nilai mg
        'Protein': r'(Protein)[:\-\s]*(\d+g)',  # Menangkap nilai g
        'Calories': r'Calories[:\-\s]*(\d+)',  # Menangkap Calories tanpa satuan
        'Sugars': r'(Total\s*Sugars|Sugars|Added\s*Sugars|Sugar|Gula)[:\-\s]*(\d+\s*g|\d+\s*mg|\d+\s*9)',  # Menambahkan fleksibilitas untuk "10g Added Sugar"
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

        # Load the TrOCR model and processor
        processor, model = load_model()

        # Ekstraksi teks dari gambar menggunakan TrOCR
        story_text = extract_text_from_block(processor, model, image)
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

    except Exception as e:
        logging.error("Error: %s", str(e))
        sys.exit(1)
