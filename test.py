import json
import logging
import numpy as np
import tensorflow as tf
import re

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variasi teks untuk "Sugars" dan "Sajian per Kemasan"
sugar_variations = [
    'Gula', 'Sugar', 'Sugars', 'Sucrose', 'Fructose', 'Glucose', 'Lactose',
    'Maltose', 'High fructose corn syrup', 'Brown Sugar', 'Powdered Sugar',
    'Invert Sugar', 'Dextrose', 'Honey', 'Molasses', 'Agave', 'Agave Syrup',
    'Syrup', 'Barley Malt', 'Cane Sugar', 'Coconut Sugar', 'Palm Sugar',
    'Maple Syrup', 'Rice Syrup', 'Muscovado', 'Caramel', 'Turbinado Sugar',
    'Raw Sugar'
]

serving_variations = [
    'Sajian per kemasan', 'Serving per pack', 'Serving per package', 
    'Servings Per Container', 'Servings Per Container about', 'Sajian perkemasan/Serving per pack'
]

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
def parse_nutrition_info(sugar_value, serving_count):
    nutrition_data = {}
    
    # Menggunakan nilai manual untuk Sugar dan Serving per Kemasan
    try:
        # Jika sugar_value atau serving_count kosong, gunakan default 1
        sugar_value = float(sugar_value) if sugar_value else 1.0
        serving_count = int(serving_count) if serving_count else 1
        
        nutrition_data['Sugars'] = f"{sugar_value} g"
        nutrition_data['Sajian per kemasan'] = str(serving_count)

        # Hitung Total Sugar
        total_sugar = sugar_value * serving_count
        nutrition_data["Total Sugar"] = f"{total_sugar:.2f} g"
    except Exception as e:
        logging.error(f"Error processing nutrition data: {str(e)}")

    return nutrition_data

# Analisis dengan Model TensorFlow
def analyze_with_model(nutrition_info, model_path):
    try:
        model = tf.keras.models.load_model(model_path)
        
        # Siapkan input untuk model
        serving_per_package = float(nutrition_info.get("Sajian per kemasan", 1))
        sugar = float(re.search(r"[\d.]+", nutrition_info.get("Sugars", "0")).group())
        total_sugar = float(re.search(r"[\d.]+", nutrition_info.get("Total Sugar", "0")).group())

        # Cetak data yang akan dikirimkan ke model
        print("Data yang akan dikirimkan ke model:")
        input_data = np.array([[serving_per_package, sugar, total_sugar]])
        print(f"Input data array (shape: {input_data.shape}):")
        print(input_data)

        # Normalisasi input
        input_data_normalized = input_data / np.max(input_data, axis=0)

        # Cetak array yang sudah dinormalisasi
        print(f"Input data yang sudah dinormalisasi (shape: {input_data_normalized.shape}):")
        print(input_data_normalized)

        # Prediksi
        predictions = model.predict(input_data_normalized)
        
        # Periksa apakah predictions berupa list atau array
        if isinstance(predictions, list):
            predictions = np.array(predictions)  # Convert ke numpy array jika list

        # Periksa bentuk (shape) dari predictions
        print(f"Shape of predictions: {predictions.shape}")
        print(f"Predictions: {predictions}")

        # Ambil batch pertama dan squeeze hasilnya
        predictions = predictions[0]  # Ambil prediksi dari batch pertama
        predictions = predictions.squeeze()  # Menghapus dimensi ekstra

        # Periksa hasil prediksi setelah di-squeeze
        print(f"Predictions setelah squeeze: {predictions}")

        # Menggunakan probabilitas untuk menentukan kelas terbaik
        kategori_gula_prob = predictions[0]  # Probabilitas kategori gula
        rekomendasi_prob = predictions[1]  # Probabilitas rekomendasi

        # Menentukan kategori gula dan rekomendasi berdasarkan probabilitas
        kategori_gula = "Tinggi Gula" if kategori_gula_prob > 0.5 else "Rendah Gula"
        rekomendasi = "Kurangi Konsumsi" if rekomendasi_prob > 0.5 else "Aman Dikonsumsi"

        return {
            "Kategori Gula": kategori_gula,
            "Rekomendasi": rekomendasi
        }
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return {}

# Fungsi Utama
if __name__ == "__main__":
    try:
        # Input manual dari pengguna
        serving_count = input("Masukkan jumlah sajian per kemasan: ")  # Input pertama: Sajian per kemasan
        sugar_value = input("Masukkan jumlah gula per sajian (dalam gram): ")  # Input kedua: Gula per sajian

        # Parsing informasi nutrisi
        nutrition_info = parse_nutrition_info(sugar_value, serving_count)

        # Path model
        model_path = 'model/analisis-nutrisi.h5'

        # Analisis dengan model
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

        # Output dalam format JSON
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
