import json
import logging
import numpy as np
import tensorflow as tf
import sys

# Konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Fungsi untuk memuat model TensorFlow dan membuat prediksi
def analyze_with_model(sugar, serving_per_package, total_sugar, model_path):
    try:
        # Muat model
        model = tf.keras.models.load_model(model_path)
        logging.info("Model berhasil dimuat.")

        # Siapkan input
        input_data = np.array([[serving_per_package, sugar, total_sugar]])
        logging.info(f"Input data: {input_data}")

        # Lakukan prediksi
        predictions = model.predict(input_data)
        logging.info(f"Raw predictions: {predictions}")

        # Validasi bentuk output model
        if predictions.ndim == 2 and predictions.shape[1] >= 2:
            pred_kategori_gula = predictions[0][0]
            pred_rekomendasi = predictions[0][1]
        else:
            raise ValueError("Model tidak memberikan output yang diharapkan.")

        kategori_gula = "Tinggi Gula" if float(pred_kategori_gula) > 0.5 else "Rendah Gula"
        rekomendasi = "Kurangi Konsumsi" if float(pred_rekomendasi) > 0.5 else "Aman Dikonsumsi"

        return {
            "Kategori Gula": kategori_gula,
            "Rekomendasi": rekomendasi
        }

    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return {"error": "Terjadi kesalahan pada analisis model."}


# Fungsi utama untuk input data dummy
if __name__ == "__main__":
    try:
        # Pastikan path model TensorFlow tersedia
        model_path = "./model/model_3Variabel_fix.h5"

        # Input data dummy
        sugar = float(input("Masukkan jumlah gula (g): "))
        serving_per_package = int(input("Masukkan sajian per kemasan: "))
        total_sugar = float(input("Masukkan total gula (g): "))

        # Analisis menggunakan model
        analysis_result = analyze_with_model(sugar, serving_per_package, total_sugar, model_path)

        # Tampilkan hasil analisis
        response = {
            "message": "Berhasil",
            "input": {
                "Sugars": sugar,
                "Sajian per kemasan": serving_per_package,
                "Total Sugar": total_sugar,
            },
            "analysis": analysis_result,
        }
        print(json.dumps(response, indent=4))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = {"message": "Error", "input": {}, "analysis": {}}
        print(json.dumps(response, indent=4))
        sys.exit(1)
