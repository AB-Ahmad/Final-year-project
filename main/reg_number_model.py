import cv2
from ultralytics import YOLO
import numpy as np
import re

# === CONFIGURATION ===
MODEL_PATH = 'models/reg_number_model_v1.pt'
IMAGE_PATH = 'reg_Number/photo_2025-07-25_18-56-56.jpg'
CONFIDENCE_THRESHOLD = 0.2
EXPECTED_LENGTH = 9
REGEX_PATTERN = r'^U\d{2}[A-Z]{2}\d{4}$'

# === AUTO-CORRECTION LOGIC ===
def correct_character(c):
    substitutions = {
        '0': 'O', 'O': 'O',
        '1': '1', 'I': '1', 'L': '1',
        ' ': '', 'C ': 'C'
    }
    return substitutions.get(c.strip(), c.strip())

# === LOAD MODEL ===
model = YOLO(MODEL_PATH)

# === PREDICT ===
results = model.predict(IMAGE_PATH, conf=CONFIDENCE_THRESHOLD, imgsz=640)[0]

# === EXTRACT RESULTS ===
boxes = results.boxes.xyxy.cpu().numpy()
confs = results.boxes.conf.cpu().numpy()
classes = results.boxes.cls.cpu().numpy()
class_names = model.names

# === SELECT TOP 9 DETECTIONS ===
detections = list(zip(boxes, classes, confs))
detections = sorted(detections, key=lambda x: x[2], reverse=True)[:EXPECTED_LENGTH]
detections = sorted(detections, key=lambda x: x[0][0])  # sort by x1 (left position)

# === COMPILE RAW AND CORRECTED CHARACTERS ===
raw_chars = [class_names[int(cls)].strip().upper() for _, cls, _ in detections]
corrected_chars = [correct_character(c) for c in raw_chars]
reg_number = ''.join(corrected_chars)

# === VALIDATE FORMAT ===
print(f"\n🔎 Raw prediction: {''.join(raw_chars)}")
print(f"✅ Corrected Reg Number: {reg_number}")

if re.fullmatch(REGEX_PATTERN, reg_number):
    print("🎉 Valid Registration Number Format")
else:
    print("⚠️ Warning: Format does not match expected pattern")

# === DRAW RESULTS ON IMAGE ===
image = cv2.imread(IMAGE_PATH)
for box, cls, conf in detections:
    x1, y1, x2, y2 = map(int, box)
    label = class_names[int(cls)]
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

cv2.imwrite('reg_output.jpg', image)
