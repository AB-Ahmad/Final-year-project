import os
import cv2
import numpy as np

# Configuration
LABEL_DIR = r"C:\Users\Ahmad Bala\runs\detect\predict\labels"
IMAGE_DIR = r"C:\Users\Ahmad Bala\Desktop\MCQ PJ\mcq-grading.v2i.yolov8\test\images"

# Answer key
answer_key = {
    f"q{i}": opt for i, opt in zip(range(1, 31), 
    ["a", "a", "a", "d", "e",  # q1 - q5
     "a", "b", "c", "d", "e",  # q6 - q10
     "a", "b", "c", "d", "e",  # q11 - q15
     "a", "b", "a", "d", "e",  # q16 - q20
     "a", "b", "d", "d", "e",  # q21 - q25
     "a", "b", "e", "d", "e"   # q26 - q30
])}


# Detect the top and bottom zones using contour analysis
def detect_answer_zones(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edged = cv2.Canny(blurred, 30, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = h / float(w)
        if area > 10000 and 0.5 < aspect < 2.0:
            boxes.append((x, y, x+w, y+h))

    boxes = sorted(boxes, key=lambda b: b[1])  # sort top to bottom
    if len(boxes) >= 2:
        return boxes[:2]  # return top two zones
    return []

# Get question and option from a detected bubble
def get_question_option(x, y, zone, zone_index):
    x1, y1, x2, y2 = zone
    zone_h = y2 - y1
    zone_w = x2 - x1

    row_height = zone_h / 15
    col_width = zone_w / 5

    rel_x = x - x1
    rel_y = y - y1

    row = int(rel_y / row_height)
    col = int(rel_x / col_width)

    question_num = row + (1 if zone_index == 0 else 16)
    option = ["a", "b", "c", "d", "e"][min(col, 4)]
    return f"q{question_num}", option

# Grade a student from YOLO label and image
def grade_student(label_path, image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"⚠️ Could not load image: {image_path}")
        return 0, {}

    zones = detect_answer_zones(image)
    if len(zones) != 2:
        print(f"⚠️ Could not detect two answer zones in {image_path}")
        return 0, {}

    zones = sorted(zones, key=lambda z: z[1])  # top-to-bottom

    h, w = image.shape[:2]
    selections = {}

    with open(label_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        _, x_c, y_c, _, _ = map(float, parts)
        x = int(x_c * w)
        y = int(y_c * h)

        for i, zone in enumerate(zones):
            if zone[1] <= y <= zone[3] and zone[0] <= x <= zone[2]:
                q, opt = get_question_option(x, y, zone, i)
                selections.setdefault(q, []).append(opt)

    # Grade logic
    score = 0
    detailed = {}
    for q in answer_key:
        opts = selections.get(q, [])
        if len(opts) == 1:
            if opts[0] == answer_key[q]:
                detailed[q] = "✔"
                score += 1
            else:
                detailed[q] = "✘"
        elif len(opts) == 0:
            detailed[q] = "○"
        else:
            detailed[q] = "✘"

    return score, detailed

# Main
if __name__ == "__main__":
    for label_file in os.listdir(LABEL_DIR):
        if not label_file.endswith(".txt"):
            continue

        student_id = label_file.replace(".txt", "")
        label_path = os.path.join(LABEL_DIR, label_file)
        image_path = os.path.join(IMAGE_DIR, student_id + ".jpg")

        if not os.path.exists(image_path):
            print(f"⚠️ Image not found for {student_id}")
            continue

        score, report = grade_student(label_path, image_path)

        print(f"\n🧑 Student: {student_id}.jpg")
        print(f"✅ Score: {score}/30")
        print("📋 Detail:", report)


































































    















































































































