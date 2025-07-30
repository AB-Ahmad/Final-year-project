import cv2
import numpy as np

# === CONFIG ===
img_path = r"mcq-grading.v2i.yolov8/test/images/sheet08_jpg.rf.422227d46a4e2e67325f08dea3662294.jpg"
output_path = "zones_detected.jpg"

# === LOAD IMAGE ===
image = cv2.imread(img_path)
if image is None:
    print("❌ Could not load image.")
    exit()

orig = image.copy()
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# === PREPROCESS ===
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 50, 150)

# === FIND CONTOURS ===
contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

zones = []

# === FILTER CONTOURS ===
for cnt in contours:
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)
    aspect = w / h if h != 0 else 0

    if area > 50000 and 0.4 < aspect < 1.5:
        zones.append((y, x, w, h))

# === SORT ZONES TOP TO BOTTOM ===
zones = sorted(zones)[:2]  # Take top 2 by Y

for i, (y, x, w, h) in enumerate(zones, 1):
    cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 255, 0), 3)
    cv2.putText(orig, f"Zone {i}", (x + 10, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

# === SAVE OUTPUT ===
cv2.imwrite(output_path, orig)
print(f"✅ Detected {len(zones)} zones and saved to {output_path}")
