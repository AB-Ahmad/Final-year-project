import cv2
import numpy as np
import re
from paddleocr import PaddleOCR
import matplotlib.pyplot as plt

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Use en+ for more robust results if needed

# Load the image
image_path = "sheet05.jpg"
img = cv2.imread(image_path)

# Step 1: Detect candidate region (heuristics for registration number box)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

boxes = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    aspect_ratio = w / float(h)
    if 2.0 < aspect_ratio < 6.5 and 100 < w < 500 and 30 < h < 100:
        boxes.append((x, y, w, h))

boxes = sorted(boxes, key=lambda b: b[1])  # top-to-bottom
reg_crop = None
if boxes:
    x, y, w, h = boxes[0]
    reg_crop = img[y:y+h, x:x+w]
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
else:
    print("❌ No registration box found.")
    exit()

# Optional: Show detected box
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.title("Detected Registration Area")
plt.axis('off')
plt.show()

# Step 2: Preprocess the crop
gray_crop = cv2.cvtColor(reg_crop, cv2.COLOR_BGR2GRAY)
gray_crop = cv2.equalizeHist(gray_crop)  # enhance contrast
gray_crop = cv2.bilateralFilter(gray_crop, 11, 17, 17)  # denoise
_, bin_crop = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

cv2.imwrite("reg_crop_cleaned.jpg", bin_crop)  # Optional: Save for debug

# Step 3: OCR
result = ocr.ocr(bin_crop, cls=True)

# Step 4: Extract text using regex
full_text = ''
for line in result:
    for box in line:
        text, score = box[1]
        full_text += f"{text} "

print("🔍 Raw OCR Output:", full_text.strip())

reg_pattern = r"U\d{2}[A-Z]{2}\d{4,6}"
matches = re.findall(reg_pattern, full_text.upper())

if matches:
    print("✅ Extracted Registration Number:", matches[0])
else:
    print("❌ No matching registration number found.")
