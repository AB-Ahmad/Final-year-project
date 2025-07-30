from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import cv2
import torch
import re

# Load TrOCR model and processor
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

# Load image
image_path = "sheet11.jpg"  # Make sure this file exists
image = cv2.imread(image_path)

if image is None:
    raise FileNotFoundError("Image not found. Check the path or file name.")

# Convert to grayscale and find contours
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 30, 150)

contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filter rectangular contours
rects = []
for cnt in contours:
    approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(approx)
        if 100 < w < 1000 and 30 < h < 200:  # Adjust size as needed
            rects.append((x, y, w, h))

# Sort by Y-axis to get top-most box
rects = sorted(rects, key=lambda r: r[1])

if not rects:
    raise Exception("No registration box detected!")

# Assume top-most rectangle is the reg number box
x, y, w, h = rects[0]
reg_crop = image[y:y + h, x:x + w]

# Save crop for verification
cv2.imwrite("cropped_reg_box.jpg", reg_crop)

# Preprocess crop
gray_crop = cv2.cvtColor(reg_crop, cv2.COLOR_BGR2GRAY)
_, thresh_crop = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
resized_crop = cv2.resize(thresh_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

# Convert back to 3-channel RGB (TrOCR expects RGB)
resized_rgb = cv2.cvtColor(resized_crop, cv2.COLOR_GRAY2RGB)
pil_img = Image.fromarray(resized_rgb)

# OCR with TrOCR
pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
generated_ids = model.generate(pixel_values, max_new_tokens=50)
output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

# Show result
print("📝 OCR Output:", output_text)

# Match registration number with regex
reg_pattern = r"U\d{2}[A-Z]{2}\d{4,6}"
match = re.search(reg_pattern, output_text.upper())
if match:
    print("✅ Reg Number Found:", match.group())
else:
    print("❌ No valid registration number found.")
