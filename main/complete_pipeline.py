import cv2
import os
import json
import re
import numpy as np
from ultralytics import YOLO

# === CONFIGURATION ===
MCQ_MODEL_PATH = 'models/yolov8_bubbles_best.pt'
REG_MODEL_PATH = 'models/reg_number_model_v1.pt'
SAMPLE_IMAGE = 'reg_Number/photo_2025-07-25_18-56-59.jpg'
OUTPUT_JSON = 'results_final.json'
OUTPUT_IMAGE = 'graded_images/final_output.jpg'
MARKER_DEBUG_IMAGE = 'graded_images/marker_debug.jpg'
CONF_THRESHOLD_REG = 0.2
EXPECTED_REG_LENGTH = 9
REGEX_PATTERN = r'^U\d{2}[A-Z]{2}\d{4}$'

CORRECT_ANSWERS = {
    1: "A", 2: "A", 3: "A", 4: "A", 5: "A",
    6: "A", 7: "A", 8: "C", 9: "A", 10: "A",
    11: "A", 12: "A", 13: "C", 14: "A", 15: "A",
    16: "A", 17: "A", 18: "C", 19: "A", 20: "A",
    21: "A", 22: "A", 23: "C", 24: "A", 25: "A",
    26: "A", 27: "A", 28: "C", 29: "B", 30: "A"
}

# === HELPERS ===
def correct_character(c):
    subs = {
        '0': 'O', 'O': 'O',
        '1': '1', 'I': '1', 'L': '1',
        'C ': 'C', ' ': ''
    }
    return subs.get(c, c)

# === MARKER ALIGNMENT ===
def find_markers_and_align(image):
    debug_img = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h_img, w_img = image.shape[:2]
    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 300 < area < 15000:  # Relaxed area filter
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            rect_area = w * h
            fill_ratio = area / rect_area if rect_area > 0 else 0

            # Filter: keep only filled, nearly square shapes
            if 0.5 < aspect_ratio < 1.5 and fill_ratio > 0.7:
                cx, cy = int(x + w / 2), int(y + h / 2)
                candidates.append((cx, cy, cnt))

    if len(candidates) < 4:
        raise ValueError(f"❌ Only {len(candidates)} marker candidates found, need at least 4")

    # Pick the four markers closest to the four corners
    corners = [(0, 0), (w_img, 0), (0, h_img), (w_img, h_img)]
    final_markers = []
    for (cx, cy, cnt) in candidates:
        distances = [np.hypot(cx - x, cy - y) for (x, y) in corners]
        min_idx = np.argmin(distances)
        final_markers.append((min_idx, cx, cy, cnt))

    # Keep the closest one for each corner
    closest = {}
    for idx, cx, cy, cnt in final_markers:
        if idx not in closest or np.hypot(cx - corners[idx][0], cy - corners[idx][1]) < \
                np.hypot(closest[idx][0] - corners[idx][0], closest[idx][1] - corners[idx][1]):
            closest[idx] = (cx, cy)

    if len(closest) != 4:
        raise ValueError(f"❌ Could not find all 4 unique corner markers, found: {len(closest)}")

    # Sort markers: top-left, top-right, bottom-left, bottom-right
    top_left = closest[0]
    top_right = closest[1]
    bottom_left = closest[2]
    bottom_right = closest[3]

    # Draw for debug
    for i, (cx, cy) in closest.items():
        cv2.circle(debug_img, (cx, cy), 10, (0, 0, 255), -1)
        cv2.putText(debug_img, f"{i}", (cx + 10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    os.makedirs(os.path.dirname(MARKER_DEBUG_IMAGE), exist_ok=True)
    cv2.imwrite(MARKER_DEBUG_IMAGE, debug_img)

    # Perspective transform
    src_pts = np.array([top_left, top_right, bottom_left, bottom_right], dtype='float32')
    dst_pts = np.array([[0, 0], [2480, 0], [0, 3508], [2480, 3508]], dtype='float32')
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    aligned = cv2.warpPerspective(image, M, (2480, 3508))

    return aligned



# === MCQ SECTION ===
def predict_mcq(image):
    model = YOLO(MCQ_MODEL_PATH)
    results = model.predict(image)[0]
    return results.boxes.xyxy, results.boxes.conf, results.boxes.cls

def divide_question_box(box, num_questions=15):
    x, y, w, h = box
    row_height = h / num_questions
    return [(x, y + i * row_height, w, row_height) for i in range(num_questions)]

def map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box):
    q1_rows = divide_question_box(q1_15_box, 15)
    q2_rows = divide_question_box(q16_30_box, 15)
    question_map = {i: ["", 0.0] for i in range(1, 31)}
    for box, conf, cls in zip(boxes, confs, classes):
        x1, y1, x2, y2 = box.tolist()
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        option = chr(65 + int(cls))

        for i, (x, y, w, h) in enumerate(q1_rows):
            if x <= cx <= x + w and y <= cy <= y + h:
                if conf > question_map[i + 1][1]:
                    question_map[i + 1] = [option, float(conf)]
                break
        for i, (x, y, w, h) in enumerate(q2_rows):
            if x <= cx <= x + w and y <= cy <= y + h:
                if conf > question_map[i + 16][1]:
                    question_map[i + 16] = [option, float(conf)]
                break
    return question_map

def grade_answers(question_map):
    score = 0
    results = []
    for q_num, (marked, conf) in question_map.items():
        correct = CORRECT_ANSWERS.get(q_num, "?")
        if marked == correct:
            status = "Correct"; score += 1
        elif marked:
            status = f"Wrong (marked {marked})"
        else:
            status = "Blank"
        results.append({"question": q_num, "marked": marked, "correct": correct,
                        "status": status, "confidence": conf})
    return {"score": score, "total": len(CORRECT_ANSWERS), "details": results}

# === REG NUMBER ===
def extract_reg_number(image):
    model = YOLO(REG_MODEL_PATH)
    results = model.predict(image, conf=CONF_THRESHOLD_REG)[0]
    boxes = results.boxes.xyxy.cpu().numpy()
    confs = results.boxes.conf.cpu().numpy()
    classes = results.boxes.cls.cpu().numpy()
    class_names = model.names

    detections = sorted(zip(boxes, classes, confs), key=lambda x: x[2], reverse=True)[:EXPECTED_REG_LENGTH]
    detections = sorted(detections, key=lambda x: x[0][0])
    raw_chars = [class_names[int(cls)].strip().upper() for _, cls, _ in detections]
    corrected_chars = [correct_character(c) for c in raw_chars]
    reg_number = ''.join(corrected_chars)

    print(f"\n🔎 Raw: {''.join(raw_chars)}")
    print(f"✅ Corrected: {reg_number}")
    if re.fullmatch(REGEX_PATTERN, reg_number):
        print("🎉 Valid Format")
    else:
        print("⚠️ Invalid Format")
    return reg_number

# === MAIN PIPELINE ===
def main():
    if not os.path.exists(SAMPLE_IMAGE):
        print(f"❌ File not found: {SAMPLE_IMAGE}")
        return

    original = cv2.imread(SAMPLE_IMAGE)
    try:
        aligned = find_markers_and_align(original)
    except ValueError as e:
        print(str(e)); return

    print("\n🔍 Extracting Reg Number...")
    reg_number = extract_reg_number(aligned)

    print("\n📝 Grading MCQ...")
    boxes, confs, classes = predict_mcq(aligned)
    q1_15_box = (270, 760, 950, 1340)
    q16_30_box = (1300, 760, 950, 1340)
    question_map = map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box)
    results = grade_answers(question_map)

    print(f"\n📊 Reg Number: {reg_number}")
    print(f"✅ Score: {results['score']} / {results['total']}")
    for item in results['details']:
        print(f"Q{item['question']:>2}: {item['status']} (conf: {item['confidence']:.2f})")

    with open(OUTPUT_JSON, 'w') as f:
        json.dump({"reg_number": reg_number, **results}, f, indent=2)
    print(f"📝 Results saved to {OUTPUT_JSON}")

if __name__ == '__main__':
    main()
