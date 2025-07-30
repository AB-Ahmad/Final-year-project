import cv2
import json
from ultralytics import YOLO
import os

# === CONFIGURATION ===
MODEL_PATH = 'models/yolov8_bubbles_best.pt'
SAMPLE_IMAGE = 'Test_images/photo_2025-07-25_18-57-25.jpg'
OUTPUT_JSON = 'results6.json'
SAVE_IMAGE = 'output6.jpg'

# Correct answers for 30 questions
CORRECT_ANSWERS = {
    1: "A", 2: "A", 3: "A", 4: "A", 5: "A",
    6: "A", 7: "A", 8: "C", 9: "A", 10: "A",
    11: "A", 12: "A", 13: "C", 14: "A", 15: "A",
    16: "A", 17: "A", 18: "C", 19: "A", 20: "A",
    21: "A", 22: "A", 23: "C", 24: "A", 25: "A",
    26: "A", 27: "A", 28: "C", 29: "B", 30: "A"
}

# === STEP 1: PREDICT BUBBLES ===
def predict_sheet(image_path):
    model = YOLO(MODEL_PATH)
    results = model.predict(image_path)
    return results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls

# === STEP 2: DIVIDE A RECTANGLE INTO 15 VERTICAL QUESTION ROWS ===
def divide_question_box(box, num_questions=15):
    x, y, w, h = box
    row_height = h / num_questions
    question_rows = []
    for i in range(num_questions):
        q_y = y + i * row_height
        question_rows.append((x, q_y, w, row_height))
    return question_rows

# === STEP 3: MAP DETECTED BUBBLES TO QUESTIONS BASED ON ROW POSITION ===
def map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box):
    q1_rows = divide_question_box(q1_15_box, 15)
    q2_rows = divide_question_box(q16_30_box, 15)
    question_map = {i: ["", 0.0] for i in range(1, 31)}

    for box, conf, cls in zip(boxes, confs, classes):
        x1, y1, x2, y2 = box.tolist()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        option = chr(65 + int(cls))  # A–E

        found = False
        for i, (x, y, w, h) in enumerate(q1_rows):
            if x <= cx <= x + w and y <= cy <= y + h:
                if conf > question_map[i + 1][1]:
                    question_map[i + 1] = [option, float(conf)]
                found = True
                break
        if not found:
            for i, (x, y, w, h) in enumerate(q2_rows):
                if x <= cx <= x + w and y <= cy <= y + h:
                    if conf > question_map[i + 16][1]:
                        question_map[i + 16] = [option, float(conf)]
                    break
    return question_map

# === STEP 4: GRADE ===
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

# === STEP 5: DETECT RECTANGLES USING CONTOURS ===
def extract_boxes_from_contours(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 10)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            rects.append((x, y, w, h, area))

    rects = [r for r in rects if r[4] > 10000]
    rects = sorted(rects, key=lambda r: r[4], reverse=True)

    q1_15_box = None
    q16_30_box = None
    tall_boxes = [r for r in rects if r[3] > r[2] * 1.2]
    tall_boxes = sorted(tall_boxes, key=lambda r: r[0])  # left to right

    if len(tall_boxes) >= 2:
        q1_15_box = tall_boxes[0][:4]
        q16_30_box = tall_boxes[1][:4]

    return q1_15_box, q16_30_box

# === STEP 6: VISUALIZE BOUNDING BOXES ===
def save_visualization(image_path, boxes, classes):
    image = cv2.imread(image_path)
    class_names = ['A', 'B', 'C', 'D', 'E', 'INVALID']
    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, class_names[int(cls)], (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.imwrite(SAVE_IMAGE, image)
    print(f"Visualization saved to {SAVE_IMAGE}")

# === MAIN ===
def main():
    if not os.path.exists(SAMPLE_IMAGE):
        print(f"Error: Image file {SAMPLE_IMAGE} not found!")
        return

    image = cv2.imread(SAMPLE_IMAGE)
    q1_15_box, q16_30_box = extract_boxes_from_contours(image)

    if not q1_15_box or not q16_30_box:
        print("❌ Failed to detect one or both answer rectangles.")
        return

    boxes, confs, classes = predict_sheet(SAMPLE_IMAGE)
    question_map = map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box)

    results = grade_answers(question_map)

    print(f"\n✅ Score: {results['score']} / {results['total']}")
    for item in results["details"]:
        print(f"Q{item['question']:>2}: {item['status']} (conf: {item['confidence']:.2f})")

    save_visualization(SAMPLE_IMAGE, boxes, classes)

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
