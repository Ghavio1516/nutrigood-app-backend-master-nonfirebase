# import sys
# import json
# import cv2
# import numpy as np
# import os
# import tensorflow as tf

# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# tf.get_logger().setLevel('ERROR')

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# def load_model():
#     model_path = "/home/ghavio_rizky_ananda_budiawan_tik/nutrigood-app-backend-master-nonfirebase/model/CustomCnn_model.keras"
#     return tf.keras.models.load_model(model_path)

# def preprocess_image(image_path):
#     image = cv2.imread(image_path)
#     if image is None:
#         raise ValueError("Image not found or invalid.")
    
#     image = cv2.resize(image, (32, 32)) 
#     image = image.astype('float32') / 255.0 
#     image = np.expand_dims(image, axis=0) 
#     return image

# if __name__ == '__main__':
#     try:
#         image_path = sys.argv[1]

#         model = load_model()

#         input_tensor = preprocess_image(image_path)

#         predictions = model.predict(input_tensor)

#         predictions_json = predictions.tolist()

#         print(f"Output : {json.dumps(predictions_json)}")

#     except Exception as e:
#         sys.stderr.write(f"Error: {e}")
#         sys.exit(1)


# Load the custom trained model
import pytesseract
import cv2
import numpy as np
import tensorflow as tf
import re
import json
import sys

# Konfigurasi path Tesseract di Ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Fungsi untuk memuat model kustom
def load_model():
    model_path = '/home/ghavio_rizky_ananda_budiawan_tik/nutrigood-app-backend-master-nonfirebase/model/my_model_best_model.h5'
    model = tf.keras.models.load_model(model_path)
    return model

# Fungsi preprocessing
def convert_2_gray(image):
    if image is None:
        raise ValueError("Gambar tidak ditemukan atau tidak valid.")
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def binarization(image):
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return thresh

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

def preprocess_image(image):
    gray = convert_2_gray(image)
    deskewed = deskew_image(gray)
    binary = binarization(deskewed)
    return binary

# Fungsi OCR
def find_text_blocks(image):
    binary_image = binarization(image)
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blocks = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 50 and h > 20:
            blocks.append([x, y, w, h])
    blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
    return blocks

def extract_text_from_block(image):
    processed_image = preprocess_image(image)
    text_blocks = find_text_blocks(processed_image)
    if not text_blocks:
        return "No text found."
    full_text = ""
    for block in text_blocks:
        x, y, w, h = block
        block_img = image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(block_img, config='--psm 6')
        full_text += text.strip() + "\n"
    return full_text.strip()

def read_story_text(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Tidak dapat membaca gambar dari path yang diberikan.")
    text = extract_text_from_block(image)
    return text

def parse_nutrition_info(extracted_text):
    nutrition_data = {}
    serving_size = re.search(r'Serving Size|Takaran Saji\s*[:\-\s]*([0-9]+g)', extracted_text, re.IGNORECASE)
    calories = re.search(r'Calories\s*[:\-\s]*([0-9]+)', extracted_text, re.IGNORECASE)
    if serving_size:
        nutrition_data['Serving Size'] = serving_size.group(1)
    if calories:
        nutrition_data['Calories'] = int(calories.group(1))
    return nutrition_data

# Main script untuk dipanggil dari backend
if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError("Path gambar harus diberikan sebagai argumen.")
        image_path = sys.argv[1]
        story_text = read_story_text(image_path)
        print("Extracted Text:", story_text)
        nutrition_info = parse_nutrition_info(story_text)
        print("Output:", json.dumps(nutrition_info, indent=4))
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
