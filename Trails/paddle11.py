from paddleocr import PaddleOCR
import re
import cv2

# Initialize OCR model
ocr_model = PaddleOCR(use_angle_cls=True, lang='en')  # Use GPU: use_gpu=True

# Load your image (replace path)
image_path = "test/images/sheet08.jpg"
image = cv2.imread(image_path)

# Run OCR on image
results = ocr_model.ocr(image_path, cls=True)

# Extract all text
extracted_text = []
for line in results:
    for (bbox, text_info) in line:
        text, confidence = text_info
        extracted_text.append(text)

# Join all text segments
full_text = " ".join(extracted_text)

# Use regex to find registration number
reg_pattern = r"U\d{2}[A-Z]{2}\d{4,6}"
matches = re.findall(reg_pattern, full_text)

if matches:
    print("✅ Registration Number(s) Found:", matches)
else:
    print("❌ No valid registration number found.")






valid_departments = {'CO', 'EE', 'ME', 'CE', 'CS'}

valid_reg_numbers = [reg for reg in matches if reg[4:6] in valid_departments]

if valid_reg_numbers:
    print("✅ Valid Reg Numbers:", valid_reg_numbers)
else:
    print("❌ No valid department match.")












