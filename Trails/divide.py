import cv2
import numpy as np

# Load the cropped q1_15_box image
q1_15_path = "q16_30_box.jpg"
img = cv2.imread(q1_15_path)

# Get image dimensions
h, w = img.shape[:2]

# Draw 15 evenly spaced horizontal lines
num_questions = 15
step = h / num_questions

for i in range(1, num_questions):  # skip 0 and h to not draw on edges
    y = int(i * step)
    cv2.line(img, (0, y), (w, y), (0, 0, 255), 2)  # red lines

# Save and display
cv2.imwrite("q1_30_divided.jpg", img)
print("Saved: q1_15_divided.jpg with 15 horizontal divisions")
