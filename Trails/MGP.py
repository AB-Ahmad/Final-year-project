import cv2
import json
import numpy as np
from ultralytics import YOLO
import os

# ---------------------
# CONFIGURATION
# ---------------------
MODEL_PATH = "yolov8_bubbles_best.pt"
SAMPLE_IMAGE = "DATASETS/sheet30.jpg"
OUTPUT_JSON = "final_results.json"
DEBUG_IMAGE = "debug_mapping.jpg"

CLASS_MAP = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'INVALID'}

# Fallback template positions (ratios of image width/height)
TEMPLATE_LEFT = (0.1, 0.25, 0.45, 0.9)    # x1,y1,x2,y2
TEMPLATE_RIGHT = (0.55, 0.25, 0.9, 0.9)

def predict_bubbles(image_path):
    model = YOLO(MODEL_PATH)
    results = model.predict(image_path, conf=CONFIDENCE_THRESHOLD)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    return boxes, confs, classes

def detect_answer_areas(image):
    print("[INFO] Detecting answer rectangles...")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[DEBUG] Found {len(contours)} contours.")

    rects = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > image.shape[1] * 0.2 and h > image.shape[0] * 0.4:
            rects.append((x, y, w, h))

    print(f"[DEBUG] Filtered {len(rects)} possible answer areas.")

    if len(rects) >= 2:
        rects = sorted(rects, key=lambda r: r[0])
        return rects[:2]
    else:
        print("[WARN] Could not find both rectangles. Using fallback template.")
        h, w = image.shape[:2]
        left = (int(TEMPLATE_LEFT[0]*w), int(TEMPLATE_LEFT[1]*h),
                int((TEMPLATE_LEFT[2]-TEMPLATE_LEFT[0])*w), int((TEMPLATE_LEFT[3]-TEMPLATE_LEFT[1])*h))
        right = (int(TEMPLATE_RIGHT[0]*w), int(TEMPLATE_RIGHT[1]*h),
                 int((TEMPLATE_RIGHT[2]-TEMPLATE_RIGHT[0])*w), int((TEMPLATE_RIGHT[3]-TEMPLATE_RIGHT[1])*h))
        return [left, right]

def map_detections_to_questions(boxes, confs, classes, rects):
    questions = {i: {"marked": "INVALID", "confidence": 0.0} for i in range(1, 31)}

    for idx, rect in enumerate(rects):
        x, y, w, h = rect
        row_height = h / 15.0

        for i in range(15):
            q_num = i + 1 if idx == 0 else i + 16
            row_y1 = y + i * row_height
            row_y2 = y + (i + 1) * row_height

            for box, conf, cls in zip(boxes, confs, classes):
                cx = (box[0] + box[2]) / 2
                cy = (box[1] + box[3]) / 2

                if x <= cx <= x + w and row_y1 <= cy <= row_y2:
                    if conf > questions[q_num]["confidence"]:
                        questions[q_num]["marked"] = CLASS_MAP[int(cls)]
                        questions[q_num]["confidence"] = float(conf)

    return questions

def create_debug_image(image, rects, boxes, classes, question_map):
    debug = image.copy()

    for idx, rect in enumerate(rects):
        x, y, w, h = rect
        cv2.rectangle(debug, (x, y), (x + w, y + h), (255, 0, 255), 2)
        for i in range(15):
            y_line = int(y + i * (h / 15))
            cv2.line(debug, (x, y_line), (x + w, y_line), (200, 200, 200), 1)

    colors = {'A': (0, 255, 0), 'B': (255, 0, 0), 'C': (0, 0, 255),
              'D': (0, 255, 255), 'E': (255, 0, 255), 'INVALID': (0, 0, 0)}

    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = map(int, box)
        option = CLASS_MAP[int(cls)]
        cv2.rectangle(debug, (x1, y1), (x2, y2), colors[option], 2)
        cv2.putText(debug, option, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[option], 1)

    cv2.imwrite(DEBUG_IMAGE, debug)
    print(f"[INFO] Debug image saved to {DEBUG_IMAGE}")

def main():
    if not os.path.exists(SAMPLE_IMAGE):
        print(f"[ERROR] Image {SAMPLE_IMAGE} not found!")
        return

    image = cv2.imread(SAMPLE_IMAGE)

    rects = detect_answer_areas(image)

    boxes, confs, classes = predict_bubbles(SAMPLE_IMAGE)
    print(f"[INFO] YOLO detected {len(boxes)} bubbles.")

    question_map = map_detections_to_questions(boxes, confs, classes, rects)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(question_map, f, indent=2)
    print(f"[INFO] Results saved to {OUTPUT_JSON}")

    print("\n=== Detected Answers ===")
    for q, data in question_map.items():
        print(f"Q{q}: {data['marked']} (conf: {data['confidence']:.2f})")

    create_debug_image(image, rects, boxes, classes, question_map)

if __name__ == "__main__":
    main()
