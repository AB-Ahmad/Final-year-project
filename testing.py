import cv2
import json
from ultralytics import YOLO
import os

# === CONFIGURATION ===
MODEL_PATH = 'models/yolov8_bubbles_best.pt'
SAMPLE_IMAGE = 'Test_images/alaa.jpg'
OUTPUT_JSON = 'result/results.json'
SAVE_IMAGE = 'graded_images/output_debug.jpg'
DEBUG_DIVISION_IMAGE = 'graded_images/debug_divisions.jpg'
MAPPED_IMAGE = 'graded_images/mapped_output.jpg'

# Correct answers for 30 questions
CORRECT_ANSWERS = {
    1: "B", 2: "C", 3: "C", 4: "B", 5: "D",
    6: "D", 7: "B", 8: "C", 9: "B", 10: "C",
    11: "B", 12: "B", 13: "C", 14: "B", 15: "B",
    16: "A", 17: "B", 18: "E", 19: "C", 20: "E",
    21: "B", 22: "C", 23: "A", 24: "D", 25: "B",
    26: "B", 27: "E", 28: "C", 29: "A", 30: "A"
}

CLASS_NAMES = ['A', 'B', 'C', 'D', 'E', 'INVALID']

# === PREDICTION ===
def predict_sheet(image_path):
    model = YOLO(MODEL_PATH)
    results = model.predict(image_path)
    return results[0].boxes.xyxy, results[0].boxes.conf, results[0].boxes.cls

# === RECTANGLE DIVISION ===
def divide_question_box(box, num_questions=15):
    x, y, w, h = box
    row_height = h / num_questions
    question_rows = []
    for i in range(num_questions):
        q_y = y + i * row_height
        question_rows.append((x, q_y, w, row_height))
    return question_rows

# === BUBBLE TO QUESTION MAPPING ===
def map_bubbles_to_questions(boxes, confs, classes, q1_15_box, q16_30_box):
    q1_rows = divide_question_box(q1_15_box, 15)
    q2_rows = divide_question_box(q16_30_box, 15)
    question_map = {i: ["", 0.0] for i in range(1, 31)}
    print(question_map)

    print("\n🔍 Mapping Detected Bubbles to Questions:")
    for box, conf, cls in zip(boxes, confs, classes):
        if conf < 0.5:  # increased threshold
            continue
        x1, y1, x2, y2 = box.tolist()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        option = CLASS_NAMES[int(cls)]

        found = False
        for i, (x, y, w, h) in enumerate(q1_rows):
            if x <= cx <= x + w and y <= cy <= y + h:
                if conf > question_map[i + 1][1]:
                    question_map[i + 1] = [option, float(conf)]
                    print(f"[Q1–15] → Q{i+1} = {option} (conf: {conf:.2f})")
                found = True
                break
        if not found:
            for i, (x, y, w, h) in enumerate(q2_rows):
                if x <= cx <= x + w and y <= cy <= y + h:
                    if conf > question_map[i + 16][1]:
                        question_map[i + 16] = [option, float(conf)]
                        print(f"[Q16–30] → Q{i+16} = {option} (conf: {conf:.2f})")
                    break
    print(question_map)
    return question_map


# === GRADING ===
def grade_answers(question_map):
    score = 0
    results = []
    for q_num, (marked, conf) in question_map.items():
        correct = CORRECT_ANSWERS.get(q_num, "?")
        if marked == correct:
            status = "Correct"
            score += 1
        elif marked == "INVALID":
            status = "Invalid Mark"
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

# === CONTOUR DETECTION ===
def extract_boxes_from_contours(image, debug_path=None):
    os.makedirs("debug_outputs", exist_ok=True)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("debug_outputs/step1_gray.jpg", gray)

    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 10
    )
    cv2.imwrite("debug_outputs/step2_thresh.jpg", thresh)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    debug_img = image.copy()
    rects = []

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            rects.append((x, y, w, h, area))
            cv2.rectangle(debug_img, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.imwrite("debug_outputs/step3_all_contours.jpg", debug_img)

    rects = [r for r in rects if r[4] > 10000]
    rects = sorted(rects, key=lambda r: r[4], reverse=True)

    tall_boxes = [r for r in rects if r[3] > r[2] * 1.2]
    tall_boxes = sorted(tall_boxes, key=lambda r: r[0])  # left to right

    if len(tall_boxes) >= 2:
        debug_img2 = image.copy()
        cv2.rectangle(debug_img2, (tall_boxes[0][0], tall_boxes[0][1]),
                      (tall_boxes[0][0]+tall_boxes[0][2], tall_boxes[0][1]+tall_boxes[0][3]), (255,0,0), 3)
        cv2.rectangle(debug_img2, (tall_boxes[1][0], tall_boxes[1][1]),
                      (tall_boxes[1][0]+tall_boxes[1][2], tall_boxes[1][1]+tall_boxes[1][3]), (0,0,255), 3)
        cv2.imwrite("debug_outputs/step4_final_boxes.jpg", debug_img2)
        return tall_boxes[0][:4], tall_boxes[1][:4]

    return None, None

# === DRAW QUESTION ZONES ===
def draw_divisions(image, box, start_q=1):
    rows = divide_question_box(box, 15)
    for i, (x, y, w, h) in enumerate(rows):
        cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), (255, 0, 0), 1)
        cv2.putText(image, f"Q{start_q + i}", (int(x)+5, int(y)+15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

# === DRAW DETECTIONS ===
def save_visualization(image_path, boxes, classes):
    image = cv2.imread(image_path)
    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, CLASS_NAMES[int(cls)], (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.imwrite(SAVE_IMAGE, image)
    print(f"✅ Saved detection image: {SAVE_IMAGE}")

# === VISUALIZE QUESTION MAPPING ===
def visualize_mapping(image_path, question_map, q1_15_box, q16_30_box, results, output_path):
    image = cv2.imread(image_path)
    rows_left = divide_question_box(q1_15_box, 15)
    rows_right = divide_question_box(q16_30_box, 15)

    for i, (x, y, w, h) in enumerate(rows_left + rows_right):
        q_num = i + 1
        marked, conf = question_map[q_num]
        detail = results["details"][q_num-1]
        status, correct = detail["status"], detail["correct"]

        # Draw row rectangle
        cv2.rectangle(image, (int(x), int(y)), (int(x+w), int(y+h)), (200, 200, 200), 1)
        cv2.putText(image, f"Q{q_num}", (int(x)-50, int(y)+20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # Decide color + symbol
        if status == "Correct":
            color, symbol = (0, 200, 0), "✔"
            label_text = f"{marked}"
        elif status.startswith("Wrong"):
            color, symbol = (0, 0, 255), "✘"
            label_text = f"{marked} / {correct}"
        elif status == "Invalid Mark":
            color, symbol = (0, 200, 255), "⚠"
            label_text = "INVALID"
        else:  # Blank
            color, symbol = (150, 150, 150), "○"
            label_text = f"- / {correct}"

        cv2.putText(image, f"{symbol} {label_text}",
                    (int(x)+10, int(y)+int(h/2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, image)
    print(f"🎯 Mapped visualization saved at {output_path}")

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

    filled = [q for q, (opt, c) in question_map.items() if opt]
    print(f"\n📊 Questions answered: {len(filled)} / 30")
    print(f"✅ Score: {results['score']} / {results['total']}")

    for item in results["details"]:
        print(f"Q{item['question']:>2}: {item['status']} (conf: {item['confidence']:.2f})")

    # Save outputs
    save_visualization(SAMPLE_IMAGE, boxes, classes)

    debug_image = cv2.imread(SAMPLE_IMAGE)
    draw_divisions(debug_image, q1_15_box, 1)
    draw_divisions(debug_image, q16_30_box, 16)
    cv2.imwrite(DEBUG_DIVISION_IMAGE, debug_image)
    print(f"🧭 Saved debug zones image: {DEBUG_DIVISION_IMAGE}")

    visualize_mapping(SAMPLE_IMAGE, question_map, q1_15_box, q16_30_box, results, MAPPED_IMAGE)

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
