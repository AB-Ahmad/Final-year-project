import cv2
import numpy as np

# Load and resize image
image_path = "photo_2025-07-22_18-37-12.jpg"
image = cv2.imread(image_path)
scale = 1000 / image.shape[1]
image = cv2.resize(image, None, fx=scale, fy=scale)

# Convert to grayscale and threshold
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 15, 10)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Approximate and collect rectangular contours
rects = []
for cnt in contours:
    epsilon = 0.02 * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(approx)
        area = w * h
        aspect = w / h
        rects.append((x, y, w, h, area, aspect))

# Filter out very small or huge contours
rects = [r for r in rects if r[4] > 10000]

# Sort by area descending
rects = sorted(rects, key=lambda r: r[4], reverse=True)

# Assign boxes
reg_box = None
q1_15_box = None
q16_30_box = None

# Find the two largest tall boxes (answer zones)
tall_boxes = [r for r in rects if r[3] > r[2] * 1.2]  # height significantly > width
tall_boxes = sorted(tall_boxes, key=lambda r: r[0])   # sort by x (left to right)

if len(tall_boxes) >= 2:
    q1_15_box = tall_boxes[0][:4]
    q16_30_box = tall_boxes[1][:4]

# Registration box: among remaining, choose one near top with moderate area
top_boxes = [r for r in rects if r not in tall_boxes and r[3] < r[2] * 1.2]  # flatter box
if top_boxes:
    reg_box = sorted(top_boxes, key=lambda r: r[1])[0][:4]

# Save crops
def save_crop(box, name):
    if box is not None:
        x, y, w, h = map(int, box)
        crop = image[y:y + h, x:x + w]
        cv2.imwrite(name, crop)
        print(f"Saved: {name}")
    else:
        print(f"{name} not found!")

save_crop(reg_box, "reg_box.jpg")
save_crop(q1_15_box, "q1_15_box.jpg")
save_crop(q16_30_box, "q16_30_box.jpg")

# Visualization
vis = image.copy()
for box, color in [(reg_box, (0, 255, 0)), (q1_15_box, (255, 0, 0)), (q16_30_box, (0, 255, 255))]:
    if box is not None:
        x, y, w, h = map(int, box)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 3)

cv2.imwrite("detected_boxes.jpg", vis)
print("Saved: detected_boxes.jpg (visualization)")
