# Integrated version with marker alignment for MCQ grading

import cv2
import json
import os
import numpy as np
from ultralytics import YOLO

# === CONFIGURATION ===
MODEL_PATH = 'models/yolov8_bubbles_best.pt'
SAMPLE_IMAGE = 'reg_Number/photo_2025-07-25_18-56-47.jpg'
OUTPUT_JSON = 'results_aligned.json'
SAVE_IMAGE = 'graded_images/output_aligned.jpg'
MARKER_DEBUG_IMAGE = 'graded_images/marker_debug.jpg'

CORRECT_ANSWERS = {
    1: "A", 2: "A", 3: "A", 4: "A", 5: "A",
    6: "A", 7: "A", 8: "C", 9: "A", 10: "A",
    11: "A", 12: "A", 13: "C", 14: "A", 15: "A",
    16: "A", 17: "A", 18: "C", 19: "A", 20: "A",
    21: "A", 22: "A", 23: "C", 24: "A", 25: "A",
    26: "A", 27: "A", 28: "C", 29: "B", 30: "A"
}

# === STEP 0: Detect and Align using 4 Markers ===
def find_markers_and_align(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    markers = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 200 < area < 1500:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) >= 4:
                M = cv2.moments(cnt)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    markers.append((cx, cy))

    if len(markers) != 4:
        raise ValueError(f"❌ Error: Expected 4 markers, but found {len(markers)}")

    markers = sorted(markers, key=lambda p: p[1])
    top = sorted(markers[:2], key=lambda p: p[0])
    bottom = sorted(markers[2:], key=lambda p: p[0])

    src_pts = np.array([top[0], top[1], bottom[0], bottom[1]], dtype='float32')
    width = 2480  # A4 @ 300dpi width
    height = 3508  # A4 @ 300dpi height
    dst_pts = np.array([[0, 0], [width, 0], [0, height], [width, height]], dtype='float32')

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    aligned = cv2.warpPerspective(image, M, (width, height))

    # Save debug image
    for x, y in markers:
        cv2.circle(image, (x, y), 10, (0, 0, 255), -1)
    cv2.imwrite(MARKER_DEBUG_IMAGE, image)
    return aligned

# === Predict Bubbles ===
def predict_sheet(image):
    model = YOLO(MODEL_PATH)
    results = model.predict(image)
    return results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls

# === Divide Rectangle into Rows ===
def divide_question_box(box, num_questions=15):
    x, y, w, h = box
    row_height = h / num_questions
    return [(x, y + i * row_height, w, row_height) for i in range(num_questions)]

# === Map Detected Bubbles to Questions ===
def map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box):
    q1_rows = divide_question_box(q1_15_box, 15)
    q2_rows = divide_question_box(q16_30_box, 15)
    question_map = {i: ["", 0.0] for i in range(1, 31)}

    for box, conf, cls in zip(boxes, confs, classes):
        x1, y1, x2, y2 = box.tolist()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
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

# === Grade Answers ===
def grade_answers(question_map):
    score = 0
    results = []
    for q_num, (marked, conf) in question_map.items():
        correct = CORRECT_ANSWERS.get(q_num, "?")
        if marked == correct:
            status = "Correct"
            score += 1
        elif marked:
            status = f"Wrong (marked {marked})"
        else:
            status = "Blank"
        results.append({
            "question": q_num,
            "marked": marked,
            "correct": correct,
            "status": status,
            "confidence": conf
        })
    return {
        "score": score,
        "total": len(CORRECT_ANSWERS),
        "details": results
    }

# === Visualization ===
def save_visualization(image_path, boxes, classes):
    image = cv2.imread(image_path)
    class_names = ['A', 'B', 'C', 'D', 'E', 'INVALID']
    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, class_names[int(cls)], (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.imwrite(SAVE_IMAGE, image)
    print(f"✅ Visualization saved to {SAVE_IMAGE}")

# === Main Entry ===
def main():
    if not os.path.exists(SAMPLE_IMAGE):
        print(f"Error: Image file {SAMPLE_IMAGE} not found!")
        return

    original = cv2.imread(SAMPLE_IMAGE)
    try:
        aligned = find_markers_and_align(original)
    except ValueError as e:
        print(str(e))
        return

    boxes, confs, classes = predict_sheet(aligned)

    # Hardcoded zones (based on known template design)
    q1_15_box = (270, 760, 950, 1340)
    q16_30_box = (1300, 760, 950, 1340)

    question_map = map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box)
    results = grade_answers(question_map)

    print(f"\n✅ Score: {results['score']} / {results['total']}")
    for item in results['details']:
        print(f"Q{item['question']:>2}: {item['status']} (conf: {item['confidence']:.2f})")

    save_visualization(SAMPLE_IMAGE, boxes, classes)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
