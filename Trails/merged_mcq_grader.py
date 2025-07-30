
import os
import cv2
import numpy as np

# CONFIG
LABEL_DIR = r"C:\Users\Ahmad Bala\runs\detect\predict12\labels"
IMAGE_DIR = r"C:\Users\Ahmad Bala\Desktop\MCQ PJ\mcq-grading.v2i.yolov8\test\images"
OUTPUT_DIR = "graded_visuals"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Answer key (Example)
answer_key = {
    f"q{i}": opt for i, opt in zip(range(1, 31), 
    ["a", "a", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e",
     "a", "b", "c", "d", "e"])
}

# Grid-aware mapping
def get_question_option(x, y, zone, zone_index):
    x1, y1, x2, y2 = zone
    zone_h = y2 - y1
    zone_w = x2 - x1

    rows = 5
    questions_per_row = 3
    options_per_question = 5

    row_height = zone_h / rows
    question_width = zone_w / questions_per_row
    option_width = question_width / options_per_question

    rel_x = x - x1
    rel_y = y - y1

    row = int(rel_y // row_height)
    row = max(0, min(row, 4))

    col = int(rel_x // question_width)
    col = max(0, min(col, 2))

    rel_x_in_question = rel_x - col * question_width
    opt_index = int(rel_x_in_question // option_width)
    opt_index = max(0, min(opt_index, 4))

    q_index = row * 3 + col + 1
    question_num = q_index if zone_index == 0 else q_index + 15
    option = ["a", "b", "c", "d", "e"][opt_index]

    return f"q{question_num}", option

# Contour zone detection
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
            boxes.append((x, y, x + w, y + h))

    boxes = sorted(boxes, key=lambda b: b[1])
    return boxes[:2] if len(boxes) >= 2 else []

# Grade + overlay
def grade_and_visualize(label_path, image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"⚠️ Could not load image: {image_path}")
        return

    h, w = image.shape[:2]
    with open(label_path, "r") as f:
        lines = f.readlines()

    zones = detect_answer_zones(image)
    if len(zones) != 2:
        print(f"⚠️ Could not detect zones in {image_path}")
        return

    zones = sorted(zones, key=lambda z: z[1])
    selections = {}
    centers = {}

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
                centers[(q, opt)] = (x, y)

    score = 0
    detailed = {}

    for q in answer_key:
        opts = selections.get(q, [])
        if len(opts) == 1:
            sel = opts[0]
            detailed[q] = "✔" if sel == answer_key[q] else "✘"
            if sel == answer_key[q]:
                score += 1
        elif len(opts) == 0:
            detailed[q] = "○"
        else:
            detailed[q] = "✘"

    # Visual overlay
    for q in answer_key:
        opts = selections.get(q, [])
        for opt in opts:
            center = centers.get((q, opt))
            if not center:
                continue
            if len(opts) > 1:
                color = (0, 255, 255)
                label = "?"
            else:
                correct = answer_key[q]
                if opt == correct:
                    color = (0, 255, 0)
                    label = "✔"
                else:
                    color = (0, 0, 255)
                    label = "✘"
            cv2.circle(image, center, 12, color, 2)
            cv2.putText(image, f"{q}_{opt} {label}", (center[0] + 5, center[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    out_path = os.path.join(OUTPUT_DIR, os.path.basename(image_path))
    cv2.imwrite(out_path, image)
    print(f"🧾 {os.path.basename(image_path)}: {score}/30")
    print("📋", detailed)

# Main loop
if __name__ == "__main__":
    for label_file in os.listdir(LABEL_DIR):
        if not label_file.endswith(".txt"):
            continue
        student_id = label_file.replace(".txt", "")
        label_path = os.path.join(LABEL_DIR, label_file)
        image_path = os.path.join(IMAGE_DIR, student_id + ".jpg")
        if not os.path.exists(image_path):
            print(f"❌ Missing image for {student_id}")
            continue
        grade_and_visualize(label_path, image_path)
